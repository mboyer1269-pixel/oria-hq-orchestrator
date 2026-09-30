"""Real SDK callback remains pending beyond the previous 30-second ceiling."""
import asyncio
import json
import time
from acp.schema import PermissionOption,ToolCallUpdate
from permission_agent import PermissionAgent

async def main():
    agent=PermissionAgent(acp_command=['never-executed'])
    async def review(**request):
        await asyncio.sleep(31)
        return {'outcome':{'outcome':'selected','optionId':'once'}}
    agent.set_permission_callback(review,timeout_seconds=210)
    try:agent.set_permission_callback(review,timeout_seconds=211)
    except ValueError:pass
    else:raise AssertionError('Unbounded timeout accepted')
    tool=ToolCallUpdate.model_validate({'toolCallId':'call','rawInput':{'command':'npm test'}})
    options=[PermissionOption.model_validate({'optionId':'once','name':'Once','kind':'allow_once'})]
    start=time.monotonic()
    response=await agent.create_acp_bridge().request_permission('session',tool,options)
    assert response.outcome.option_id=='once'
    assert time.monotonic()-start>=31
    print(json.dumps({'actualSdkCallback':True,'waitedBeyond30Seconds':True,'maximum210SecondsEnforced':True,'modelCalls':0}))

if __name__=='__main__':asyncio.run(main())
