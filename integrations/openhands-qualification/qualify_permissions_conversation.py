"""Real ACP permission exchange and persisted SDK events; no real tools/model.

The deny case replaces a private bridge symbol ONLY inside this isolated,
single-conversation subprocess and restores it in finally. Not a production
extension, not thread-safe, and never imported by application code.
"""
import importlib.metadata
import json
import signal
import subprocess
import sys
import tempfile
from pathlib import Path

from openhands.sdk import Conversation
from openhands.sdk.agent import ACPAgent
import openhands.sdk.agent.acp_agent as acp_module
from qualify import DenyPermissionProbe


def alarm_handler(signum, frame):
    raise TimeoutError("Qualification exceeded 35-second hard deadline")


def run_case(mode):
    assert mode in ("upstream", "deny")
    assert importlib.metadata.version("openhands-sdk") == "1.50.0"
    signal.signal(signal.SIGALRM, alarm_handler)
    signal.alarm(35)
    original_bridge = acp_module._OpenHandsACPBridge
    if mode == "deny":
        acp_module._OpenHandsACPBridge = DenyPermissionProbe
    marker = "HQ_SYNTHETIC_PERMISSION_" + ("DENIED" if mode == "deny" else "ALLOWED")
    agent = None
    restored = None
    try:
        with tempfile.TemporaryDirectory(prefix="hq-acp-permissions-") as directory:
            root = Path(directory)
            workspace = root / "workspace"
            workspace.mkdir()
            persistence = root / "conversations"
            events = []
            agent = ACPAgent(
                acp_command=[sys.executable, str(Path(__file__).with_name("fake_acp.py")), "--permission-probe"],
                acp_startup_timeout=8,
                acp_prompt_timeout=8,
            )
            conversation = Conversation(agent=agent, workspace=str(workspace),
                                        persistence_dir=str(persistence), callbacks=[events.append])
            conversation.send_message("Run the synthetic permission protocol probe.")
            conversation.run()
            payload = [event.model_dump(mode="json") for event in events]
            assert marker in json.dumps(payload), "Peer did not report expected permission outcome"
            conversation_id = conversation.id
            agent.close()
            agent = None
            # Public persistence restoration; do not call run() and do not claim
            # provider session recovery. Only stored SDK events are checked.
            restored = Conversation(agent=None, workspace=str(workspace),
                                    persistence_dir=str(persistence), conversation_id=conversation_id)
            persisted = [event.model_dump(mode="json") for event in restored.state.events]
            assert marker in json.dumps(persisted), "Expected peer evidence missing after reload"
            assert any(persistence.rglob("base_state.json")), "No durable SDK base state"
            print(json.dumps({"mode": mode, "actualAcpPermissionExchange": True,
                              "expectedOutcome": "denied" if mode == "deny" else "allowed",
                              "sdkEventsRestored": True, "persistedEventCount": len(persisted),
                              "remoteSessionResumed": False, "productionIntegrated": False,
                              "privatePatchQualificationOnly": mode == "deny",
                              "modelCalls": 0, "providerCredentialsUsed": False}))
    finally:
        if agent is not None:
            agent.close()
        if restored is not None:
            restored.agent.close()
        acp_module._OpenHandsACPBridge = original_bridge
        signal.alarm(0)


if __name__ == "__main__":
    if len(sys.argv) == 2:
        run_case(sys.argv[1])
    else:
        # Separate OS processes prevent private symbol mutation from affecting
        # another case. Parent watchdog also bounds a blocked cleanup handler.
        for mode in ("upstream", "deny"):
            subprocess.run([sys.executable, __file__, mode], check=True, timeout=45)
