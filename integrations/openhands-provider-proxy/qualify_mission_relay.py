"""Real SDK/mission entry point with explicit synthetic ACP, no account or model."""
import hashlib
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid

sys.path.insert(0,'/opt/oria-openhands-qualification/provider-gateway-check')
from container_job import create_job
from dossier import digest
from provider_gateway import provider_gateway
from provider_policy import EXPECTED
from supervisor import supervise

IMAGE='sha256:ecfafc87bc148d922dd4d43c3c5d3bb80f4a0828e4ff9af22ef80b7bd5c2924d'


def main():
    source=Path(__file__).resolve().parent
    launch=str(uuid.uuid4());root=Path('/opt/oria-openhands-qualification/relay-jobs');root.mkdir(mode=0o700,exist_ok=True)
    folder=root/launch;folder.mkdir(mode=0o700)
    repo=folder/'checkout';repo.mkdir();results=folder/'results';results.mkdir()
    def git(*args):return subprocess.check_output(['git','-C',str(repo),*args],text=True,stderr=subprocess.DEVNULL).strip()
    git('init');git('-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','--allow-empty','-m','fixture')
    data=json.loads(Path('/opt/oria-openhands-qualification/relay-runtime/fixtures/hq-memory-dossier.json').read_text())
    data['source']['commitSha']=git('rev-parse','HEAD')
    data['payloadHash']=digest({key:value for key,value in data.items() if key not in ('payloadHash','idempotencyKey')})
    (folder/'dossier.json').write_text(json.dumps(data))
    for directory in (repo,results):
        for current,dirs,files in os.walk(directory):
            os.chown(current,10001,10001)
            for filename in files:os.chown(Path(current)/filename,10001,10001)
    policies=folder/'policies';policies.mkdir();policy_folder=policies/'synthetic-relay';policy_folder.mkdir()
    existing=Path('/opt/oria-openhands-qualification/provider-policy-check/qualified/claude-subscription-v1')
    policy=json.loads((existing/'policy.json').read_text());policy['runtimeImage']=IMAGE
    for filename in policy['files']:(policy_folder/filename).write_bytes((existing/filename).read_bytes())
    raw=json.dumps(policy,sort_keys=True,separators=(',',':')).encode();(policy_folder/'policy.json').write_bytes(raw)
    config={'imageDigest':IMAGE,'timeoutSeconds':60,'providerProfile':{**EXPECTED,'id':'synthetic-relay','policySha256':hashlib.sha256(raw).hexdigest()}}
    gateways=Path('/opt/oria-openhands-qualification/gateways');gateways.mkdir(mode=0o700,exist_ok=True)
    container=None
    try:
        with provider_gateway(config=config,launch_id=launch,root=gateways,policy_root=policies) as gateway:
            refused=0
            for change in ('image','relay','launch'):
                altered=copy.deepcopy(gateway);selected_launch=launch
                if change=='image':altered['policy']['runtimeImage']='sha256:'+'0'*64
                if change=='relay':altered['policy']['files']['relay.mjs']='0'*64
                if change=='launch':selected_launch=str(uuid.uuid4())
                try:create_job(launch_id=selected_launch,image_digest=IMAGE,workspace_id=data['mission']['workspaceId'],job_root=folder,provider=altered)
                except ValueError:refused+=1
                else:raise AssertionError('Altered provider binding accepted')
            container=create_job(launch_id=launch,image_digest=IMAGE,workspace_id=data['mission']['workspaceId'],job_root=folder,provider=gateway)
            process=supervise(container_id=container['containerId'],timeout_seconds=60)
            assert process['exitCode']==0 and process['containerStopped']
            outcome=json.loads((results/'outcome.json').read_text());assert outcome['state']=='agent_returned'
            assert outcome['independentValidationPassed'] is False
            fixture=json.loads((results/'provider-fixture.json').read_text());assert fixture['providerTlsVerified'] and fixture['foreignHostDenied']
            assert (results/'started.json').exists() and list((results/'conversation').rglob('*'))
        journal=json.loads((gateways/launch/'lifecycle.json').read_text());assert journal['state']=='closed'
        evidence={'launchId':launch,'image':IMAGE,'syntheticAcp':True,'actualSdkAndEntryPoint':True,
                  'process':process,'outcome':outcome,'transport':fixture,'gatewayState':journal['state'],
                  'alteredBindingsRefused':refused,'modelRequests':0}
        (source/'mission-relay-evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
        print(json.dumps(evidence))
    finally:
        if container:
            logs=subprocess.run(['docker','logs',container['containerId']],capture_output=True,text=True,timeout=15)
            (folder/'runtime.log').write_text(logs.stdout+logs.stderr)
            subprocess.run(['docker','rm','-f',container['containerId']],capture_output=True,check=True,timeout=20)


if __name__=='__main__':main()
