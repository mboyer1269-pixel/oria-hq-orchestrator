"""Actual HQ Node client to host Python pending registry, no database/model."""
import asyncio
from datetime import datetime,timezone,timedelta
from pathlib import Path
import tempfile
import uuid
from pending_permissions import PendingPermissions
from permission_control import serve_control

ROOT=Path('/opt/oria-openhands-qualification')
CLIENT="""
import assert from 'node:assert/strict';
import {createJiti} from '/workspace/hq/node_modules/jiti/lib/jiti.mjs';
const jiti=createJiti(import.meta.url,{alias:{'@':'/workspace/hq/src','server-only':'/workspace/hq/src/scripts/smoke/server-only-stub.mjs'}});
const {createOpenHandsControlClient}=await jiti.import('/workspace/hq/src/server/missions/openhands-control-client.ts');
const client=createOpenHandsControlClient('/control/review.sock');
const owner={actorId:'owner',workspaceId:'w'};
const ids=await client.list(owner);assert.equal(ids.length,1);
const pending=await client.load(owner,ids[0]);assert.equal(pending.request.toolCallId,'call');
assert.deepEqual(await client.list({...owner,actorId:'foreign'}),[]);
assert.equal(await client.load({...owner,workspaceId:'foreign'},ids[0]),null);
assert.equal(await client.notify(owner,ids[0]),true);
console.log(JSON.stringify({nodePythonInteroperability:true,scopeIsolation:true,notificationOnly:true}));
"""

async def main():
    config=dict(imageDigest='sha256:'+'a'*64,executorVersion='1.50.0',runnerId='r',permissionPolicy='deny',maxCostCents=100,maxTokens=1000,maxIterations=2,timeoutSeconds=60,hardTokenLimitEnforced=False)
    now=datetime.now(timezone.utc)
    request=dict(version=1,workspaceId='w',missionId=str(uuid.uuid4()),launchId=str(uuid.uuid4()),runnerId='r',containerId='a'*64,sessionId='s',toolCallId='call',inputJson='{"command":"npm test"}',options=[dict(optionId='once',kind='allow_once')],requestedAt=now.isoformat(),expiresAt=(now+timedelta(seconds=30)).isoformat())
    pending=PendingPermissions(actor_id='owner',workspace_id='w',config=config)
    with tempfile.TemporaryDirectory(prefix='hq-control-') as temporary:
        root=Path(temporary);root.chmod(0o755)
        control=root/'control';control.mkdir(mode=0o755)
        script=root/'client.mjs';script.write_text(CLIENT);script.chmod(0o444)
        server=await serve_control(str(control/'review.sock'),pending,uid=1000)
        name='hq-control-qualification-'+uuid.uuid4().hex
        try:
            async with pending.publish(request) as request_id:
                mounts=[]
                mounts+=['--mount',f'type=bind,src={ROOT}/lifecycle/openhands-launch-contract.ts,dst=/workspace/hq/src/core/openhands-launch-contract.ts,readonly']
                for filename in ('openhands-control-client.ts','openhands-tool-permission.ts','openhands-launch.ts'):
                    mounts+=['--mount',f'type=bind,src={ROOT}/lifecycle/{filename},dst=/workspace/hq/src/server/missions/{filename},readonly']
                process=await asyncio.create_subprocess_exec('docker','run','--rm','--name',name,'--network','none',
                    '--read-only','--user','1000:1000','--cap-drop','ALL','--security-opt','no-new-privileges',
                    '--memory','512m','--pids-limit','64','--tmpfs','/tmp:rw,nosuid,nodev,size=32m,mode=1777',
                    '--mount',f'type=bind,src={control},dst=/control,readonly',
                    '--mount',f'type=bind,src={script},dst=/qualification.mjs,readonly',*mounts,
                    '--entrypoint','node','sha256:32f6f90cc1ab149069e4436e0ea025cb07f8730be6b1581677dcb76e7a16be85','/qualification.mjs',
                    stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE)
                output,error=await asyncio.wait_for(process.communicate(),25)
                if process.returncode:raise RuntimeError(error.decode())
                assert await pending.wait(request_id)
                print(output.decode().strip())
        finally:
            server.close();await server.wait_closed()
            cleanup=await asyncio.create_subprocess_exec('docker','rm','-f',name,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE)
            _,error=await cleanup.communicate()
            if cleanup.returncode and b'No such container' not in error:raise RuntimeError('Cleanup failed')

if __name__=='__main__':asyncio.run(main())
