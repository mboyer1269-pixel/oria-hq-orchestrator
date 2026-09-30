"""Host socket -> UID10001 container, no network/provider or HQ approval."""
import asyncio
import json
import os
from pathlib import Path
import shutil
import tempfile
import uuid
from permission_transport import serve_permissions

IMAGE='sha256:152df564b18fd7381e0bdfdd18ff57918eb9fa9a6e1d47a4820318e34c159da2'
CLIENT='''
import asyncio,json,os
from acp.schema import PermissionOption,ToolCallUpdate
from permission_transport import request_permission
async def main():
    assert os.getuid()==10001
    try:
        open('/ipc/forbidden','w').close()
        raise AssertionError('IPC mount writable')
    except OSError:pass
    response=await request_permission('/ipc/permission.sock',session_id='session',
        tool_call=ToolCallUpdate.model_validate({'toolCallId':'call','rawInput':{'command':'npm test'}}),
        options=[PermissionOption.model_validate({'optionId':'once','name':'Once','kind':'allow_once'})])
    assert response['outcome']['optionId']=='once',response
    print(json.dumps({'containerUid':os.getuid(),'readonlyIpc':True,'hostResponseReceived':True}))
asyncio.run(main())
'''


async def main():
    with tempfile.TemporaryDirectory(prefix='hq-ipc-') as temporary:
        root=Path(temporary);root.chmod(0o755)
        ipc=root/'ipc';ipc.mkdir(mode=0o755)
        code=root/'code';code.mkdir(mode=0o755)
        shutil.copyfile(Path(__file__).with_name('permission_transport.py'),code/'permission_transport.py')
        (code/'client.py').write_text(CLIENT)
        for file in code.iterdir():file.chmod(0o444)
        calls=[]
        async def handler(**request):
            calls.append(request)
            return {'outcome':{'outcome':'selected','optionId':'once'}}
        server=await serve_permissions(str(ipc/'permission.sock'),handler,uid=10001)
        process=None
        container_name='hq-ipc-qualification-'+uuid.uuid4().hex
        try:
            process=await asyncio.create_subprocess_exec('docker','run','--rm','--name',container_name,'--network','none',
                '--read-only','--user','10001:10001','--cap-drop','ALL','--security-opt','no-new-privileges',
                '--memory','256m','--pids-limit','64',
                '--mount',f'type=bind,src={ipc},dst=/ipc,readonly',
                '--mount',f'type=bind,src={code},dst=/qualification,readonly',
                '--entrypoint','python',IMAGE,'/qualification/client.py',
                stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE)
            stdout,stderr=await asyncio.wait_for(process.communicate(),timeout=40)
            if process.returncode:raise RuntimeError(stderr.decode())
            assert len(calls)==1 and calls[0]['tool_call']['toolCallId']=='call'
            print(stdout.decode().strip())
            print(json.dumps({'crossContainerSocket':True,'hostHandlerSynthetic':True,'modelCalls':0}))
        finally:
            server.close();await server.wait_closed()
            if process is not None and process.returncode is None:
                process.kill();await process.wait()
            cleanup=await asyncio.create_subprocess_exec('docker','rm','-f',container_name,
                stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE)
            _,error=await cleanup.communicate()
            if cleanup.returncode and b'No such container' not in error:
                raise RuntimeError('Qualification container cleanup requires review')

if __name__=='__main__':asyncio.run(main())
