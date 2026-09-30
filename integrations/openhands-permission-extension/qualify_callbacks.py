"""Callback boundary tests with real ACP schema and patched SDK instance factory."""
import asyncio
import importlib.metadata
import json
from acp.schema import PermissionOption, ToolCallUpdate
from permission_agent import PermissionAgent


async def main():
    assert importlib.metadata.version("openhands-sdk") == "1.50.0"
    options = [PermissionOption.model_validate({"optionId": "allow", "name": "Allow", "kind": "allow_once"})]
    tool = ToolCallUpdate.model_validate({"toolCallId": "call-1", "title": "Synthetic", "kind": "other"})
    agent = PermissionAgent(acp_command=["never-executed"])
    bridge = agent.create_acp_bridge()

    async def ask(target=bridge):
        return await target.request_permission("session-1", tool, options)

    async def allowed(**request):
        assert request["session_id"] == "session-1"
        assert request["tool_call"].tool_call_id == "call-1"
        assert request["options"][0].option_id == "allow"
        return {"outcome": {"outcome": "selected", "optionId": "allow"}}

    async def unknown(**request):
        return {"outcome": {"outcome": "selected", "optionId": "not-offered"}}

    async def failure(**request):
        raise ValueError("synthetic callback failure")

    async def slow(**request):
        await asyncio.sleep(10)

    assert (await ask()).outcome.outcome == "cancelled"
    agent.set_permission_callback(allowed)
    assert (await ask()).outcome.option_id == "allow"
    persistent_options = [PermissionOption.model_validate({"optionId":"allow", "name":"Always allow", "kind":"allow_always"})]
    persistent = await bridge.request_permission("session-1", tool, persistent_options)
    assert persistent.outcome.outcome == "cancelled"
    other = PermissionAgent(acp_command=["never-executed"])
    assert (await ask(other.create_acp_bridge())).outcome.outcome == "cancelled"
    # Runtime callback must disappear across serialization reconstruction.
    restored = PermissionAgent.model_validate(agent.model_dump())
    assert restored._permission_callback is None
    assert (await ask(restored.create_acp_bridge())).outcome.outcome == "cancelled"
    for callback in (unknown, failure, slow):
        agent.set_permission_callback(callback, timeout_seconds=0.02)
        response = await asyncio.wait_for(ask(), timeout=1)
        assert response.outcome.outcome == "cancelled"
    agent.set_permission_callback(slow, timeout_seconds=2)
    task = asyncio.create_task(ask())
    await asyncio.sleep(0.01)
    task.cancel()
    try:
        await task
        raise AssertionError("Caller cancellation was swallowed")
    except asyncio.CancelledError:
        pass
    agent.set_permission_callback(None)
    assert (await ask()).outcome.outcome == "cancelled"
    print(json.dumps({"callbackAllowedOfferedOption": True, "unknownOptionDenied": True,
                      "persistentPermissionDenied": True,
                      "exceptionDenied": True, "timeoutDenied": True,
                      "callerCancellationPropagated": True, "instanceIsolation": True,
                      "serializedRestoreDefaultsDeny": True, "modelCalls": 0,
                      "durableHqApprovalIntegrated": False, "providerTested": False}))


if __name__ == "__main__":
    asyncio.run(asyncio.wait_for(main(), timeout=10))
