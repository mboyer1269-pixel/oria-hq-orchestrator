"""Host-only container creation; caller must hold the durable HQ launch claim.

No start, credentials, network selection or arbitrary Docker flags are accepted.
Creation errors require reconciliation by deterministic name, never auto-retry.
"""
from pathlib import Path
import os
import re
import uuid
import hashlib
import stat
import json
import math
import time
from provider_policy import protected_bytes
from supervisor import docker


def create_job(*, launch_id, image_digest, workspace_id, job_root, permission_channel=False, provider=None,deadline_monotonic=None):
    if deadline_monotonic is not None and (type(deadline_monotonic) not in (int,float) or not math.isfinite(deadline_monotonic)):
        raise ValueError('Invalid creation deadline')
    if type(permission_channel) is not bool:raise ValueError('Host channel flag required')
    if str(uuid.UUID(launch_id)) != launch_id:
        raise ValueError('Canonical launch UUID required')
    if not re.fullmatch(r'sha256:[a-f0-9]{64}', image_digest):
        raise ValueError('Pinned image required')
    if not isinstance(workspace_id, str) or not 1 <= len(workspace_id) <= 160:
        raise ValueError('Workspace ID required')
    root=Path(job_root)
    if not root.is_absolute() or root.resolve(strict=True)!=root or not root.is_dir():
        raise ValueError('Real absolute job directory required')
    paths={name:root/name for name in ('checkout','results','dossier.json')}
    for name,path in paths.items():
        if path.resolve(strict=True)!=path or ',' in str(path):
            raise ValueError('Unsafe mount path')
        if name=='dossier.json':
            if not path.is_file(): raise ValueError('Dossier file required')
        elif not path.is_dir(): raise ValueError('Job directory required')
    # The host owns these paths; they must never be taken from a browser payload.
    # Explicit mounts expose neither the original repository nor Docker socket.
    channel_mount=[]
    provider_mount=[]
    if provider is not None:
        # Host-selected active gateway, never a field from a browser/dossier.
        if not isinstance(provider,dict) or set(provider)!={'containerId','networkId','ipcPath','relayPath','policy'}:
            raise ValueError('Verified host gateway required')
        policy=provider['policy']
        if policy['runtimeImage']!=image_digest:raise ValueError('Provider runtime image mismatch')
        relay=Path(provider['relayPath']);ipc=Path(provider['ipcPath'])
        if relay.name!='relay.mjs' or ipc!=relay.parent/'ipc' or relay.parent.name!=launch_id:
            raise ValueError('Gateway paths must belong to this launch')
        if ',' in str(ipc) or ',' in str(relay):raise ValueError('Unsafe provider mount')
        if hashlib.sha256(protected_bytes(relay,65536)).hexdigest()!=policy['files']['relay.mjs']:
            raise ValueError('Relay artifact mismatch')
        if ipc.resolve(strict=True)!=ipc or not ipc.is_dir():raise ValueError('Real gateway directory required')
        info=ipc.stat();sock=(ipc/'provider.sock').lstat()
        if info.st_uid!=10001 or stat.S_IMODE(info.st_mode)!=0o700 or not stat.S_ISSOCK(sock.st_mode) or sock.st_uid!=10001 or stat.S_IMODE(sock.st_mode)!=0o600:
            raise ValueError('Unexpected gateway socket permissions')
        if not isinstance(provider['containerId'],str) or not re.fullmatch(r'[a-f0-9]{64}',provider['containerId']):
            raise ValueError('Full gateway container identity required')
        inspection_timeout=10 if deadline_monotonic is None else min(10,deadline_monotonic-time.monotonic())
        if inspection_timeout<=0:raise TimeoutError('Mission deadline elapsed before gateway inspection')
        observed=json.loads(docker('inspect','--format',
            '[{{json .State.Running}},{{json .Image}},{{json (index .Config.Labels "oria.launch-id")}},{{json (index .Config.Labels "oria.purpose")}}]',
            provider['containerId'],timeout=inspection_timeout).stdout)
        if observed!=[True,policy['proxyImage'],launch_id,'provider-gateway']:
            raise ValueError('Gateway is not live and bound to this launch')
        provider_mount=['--mount',f'type=bind,src={ipc},dst=/provider,readonly',
                        '--mount',f'type=bind,src={relay},dst=/provider-relay.mjs,readonly']
    if permission_channel:
        ipc=root/'ipc'
        if ipc.resolve(strict=True)!=ipc or not ipc.is_dir() or ',' in str(ipc):
            raise ValueError('Private IPC directory required')
        info=ipc.stat()
        if os.name!='posix' or info.st_uid!=0 or info.st_mode & 0o022:
            raise ValueError('IPC directory must be host-owned and not writable by the job')
        channel_mount=['--mount',f'type=bind,src={ipc},dst=/ipc,readonly']
    args=['create','--name','hq-openhands-'+launch_id,
          '--label','oria.purpose=openhands-supervised-job',
          '--label','oria.launch-id='+launch_id,
          '--network','none','--read-only','--user','10001:10001',
          '--cap-drop','ALL','--security-opt','no-new-privileges:true',
          '--pids-limit','128','--memory','1g','--cpus','1',
          '--log-driver','json-file','--log-opt','max-size=10m','--log-opt','max-file=2',
          '--tmpfs','/tmp:rw,nosuid,nodev,size=128m,mode=1777',
          '--tmpfs','/home/runner:rw,nosuid,nodev,size=32m,uid=10001,gid=10001',
          '--mount',f'type=bind,src={paths["checkout"]},dst=/workspace',
          '--mount',f'type=bind,src={paths["results"]},dst=/results',
          '--mount',f'type=bind,src={paths["dossier.json"]},dst=/mission.json,readonly',
          *channel_mount,*provider_mount,image_digest,'--dossier','/mission.json','--workspace-id',workspace_id,
          *(['--provider-relay'] if provider is not None else []),
          *(['--permission-channel'] if permission_channel else [])]
    remaining=30 if deadline_monotonic is None else min(30,deadline_monotonic-time.monotonic())
    if remaining<=0:raise TimeoutError('Mission deadline elapsed before container creation')
    result=docker(*args,timeout=remaining)
    container_id=result.stdout.strip()
    if not re.fullmatch(r'[a-f0-9]{64}',container_id):
        raise RuntimeError('Creation outcome requires reconciliation')
    return {'containerId':container_id,'containerName':'hq-openhands-'+launch_id,
            'state':'container_created','started':False}
