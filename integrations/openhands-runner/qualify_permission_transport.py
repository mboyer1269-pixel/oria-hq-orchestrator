"""Real ACP schemas -> Unix IPC -> host binding; no provider/model invocation."""
import asyncio
import json
import os
import tempfile
from acp.schema import PermissionOption,ToolCallUpdate
from permission_transport import request_permission,serve_permissions
from permission_host import host_handler


async def main():
    captured=[];transitions=[]
    job=dict(workspaceId='fixture',missionId='11111111-1111-4111-8111-111111111111',
             launchId='22222222-2222-4222-8222-222222222222',runnerId='fixture',containerId='a'*64)
    def transition(before,after,data):
        transitions.append((before,after,data));return True
    def consume(request):
        captured.append(request)
        return {'outcome':{'outcome':'selected','optionId':'once'}}
    handler=host_handler(job=job,transition=transition,consume=consume)
    with tempfile.TemporaryDirectory() as directory:
        socket=directory+'/permission.sock'
        server=await serve_permissions(socket,handler,uid=os.getuid())
        options=[PermissionOption.model_validate({'optionId':'once','name':'Allow once','kind':'allow_once'})]
        tool=ToolCallUpdate.model_validate({'toolCallId':'call','rawInput':{'command':'npm test'}})
        try:
            response=await request_permission(socket,session_id='session',tool_call=tool,options=options)
            assert response['outcome']['optionId']=='once',response
            assert len(transitions)==1
            assert captured[0]['containerId']==job['containerId']
            assert json.loads(captured[0]['inputJson'])=={'command':'npm test'}
            changed=await request_permission(socket,session_id='foreign',tool_call=tool,options=options)
            assert changed['outcome']['outcome']=='cancelled'
            assert len(captured)==1
        finally:server.close();await server.wait_closed()
    print(json.dumps({'realAcpSchemas':True,'realUnixSocket':True,'hostBoundIdentity':True,
                      'changedSessionDenied':True,'hqAuthorityMocked':True,'modelCalls':0}))

if __name__=='__main__':asyncio.run(main())
