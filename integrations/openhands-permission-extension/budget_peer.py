"""Echo metadata actually received on ACP wire; no model or tool execution."""
import json
import sys
received=None
for line in sys.stdin:
    request=json.loads(line)
    method=request.get("method")
    if method=="initialize":
        result={"protocolVersion":1,"agentCapabilities":{},"authMethods":[],
                "agentInfo":{"name":"hq-budget-peer","version":"1"}}
    elif method=="session/new":
        received=request["params"].get("_meta",{})
        result={"sessionId":"synthetic","modes":{"currentModeId":"default",
                "availableModes":[{"id":"default","name":"Default"}]}}
    elif method=="session/set_mode":
        assert request["params"]["modeId"]=="default"
        result={}
    elif method=="session/prompt":
        print(json.dumps({"jsonrpc":"2.0","method":"session/update","params":{"sessionId":"synthetic",
            "update":{"sessionUpdate":"agent_message_chunk","content":{"type":"text",
                      "text":"HQ_BUDGET_RECEIVED:"+json.dumps(received,sort_keys=True)}}}}),flush=True)
        result={"stopReason":"end_turn"}
    elif method=="session/cancel": continue
    else: raise AssertionError(method)
    if "id" in request:
        print(json.dumps({"jsonrpc":"2.0","id":request["id"],"result":result}),flush=True)
