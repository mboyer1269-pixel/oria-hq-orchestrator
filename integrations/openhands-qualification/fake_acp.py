"""Synthetic ACP stdio peer. No model, shell command or filesystem operation."""
import json
import sys
from pathlib import Path

permission_probe = "--permission-probe" in sys.argv
cancel_probe = "--cancel-probe" in sys.argv
pending_prompt_id = None


def send(message):
    print(json.dumps(message), flush=True)


for line in sys.stdin:
    message = json.loads(line)
    method = message.get("method")
    request_id = message.get("id")
    if method == "initialize":
        result = {
            "protocolVersion": 1,
            "agentCapabilities": {},
            "authMethods": [],
            "agentInfo": {"name": "hq-synthetic-peer", "version": "1.0.0"},
        }
    elif method == "session/new":
        result = {"sessionId": "hq-synthetic-session"}
    elif method == "session/prompt":
        marker = "HQ_SYNTHETIC_PROTOCOL_OK"
        if cancel_probe:
            pending_prompt_id = request_id
            Path(sys.argv[sys.argv.index("--cancel-probe") + 1] + ".ready").write_text(
                "prompt-active", encoding="utf-8")
            send({"jsonrpc": "2.0", "method": "session/update", "params": {
                "sessionId": "hq-synthetic-session",
                "update": {"sessionUpdate": "agent_message_chunk", "content": {
                    "type": "text", "text": "HQ_SYNTHETIC_WAITING_FOR_CANCEL"}},
            }})
            continue
        if permission_probe:
            send({"jsonrpc": "2.0", "id": "permission-probe", "method": "session/request_permission", "params": {
                "sessionId": "hq-synthetic-session",
                "toolCall": {"toolCallId": "synthetic-execute", "title": "Synthetic execution", "kind": "execute"},
                "options": [
                    {"optionId": "allow-once", "name": "Allow once", "kind": "allow_once"},
                    {"optionId": "reject-once", "name": "Reject", "kind": "reject_once"},
                ],
            }})
            # The driver imposes a hard deadline in addition to SDK timeouts.
            response = json.loads(sys.stdin.readline())
            assert response.get("id") == "permission-probe", response
            outcome = response["result"]["outcome"]
            if outcome == {"outcome": "selected", "optionId": "allow-once"}:
                marker = "HQ_SYNTHETIC_PERMISSION_ALLOWED"
            elif outcome == {"outcome": "cancelled"}:
                marker = "HQ_SYNTHETIC_PERMISSION_DENIED"
            else:
                raise AssertionError(f"Unexpected permission response: {outcome}")
        send({"jsonrpc": "2.0", "method": "session/update", "params": {
            "sessionId": "hq-synthetic-session",
            "update": {"sessionUpdate": "agent_message_chunk", "content": {
                "type": "text", "text": marker}},
        }})
        result = {"stopReason": "end_turn"}
    elif method == "session/cancel":
        if cancel_probe and pending_prompt_id is not None:
            # Receipt is synthetic evidence of receiving the wire notification,
            # independent of SDK state labels or callbacks during interruption.
            receipt_path = Path(sys.argv[sys.argv.index("--cancel-probe") + 1])
            receipt_path.write_text(json.dumps({"method": method,
                "sessionId": message["params"]["sessionId"],
                "promptResponse": "cancelled"}), encoding="utf-8")
            send({"jsonrpc": "2.0", "id": pending_prompt_id,
                  "result": {"stopReason": "cancelled"}})
            pending_prompt_id = None
        continue
    else:
        if request_id is not None:
            send({"jsonrpc": "2.0", "id": request_id,
                  "error": {"code": -32601, "message": "Synthetic method unsupported"}})
        continue
    if request_id is not None:
        send({"jsonrpc": "2.0", "id": request_id, "result": result})
