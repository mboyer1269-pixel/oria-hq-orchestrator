"""Disposable VPS probe. Creates only private, uniquely named qualification resources."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
import uuid

RUNTIME='sha256:3d8c97af6b8f1e6979596709f659124ca8f0319d5949e0f6f06f9c0287a7e11e'


def command(*args,check=True,timeout=60):
    return subprocess.run(args,text=True,capture_output=True,check=check,timeout=timeout)


def main():
    if os.geteuid()!=0:raise RuntimeError('Linux root qualification required')
    source=Path(__file__).resolve().parent
    run_id='hq-provider-probe-'+uuid.uuid4().hex[:12]
    folder=source/run_id;folder.mkdir(mode=0o700)
    ipc=folder/'ipc';ipc.mkdir(mode=0o700);os.chown(ipc,10001,10001)
    proxy_id=None;network_id=None;probe_id=None
    evidence={'runId':run_id,'runtimeImage':RUNTIME,'credentialsMounted':False,'portsPublished':False}
    try:
        built=command('docker','build','--tag',run_id,str(source),timeout=300)
        (folder/'build.log').write_text(built.stdout+built.stderr)
        image=command('docker','image','inspect',run_id,'--format','{{.Id}}').stdout.strip()
        evidence['proxyImage']=image
        policy={'version':1,'provider':'claude','authentication':'subscription',
                'network':'restricted-proxy','agentNetwork':'none','accountConnectors':'disabled',
                'runtimeImage':RUNTIME,'proxyImage':image,'relayPort':3129,'socketPath':'/provider/provider.sock',
                'files':{name:hashlib.sha256((source/name).read_bytes()).hexdigest()
                         for name in ('squid.conf','entrypoint.sh','relay.mjs')}}
        policy_bytes=json.dumps(policy,sort_keys=True,separators=(',',':')).encode('utf-8')
        (folder/'policy.json').write_bytes(policy_bytes)
        evidence['policySha256']=hashlib.sha256(policy_bytes).hexdigest()
        network_id=command('docker','network','create','--label','oria.purpose=provider-qualification',run_id).stdout.strip()
        proxy_id=command('docker','run','-d','--name',run_id,'--network',run_id,
            '--label','oria.purpose=provider-qualification','--read-only','--user','10001:10001',
            '--cap-drop','ALL','--security-opt','no-new-privileges:true','--pids-limit','64',
            '--memory','256m','--cpus','0.5','--tmpfs','/tmp:rw,nosuid,nodev,size=32m,uid=10001,gid=10001',
            '--mount',f'type=bind,src={ipc},dst=/ipc',image).stdout.strip()
        for _ in range(30):
            if (ipc/'provider.sock').exists():break
            status=command('docker','inspect',proxy_id,'--format','{{.State.Running}}').stdout.strip()
            if status!='true':raise RuntimeError('Proxy exited before readiness')
            time.sleep(0.2)
        else:raise RuntimeError('Proxy socket unavailable')
        # Squid parses before the relay opens. Brief polling verifies its listener.
        for _ in range(30):
            listening=command('docker','exec',proxy_id,'/usr/bin/socat','-T1','-','TCP:127.0.0.1:3128',check=False,timeout=3)
            if listening.returncode==0:break
            time.sleep(0.2)
        else:raise RuntimeError('Proxy listener unavailable')
        args=['docker','create','--name',run_id+'-client','--entrypoint','python',
              '--network','none','--read-only','--user','10001:10001',
              '--cap-drop','ALL','--security-opt','no-new-privileges:true','--pids-limit','32',
              '--memory','128m','--cpus','0.5','--mount',f'type=bind,src={ipc},dst=/provider,readonly',
              '--mount',f'type=bind,src={source / "relay.mjs"},dst=/relay.mjs,readonly',
              '--mount',f'type=bind,src={source / "probe.py"},dst=/probe.py,readonly',RUNTIME,'/probe.py']
        probe_id=command(*args).stdout.strip()
        for container,network in ((proxy_id,run_id),(probe_id,'none')):
            actual=json.loads(command('docker','inspect',container).stdout)[0]
            host=actual['HostConfig']
            assert host['NetworkMode']==network and host['ReadonlyRootfs'] is True
            assert not host['PortBindings'] and host['Privileged'] is False
            assert actual['Config']['User']=='10001:10001'
            assert 'ALL' in host['CapDrop'] and 'no-new-privileges:true' in host['SecurityOpt']
            assert all(mount['Destination']!='/var/run/docker.sock' for mount in actual['Mounts'])
            if container==probe_id:assert all(not mount['RW'] for mount in actual['Mounts'])
        evidence['dockerBoundariesInspected']=True
        measured=command('docker','start','--attach',probe_id,timeout=120)
        evidence['probe']=json.loads(measured.stdout)
        evidence['proxyStats']=command('docker','stats','--no-stream','--format','{{json .}}',proxy_id).stdout.strip()
        print(json.dumps(evidence))
    except subprocess.CalledProcessError as error:
        (folder/'failure.log').write_text((error.stdout or '')+(error.stderr or ''))
        raise
    finally:
        if probe_id:command('docker','rm','-f',probe_id,check=False)
        if proxy_id:
            logs=command('docker','logs',proxy_id,check=False)
            (folder/'proxy.log').write_text(logs.stdout+logs.stderr)
            command('docker','rm','-f',proxy_id,check=False)
        if network_id:command('docker','network','rm',network_id,check=False)
        (folder/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')


if __name__=='__main__':main()
