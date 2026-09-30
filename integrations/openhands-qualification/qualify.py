"""No-model qualification of the installed OpenHands SDK. Never connects a provider."""
import asyncio
import importlib.metadata
import json

from acp.schema import RequestPermissionResponse
from openhands.sdk.agent.acp_agent import _OpenHandsACPBridge


class DenyPermissionProbe(_OpenHandsACPBridge):
    """Qualification-only override of a PRIVATE class; not wired to ACPAgent.

    Default-deny is intentional: a tool title such as Read/Edit/Write is not an
    authorization boundary. A future policy needs canonical tool identity,
    normalized paths, mission scope and a durable decision before allowing it.
    """

    async def request_permission(self, session_id, tool_call, options, **kwargs):
        return RequestPermissionResponse.model_validate(
            {"outcome": {"outcome": "cancelled"}}
        )


async def main():
    version = importlib.metadata.version("openhands-sdk")
    assert version == "1.50.0", f"Unexpected SDK {version}; re-review private contract"
    # Pydantic inputs are validated as real protocol models, not mock outputs.
    from acp.schema import PermissionOption, ToolCallUpdate

    options = [
        PermissionOption.model_validate(
            {"optionId": "allow-once", "name": "Allow once", "kind": "allow_once"}
        ),
        PermissionOption.model_validate(
            {"optionId": "reject-once", "name": "Reject", "kind": "reject_once"}
        ),
    ]
    call = ToolCallUpdate.model_validate(
        {"toolCallId": "synthetic-call", "title": "Bash", "kind": "execute"}
    )
    upstream = await _OpenHandsACPBridge().request_permission("synthetic", call, options)
    assert upstream.outcome.outcome == "selected"
    assert upstream.outcome.option_id == "allow-once"
    policy = DenyPermissionProbe()
    for title in ("Bash", "Read", "Edit", "Write", "unknown"):
        candidate = ToolCallUpdate.model_validate(
            {"toolCallId": "synthetic-call", "title": title, "kind": "other"}
        )
        denied = await policy.request_permission("synthetic", candidate, options)
        assert denied.outcome.outcome == "cancelled", title
    denied = await policy.request_permission("synthetic", call, [])
    assert denied.outcome.outcome == "cancelled"
    print(json.dumps({
        "sdkVersion": version,
        "upstreamAutoAllowObserved": True,
        "qualificationOnlyDenyOverridePassed": True,
        "titlesNotTreatedAsAuthority": True,
        "productionPolicyIntegrated": False,
        "modelCalls": 0,
        "providerCredentialsUsed": False,
    }))


if __name__ == "__main__":
    asyncio.run(main())
