"""Dedicated provider gateway lifecycle; caller must separately authorize the job."""
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import stat
import time
import uuid
import math
from provider_policy import ROOT,load_provider_policy,protected_bytes
from supervisor import docker


def resource_id(result):
    value=result.stdout.strip()
    if not re.fullmatch(r'[a-f0-9]{64}',value):raise RuntimeError('Unknown resource creation outcome')
    return value


def inspect_gateway(*, root, launch_id):
    """Read-only recovery evidence; never infer live state from the journal."""
    if str(uuid.UUID(launch_id))!=launch_id:raise ValueError('Canonical launch ID required')
    journal=json.loads(protected_bytes(Path(root)/launch_id/'lifecycle.json',65536))
    name='hq-provider-'+launch_id
    if journal.get('launchId')!=launch_id or journal.get('name')!=name:
        raise ValueError('Gateway journal identity mismatch')
    result={'launchId':launch_id,'journalState':journal.get('state'),
            'containerState':'unknown','networkState':'unknown','automaticRetry':False,
            'resourcesModified':False}
    try:
        ids=docker('ps','-a','--no-trunc','--filter','name=^/'+name+'$','--format','{{.ID}}').stdout.split()
        if not ids:result['containerState']='absent'
        elif len(ids)==1 and re.fullmatch(r'[a-f0-9]{64}',ids[0]):
            info=json.loads(docker('inspect','--format',
                '[{{json .Id}},{{json .Name}},{{json .Config.Labels}},{{json .State.Status}}]',ids[0]).stdout)
            labels=info[2] or {}
            if (info[0]!=ids[0] or info[1]!='/'+name
                or labels.get('oria.purpose')!='provider-gateway'
                or labels.get('oria.launch-id')!=launch_id
                or journal.get('containerId') not in (None,ids[0])):
                result['containerState']='identity_mismatch'
            else:result.update(containerState=info[3],containerId=ids[0])
        network_ids=docker('network','ls','--no-trunc','--filter','name=^'+name+'$','--format','{{.ID}}').stdout.split()
        if not network_ids:result['networkState']='absent'
        elif len(network_ids)==1 and re.fullmatch(r'[a-f0-9]{64}',network_ids[0]):
            info=json.loads(docker('network','inspect','--format',
                '[{{json .Id}},{{json .Name}},{{json .Labels}},{{json .Containers}}]',network_ids[0]).stdout)
            if (info[0]!=network_ids[0] or info[1]!=name or (info[2] or {}).get('oria.purpose')!='provider-gateway'
                or journal.get('networkId') not in (None,network_ids[0])):
                result['networkState']='identity_mismatch'
            else:result.update(networkState='present',networkId=network_ids[0],attachedContainers=len(info[3] or {}))
    except Exception:result['inspectionIncomplete']=True
    result['reconciliationRequired']=(result['containerState']!='absent' or result['networkState']!='absent'
                                      or result.get('inspectionIncomplete',False))
    return result


def write_journal(folder,journal):
    """Atomic durable journal write; the only writer of this file."""
    target=folder/'lifecycle.json'
    temporary=folder/'lifecycle.tmp'
    with temporary.open('w',encoding='utf-8') as stream:
        json.dump(journal,stream);stream.flush();os.fsync(stream.fileno())
    os.replace(temporary,target)
    descriptor=os.open(folder,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(descriptor)
    finally:os.close(descriptor)


TERMINAL_LAUNCH_STATES=('execution_finished','cancelled','succeeded','failed')


def release_gateway(*, root, launch_id, canonical_state, observed=None):
    """Remove only resources this launch's labels and journal already identify.

    The canonical launch must already be terminal, so no mission can still be
    entitled to this gateway; the caller is responsible for having observed that
    its agent container cannot act either. Never touches an unverified or
    partially observed resource, and always retains the journal as evidence.
    """
    if canonical_state not in TERMINAL_LAUNCH_STATES:
        raise ValueError('Gateway release requires a terminal canonical launch')
    observed=observed if observed is not None else inspect_gateway(root=root,launch_id=launch_id)
    if observed.get('inspectionIncomplete'):raise RuntimeError('Gateway inspection incomplete')
    if 'identity_mismatch' in (observed['containerState'],observed['networkState']):
        raise RuntimeError('Gateway identity mismatch; never remove an unverified resource')
    folder=Path(root)/launch_id
    journal=json.loads(protected_bytes(folder/'lifecycle.json',65536))
    removed={'container':None,'network':None};errors=[]
    if observed.get('containerId'):
        try:docker('rm','-f',observed['containerId'],timeout=20);removed['container']=observed['containerId']
        except Exception:errors.append('container_cleanup_unknown')
    if observed.get('networkId'):
        try:docker('network','rm',observed['networkId']);removed['network']=observed['networkId']
        except Exception:errors.append('network_cleanup_unknown')
    journal['releaseErrors']=errors
    journal['state']='reconciliation_required' if errors else 'released'
    write_journal(folder,journal)
    if errors:raise RuntimeError('Gateway release requires reconciliation')
    return {'launchId':launch_id,'removed':removed,'journalState':journal['state']}


def wait_ready(path,timeout=10):
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        try:
            info=path.lstat()
            if not stat.S_ISSOCK(info.st_mode) or info.st_uid!=10001 or stat.S_IMODE(info.st_mode)!=0o600:
                raise ValueError('Unexpected gateway socket')
            with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as client:
                client.settimeout(0.5);client.connect(str(path))
                client.sendall(b'CONNECT example.com:443 HTTP/1.1\r\nHost: example.com:443\r\n\r\n')
                line=b''
                while b'\r\n' not in line and len(line)<1024 and time.monotonic()<deadline:
                    block=client.recv(1)
                    if not block:break
                    line+=block
                if line.startswith(b'HTTP/1.1 403 ') or line.startswith(b'HTTP/1.0 403 '):return
        except (FileNotFoundError,ConnectionError,TimeoutError):pass
        time.sleep(0.1)
    raise RuntimeError('Gateway readiness not confirmed')


@contextmanager
def provider_gateway(*,config,launch_id,root,policy_root=ROOT,deadline_monotonic=None):
    """No credential access. Retain journal/paths, close only resources created here.

    This helper does not accept Docker arguments from agents and does not claim
    a mission. Unknown creates are left for reconciliation by deterministic name.
    """
    if os.name!='posix' or os.geteuid()!=0:raise ValueError('Linux root required')
    if str(uuid.UUID(launch_id))!=launch_id:raise ValueError('Canonical launch ID required')
    duration=config.get('timeoutSeconds')
    if type(duration) is not int or not 1<=duration<=1800:raise ValueError('Bounded mission deadline required')
    # Startup allowance is bounded; GNU timeout runs independently of this host
    # process and terminates the proxy process group if the host disappears.
    lifetime=duration+15
    if deadline_monotonic is not None:
        if type(deadline_monotonic) not in (int,float) or not math.isfinite(deadline_monotonic):raise ValueError('Invalid shared deadline')
        remaining=min(duration,deadline_monotonic-time.monotonic())
        if remaining<=0:raise TimeoutError('Mission deadline elapsed before gateway creation')
        expires_ms=int(time.time()*1000)+int(remaining*1000)
    else:expires_ms=None
    policy=load_provider_policy(config,policy_root)
    root=Path(root)
    if not root.is_absolute() or root.resolve(strict=True)!=root or not root.is_dir():raise ValueError('Protected gateway root required')
    for path in (root,*root.parents):
        info=path.stat()
        if info.st_uid!=0 or info.st_mode & 0o022:raise ValueError('Unprotected gateway root')
    if ',' in str(root):raise ValueError('Invalid mount path')
    if len(os.fsencode(root/launch_id/'ipc'/'provider.sock'))>=108:
        raise ValueError('Gateway root exceeds Linux Unix socket path limit')
    # Copy exact protected bytes before creating Docker resources; no mutable
    # source mount can change the policy between verification and execution.
    artifacts={name:protected_bytes(Path(policy_root)/config['providerProfile']['id']/name,65536) for name in policy['files']}
    if any(hashlib.sha256(raw).hexdigest()!=policy['files'][name] for name,raw in artifacts.items()):raise ValueError('Policy changed during preparation')
    folder=root/launch_id;folder.mkdir(mode=0o700)
    for name,raw in artifacts.items():
        (folder/name).write_bytes(raw);(folder/name).chmod(0o444)
    ipc=folder/'ipc';ipc.mkdir(mode=0o700);os.chown(ipc,10001,10001)
    name='hq-provider-'+launch_id
    journal={'launchId':launch_id,'name':name,'policySha256':config['providerProfile']['policySha256'],
             'networkId':None,'containerId':None,'state':'prepared',
             'lifetimeSeconds':lifetime,'terminationGraceSeconds':5}
    if expires_ms is not None:journal['sharedDeadlineUnixMs']=expires_ms
    def save(state):
        journal['state']=state
        write_journal(folder,journal)
    uncertain=False
    def remaining_timeout(limit):
        if deadline_monotonic is None:return limit
        remaining=deadline_monotonic-time.monotonic()
        if remaining<=0:raise TimeoutError('Mission deadline elapsed during gateway preparation')
        return min(limit,remaining)
    try:
        if deadline_monotonic is not None and time.monotonic()>=deadline_monotonic:
            raise TimeoutError('Mission deadline elapsed before gateway network')
        save('network_creation_requested');uncertain=True
        journal['networkId']=resource_id(docker('network','create','--label','oria.purpose=provider-gateway',name,timeout=remaining_timeout(30)))
        uncertain=False;save('network_created')
        if deadline_monotonic is not None and time.monotonic()>=deadline_monotonic:
            raise TimeoutError('Mission deadline elapsed before proxy creation')
        entry=['--entrypoint','/usr/bin/timeout',policy['proxyImage'],'--signal=TERM','--kill-after=5s',
               str(lifetime)+'s','/bin/bash','/opt/proxy-entrypoint.sh']
        if expires_ms is not None:
            # Compute the remaining time inside the container when it actually
            # starts; Docker creation latency must not extend provider access.
            script='remaining=$(($1-$(date +%s%3N))); ((remaining>0)) || exit 124; ((remaining<=$2)) || remaining=$2; printf -v seconds "%d.%03d" "$((remaining/1000))" "$((remaining%1000))"; exec /usr/bin/timeout --signal=TERM --kill-after=5s "${seconds}s" /bin/bash /opt/proxy-entrypoint.sh'
            entry=['--entrypoint','/bin/bash',policy['proxyImage'],'-c',script,'hq-deadline',str(expires_ms),str(duration*1000)]
        save('container_creation_requested');uncertain=True
        journal['containerId']=resource_id(docker('create','--name',name,'--network',journal['networkId'],
            '--label','oria.purpose=provider-gateway','--label','oria.launch-id='+launch_id,
            '--restart','no','--read-only','--user','10001:10001','--cap-drop','ALL','--security-opt','no-new-privileges:true',
            '--pids-limit','64','--memory','256m','--cpus','0.5','--log-driver','json-file',
            '--log-opt','max-size=1m','--log-opt','max-file=2',
            '--tmpfs','/tmp:rw,nosuid,nodev,size=32m,uid=10001,gid=10001',
            '--mount',f'type=bind,src={ipc},dst=/ipc',
            '--mount',f'type=bind,src={folder / "squid.conf"},dst=/etc/squid/squid.conf,readonly',
            '--mount',f'type=bind,src={folder / "entrypoint.sh"},dst=/opt/proxy-entrypoint.sh,readonly',
            *entry,timeout=remaining_timeout(30)))
        uncertain=False;save('container_created')
        docker('start',journal['containerId'],timeout=remaining_timeout(30))
        readiness_timeout=10 if deadline_monotonic is None else min(10,max(0,deadline_monotonic-time.monotonic()))
        wait_ready(ipc/'provider.sock',timeout=readiness_timeout);save('ready')
        yield {'containerId':journal['containerId'],'networkId':journal['networkId'],
               'ipcPath':str(ipc),'relayPath':str(folder/'relay.mjs'),'policy':policy}
    finally:
        errors=[]
        if journal['containerId']:
            try:docker('rm','-f',journal['containerId'],timeout=20)
            except Exception:errors.append('container_cleanup_unknown')
        if journal['networkId']:
            try:docker('network','rm',journal['networkId'])
            except Exception:errors.append('network_cleanup_unknown')
        journal['cleanupErrors']=errors
        save('reconciliation_required' if uncertain or errors else 'closed')
        if errors:raise RuntimeError('Gateway cleanup requires reconciliation')
