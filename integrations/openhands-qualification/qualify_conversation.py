"""Real SDK conversation against a synthetic ACP peer; no inference."""
import importlib.metadata
import json
import sys
import tempfile
from pathlib import Path

from openhands.sdk import Conversation
from openhands.sdk.agent import ACPAgent


def main():
    assert importlib.metadata.version("openhands-sdk") == "1.50.0"
    events = []
    agent = ACPAgent(
        acp_command=[sys.executable, str(Path(__file__).with_name("fake_acp.py"))],
        acp_startup_timeout=10,
        acp_prompt_timeout=10,
    )
    with tempfile.TemporaryDirectory(prefix="hq-acp-qualification-") as work:
        conversation = Conversation(agent=agent, workspace=work, callbacks=[events.append])
        try:
            conversation.send_message("Return the synthetic protocol marker.")
            conversation.run()
            serialized = [event.model_dump(mode="json") for event in events]
            assert "HQ_SYNTHETIC_PROTOCOL_OK" in json.dumps(serialized)
            print(json.dumps({"sdkVersion": "1.50.0", "realSdkConversationPassed": True,
                              "syntheticPeer": True, "eventsObserved": len(events),
                              "modelCalls": 0, "providerCredentialsUsed": False,
                              "cancellationQualified": False,
                              "productionPermissionPolicyIntegrated": False}))
        finally:
            agent.close()


if __name__ == "__main__":
    main()
