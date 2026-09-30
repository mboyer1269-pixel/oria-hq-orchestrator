import concurrent.futures
import importlib.metadata
import json
from pathlib import Path
import signal
import sys
import tempfile
from openhands.sdk import Conversation
from budget_agent import BudgetPermissionAgent
from pydantic import ValidationError


def case(values):
    turns,cents=values
    events=[]
    with tempfile.TemporaryDirectory() as directory:
        agent=BudgetPermissionAgent(hq_max_iterations=turns,hq_max_cost_cents=cents,
            acp_command=[sys.executable,str(Path(__file__).with_name("budget_peer.py"))],
            acp_startup_timeout=8,acp_prompt_timeout=8)
        assert agent.hq_permission_policy=="deny"
        conversation=Conversation(agent=agent,workspace=directory,callbacks=[events.append])
        try:
            conversation.send_message("Echo only the received session metadata.")
            conversation.run()
            expected={"claudeCode":{"options":{"maxTurns":turns,"maxBudgetUsd":cents/100,
                        "allowDangerouslySkipPermissions":False}}}
            marker="HQ_BUDGET_RECEIVED:"+json.dumps(expected,sort_keys=True)
            # Find marker in actual event text, not a re-serialized escaped JSON.
            def strings(value):
                if isinstance(value,str): yield value
                elif isinstance(value,dict):
                    for child in value.values(): yield from strings(child)
                elif isinstance(value,list):
                    for child in value: yield from strings(child)
            assert any(marker in text for event in events for text in strings(event.model_dump(mode="json")))
            return {"maxTurnsReceived":turns,"maxBudgetUsdReceived":cents/100}
        finally: conversation.close()


def main():
    assert importlib.metadata.version("openhands-sdk")=="1.50.0"
    for invalid in ({"hq_permission_policy":"upstream-auto-allow"},
                    {"acp_session_mode":"bypassPermissions"},
                    {"hq_max_iterations":True}, {"hq_max_cost_cents":0}):
        options={"hq_max_iterations":2,"hq_max_cost_cents":125,
                 "acp_command":[sys.executable,"unused-peer"]}
        options.update(invalid)
        try:
            BudgetPermissionAgent(**options)
        except ValidationError:
            pass
        else:
            raise RuntimeError("Unsafe or invalid configuration accepted")
    def expired(*args): raise TimeoutError("Qualification exceeded40seconds")
    signal.signal(signal.SIGALRM,expired)
    signal.alarm(40)
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(case,((2,125),(7,350))))
        print(json.dumps({"instanceBudgetsReceivedOverAcp":results,"permissionsDefaultDeny":True,
             "hardTokenLimitEnforced":False,"providerLimitsEnforced":False,
             "modelCalls":0,"globalMonkeypatch":False}))
    finally: signal.alarm(0)


if __name__=="__main__": main()
