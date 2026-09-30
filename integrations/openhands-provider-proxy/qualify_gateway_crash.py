"""Kill the host helper with SIGKILL; observe container-enforced proxy expiry."""
import hashlib
import json
import multiprocessing
from pathlib import Path
import socket
import subprocess
import sys
import time
import uuid
from unittest.mock import patch

sys.path.insert(0,'/opt/oria-openhands-qualification/provider-gateway-check')
from provider_gateway import provider_gateway
from provider_policy import EXPECTED
import provider_gateway as gateway_module


def docker(*args):
    return subprocess.run(['docker',*args],capture_output=True,text=True,check=True,timeout=15)


def child(pipe,config,launch,root,policies,shared):
    real_docker=gateway_module.docker
    def delayed(*args,**kwargs):
        if shared and args[0]=='start':time.sleep(2)
        return real_docker(*args,**kwargs)
    with patch.object(gateway_module,'docker',side_effect=delayed):
        with provider_gateway(config=config,launch_id=launch,root=root,policy_root=policies,
                              **({'deadline_monotonic':time.monotonic()+6} if shared else {})) as gateway:
            pipe.send(gateway);pipe.close()
            time.sleep(120)


def main():
    policies=Path('/opt/oria-openhands-qualification/provider-policy-check/qualified')
    raw=(policies/'claude-subscription-v1/policy.json').read_bytes();policy=json.loads(raw)
    shared='--shared-deadline' in sys.argv
    config={'imageDigest':policy['runtimeImage'],'timeoutSeconds':30 if shared else 1,'providerProfile':{
        **EXPECTED,'id':'claude-subscription-v1','policySha256':hashlib.sha256(raw).hexdigest()}}
    root=Path('/opt/oria-openhands-qualification/gateways');root.mkdir(mode=0o700,exist_ok=True)
    launch=str(uuid.uuid4());receiver,sender=multiprocessing.Pipe(duplex=False)
    process=multiprocessing.Process(target=child,args=(sender,config,launch,root,policies,shared))
    gateway=None;started=time.monotonic()
    try:
        process.start();sender.close()
        if not receiver.poll(15):raise RuntimeError('Gateway child not ready')
        gateway=receiver.recv()
        assert json.loads(docker('inspect','--format','{{json .State}}',gateway['containerId']).stdout)['Running']
        process.kill();process.join(timeout=5)
        assert process.exitcode==-9
        while time.monotonic()-started<30:
            state=json.loads(docker('inspect','--format','{{json .State}}',gateway['containerId']).stdout)
            if not state['Running']:break
            time.sleep(0.25)
        else:raise AssertionError('Proxy survived enforced lifetime')
        assert state['Status']=='exited' and state['ExitCode'] in (124,137)
        with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as stream:
            stream.settimeout(1)
            try:stream.connect(str(Path(gateway['ipcPath'])/'provider.sock'))
            except OSError:pass
            else:raise AssertionError('Expired proxy still accepts connections')
        journal=json.loads((root/launch/'lifecycle.json').read_text())
        if shared:assert time.monotonic()-started<11
        evidence={'launchId':launch,'hostKilledBySigkill':True,'proxyStoppedWithoutHostCleanup':True,
                  'proxyExitCode':state['ExitCode'],'elapsedSeconds':round(time.monotonic()-started,3),
                  'lifetimeSeconds':journal['lifetimeSeconds'],'graceSeconds':journal['terminationGraceSeconds'],
                  'journalStateAfterCrash':journal['state'],'socketAcceptsConnections':False,'modelRequests':0,
                  'sharedDeadline':shared,'startupDelaySeconds':2 if shared else 0,
                  'sharedBudgetSeconds':6 if shared else None}
    finally:
        if process.is_alive():process.kill();process.join(timeout=5)
        receiver.close()
        if gateway:
            docker('rm','-f',gateway['containerId']);docker('network','rm',gateway['networkId'])
    evidence['qualificationResourcesRemoved']=True
    filename='gateway-shared-deadline-evidence.json' if shared else 'gateway-crash-evidence.json'
    (Path(__file__).parent/filename).write_text(json.dumps(evidence,indent=2)+'\n')
    print(json.dumps(evidence))


if __name__=='__main__':main()
