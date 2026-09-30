"""Synthetic ACP permission peer, performs no real tool operation."""
import json
import sys

def send(value):
    print(json.dumps(value), flush=True)

for line in sys.stdin:
    request = json.loads(line)
    method = request.get("method")
    ident = request.get("id")
    if method == "initialize":
        result = {"protocolVersion": 1, "agentCapabilities": {}, "authMethods": [],
                  "agentInfo": {"name": "hq-policy-peer", "version": "1.0.0"}}
    elif method == "session/new":
        result = {"sessionId": "synthetic", "modes": {"currentModeId": "default",
                  "availableModes": [{"id": "default", "name": "Default"}]}}
    elif method == "session/set_mode":
        assert request["params"]["modeId"] == "default"
        result = {}
    elif method == "session/prompt":
        send({"jsonrpc": "2.0", "id": "permission", "method": "session/request_permission", "params": {
            "sessionId": "synthetic", "toolCall": {"toolCallId": "probe", "title": "Synthetic", "kind": "execute"},
            "options": [{"optionId": "allow", "name": "Allow", "kind": "allow_once"},
                        {"optionId": "reject", "name": "Reject", "kind": "reject_once"}]}})
        response = json.loads(sys.stdin.readline())
        assert response["id"] == "permission"
        outcome = response["result"]["outcome"]
        if outcome == {"outcome": "cancelled"}:
            marker = "DENIED"
        elif outcome == {"outcome": "selected", "optionId": "allow"}:
            marker = "ALLOWED"
        else:
            raise AssertionError(outcome)
        send({"jsonrpc": "2.0", "method": "session/update", "params": {"sessionId": "synthetic",
              "update": {"sessionUpdate": "agent_message_chunk", "content": {
                  "type": "text", "text": "HQ_PERMISSION_" + marker}}}})
        result = {"stopReason": "end_turn"}
    elif method == "session/cancel":
        continue
    else:
        if ident is not None:
            send({"jsonrpc": "2.0", "id": ident, "error": {"code": -32601, "message": "Unsupported"}})
        continue
    if ident is not None:
        send({"jsonrpc": "2.0", "id": ident, "result": result})
