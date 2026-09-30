"""Experimental instance-scoped policy, requiring the pinned factory patch."""
from typing import Literal
import asyncio
import inspect
from pydantic import PrivateAttr

from acp.schema import RequestPermissionResponse
from openhands.sdk.agent.acp_agent import ACPAgent, _OpenHandsACPBridge


class DenyBridge(_OpenHandsACPBridge):
    async def request_permission(self, session_id, tool_call, options, **kwargs):
        return RequestPermissionResponse.model_validate({"outcome": {"outcome": "cancelled"}})


class CallbackBridge(DenyBridge):
    def __init__(self, owner):
        super().__init__()
        self.owner = owner

    async def request_permission(self, session_id, tool_call, options, **kwargs):
        callback = self.owner._permission_callback
        if callback is None:
            return await super().request_permission(session_id, tool_call, options)
        # Isolate request data from mutation by the callback; preserve IDs for
        # correlation. Never infer permission from tool titles or option order.
        request = {"session_id": session_id,
                   "tool_call": tool_call.model_copy(deep=True),
                   "options": tuple(option.model_copy(deep=True) for option in options)}
        # This boundary authorizes one tool invocation only. Persisting a broad
        # provider permission would outlive the exact HQ decision being checked.
        selected_ids = {option.option_id for option in options
                        if option.kind in ("allow_once", "reject_once")}
        task = None
        try:
            task = asyncio.create_task(callback(**request))
            done, _ = await asyncio.wait({task}, timeout=self.owner._permission_timeout)
            if not done:
                task.cancel()
                return await super().request_permission(session_id, tool_call, options)
            response = RequestPermissionResponse.model_validate(task.result())
            if response.outcome.outcome == "selected" and response.outcome.option_id not in selected_ids:
                return await super().request_permission(session_id, tool_call, options)
            # Clearing/replacing policy while waiting invalidates the response.
            if self.owner._permission_callback is not callback:
                return await super().request_permission(session_id, tool_call, options)
            return response
        except asyncio.CancelledError:
            raise
        except Exception:
            return await super().request_permission(session_id, tool_call, options)
        finally:
            if task is not None and not task.done():
                task.cancel()
                # Retrieve late exceptions without waiting beyond the deadline.
                task.add_done_callback(lambda completed: None if completed.cancelled() else completed.exception())


class PermissionAgent(ACPAgent):
    # Serializable intent; default stays deny when reconstructed. This is not a
    # durable human approval service and cannot prevent a provider bypass mode.
    hq_permission_policy: Literal["deny", "upstream-auto-allow"] = "deny"
    acp_session_mode: str | None = "default"
    _permission_callback: object = PrivateAttr(default=None)
    _permission_timeout: float = PrivateAttr(default=1.0)

    def set_permission_callback(self, callback, *, timeout_seconds=1.0):
        """Attach a trusted async runtime callback; never serialized or persisted."""
        if callback is not None and not inspect.iscoroutinefunction(callback):
            raise TypeError("Permission callback must be an async function")
        if not 0.01 <= timeout_seconds <= 210:
            raise ValueError("Permission timeout must be between 0.01 and 210 seconds")
        if self.hq_permission_policy != "deny":
            raise ValueError("Callbacks require the default deny policy")
        self._permission_callback = callback
        self._permission_timeout = float(timeout_seconds)

    def create_acp_bridge(self):
        if self.hq_permission_policy == "deny":
            return CallbackBridge(self)
        return super().create_acp_bridge()
