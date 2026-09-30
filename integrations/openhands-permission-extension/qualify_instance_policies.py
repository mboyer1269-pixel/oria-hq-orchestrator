"""Two actual SDK conversations with different policies, concurrently, no LLM."""
from concurrent.futures import ThreadPoolExecutor
import importlib.metadata
import json
from pathlib import Path
import signal
import sys
import tempfile

from openhands.sdk import Conversation
from openhands.sdk.agent.acp_agent import ACPAgent, _OpenHandsACPBridge
from permission_agent import PermissionAgent


def deadline(signum, frame):
    raise TimeoutError("Instance-policy qualification exceeded 40 seconds")


def run_case(policy, callback=None, expected_outcome=None):
    with tempfile.TemporaryDirectory(prefix="hq-instance-policy-") as work:
        events = []
        agent = PermissionAgent(
            hq_permission_policy=policy,
            acp_command=[sys.executable, str(Path(__file__).with_name("permission_peer.py"))],
            acp_startup_timeout=8, acp_prompt_timeout=8,
        )
        assert agent.model_dump()["hq_permission_policy"] == policy
        if callback is not None:
            agent.set_permission_callback(callback, timeout_seconds=0.1)
        conversation = Conversation(agent=agent, workspace=work, callbacks=[events.append])
        try:
            conversation.send_message("Synthetic permission request only.")
            conversation.run()
            expected = expected_outcome or ("DENIED" if policy == "deny" else "ALLOWED")
            assert f"HQ_PERMISSION_{expected}" in json.dumps([e.model_dump(mode="json") for e in events])
            return {"policy": policy, "wireOutcome": expected}
        finally:
            conversation.close()


def main():
    assert importlib.metadata.version("openhands-sdk") == "1.50.0"
    assert hasattr(ACPAgent, "create_acp_bridge"), "Apply pinned factory patch in build stage first"
    signal.signal(signal.SIGALRM, deadline)
    signal.alarm(40)
    original_method = _OpenHandsACPBridge.request_permission
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(run_case, ("deny", "upstream-auto-allow")))
        assert _OpenHandsACPBridge.request_permission is original_method
        assert run_case("deny")["wireOutcome"] == "DENIED"
        async def approve_offered(**request):
            assert request["session_id"]
            assert request["tool_call"].tool_call_id
            option = next(item for item in request["options"] if item.kind == "allow_once")
            return {"outcome": {"outcome": "selected", "optionId": option.option_id}}

        async def unavailable_authority(**request):
            raise RuntimeError("Synthetic authority unavailable")

        assert run_case("deny", approve_offered, "ALLOWED")["wireOutcome"] == "ALLOWED"
        assert run_case("deny", unavailable_authority)["wireOutcome"] == "DENIED"
        print(json.dumps({"sdkVersion": "1.50.0", "concurrentInstancePolicies": results,
                          "denyAfterAllowPassed": True, "globalSymbolMutation": False,
                          "wireCallbackAllowedOfferedOption": True, "wireCallbackFailureDenied": True,
                          "modelCalls": 0, "humanApprovalIntegrated": False,
                          "productionQualified": False}))
    finally:
        signal.alarm(0)


if __name__ == "__main__":
    main()
