"""Run the host lifecycle against real Docker; qualification only, no model."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import uuid

sys.path.insert(0,'/opt/oria-openhands-qualification/provider-gateway-check')
from provider_gateway import provider_gateway
from provider_policy import EXPECTED


def main():
    source=Path(__file__).resolve().parent
    policies=Path('/opt/oria-openhands-qualification/provider-policy-check/qualified')
    raw=(policies/'claude-subscription-v1/policy.json').read_bytes();policy=json.loads(raw)
    config={'imageDigest':policy['runtimeImage'],'timeoutSeconds':60,'providerProfile':{**EXPECTED,'id':'claude-subscription-v1','policySha256':hashlib.sha256(raw).hexdigest()}}
    root=Path('/opt/oria-openhands-qualification/gateways');root.mkdir(mode=0o700,exist_ok=True)
    results=[]
    for fail in (False,True):
        launch=str(uuid.uuid4());client=None;gateway=None
        try:
            with provider_gateway(config=config,launch_id=launch,root=root,policy_root=policies) as gateway:
                if fail:raise RuntimeError('intentional qualification failure')
                args=['docker','create','--name','hq-provider-lifecycle-probe-'+launch,'--entrypoint','python',
                      '--network','none','--read-only','--user','10001:10001','--cap-drop','ALL',
                      '--security-opt','no-new-privileges:true','--memory','128m','--pids-limit','32','--cpus','0.5',
                      '--mount',f'type=bind,src={gateway["ipcPath"]},dst=/provider,readonly',
                      '--mount',f'type=bind,src={gateway["relayPath"]},dst=/relay.mjs,readonly',
                      '--mount',f'type=bind,src={source / "probe.py"},dst=/probe.py,readonly',policy['runtimeImage'],'/probe.py']
                client=subprocess.run(args,capture_output=True,text=True,check=True,timeout=30).stdout.strip()
                try:
                    process=subprocess.run(['docker','start','--attach',client],capture_output=True,text=True,check=True,timeout=120)
                    probe=json.loads(process.stdout);assert probe['passed']
                finally:
                    subprocess.run(['docker','rm','-f',client],capture_output=True,check=True,timeout=20)
        except RuntimeError as error:
            if not fail or str(error)!='intentional qualification failure':raise
        journal=json.loads((root/launch/'lifecycle.json').read_text());assert journal['state']=='closed'
        # Inspect complete current inventories; a daemon error cannot masquerade
        # as successful cleanup of an individual resource.
        containers=subprocess.run(['docker','ps','-aq','--no-trunc'],capture_output=True,text=True,check=True,timeout=10).stdout.splitlines()
        networks=subprocess.run(['docker','network','ls','-q','--no-trunc'],capture_output=True,text=True,check=True,timeout=10).stdout.splitlines()
        assert gateway['containerId'] not in containers and gateway['networkId'] not in networks
        results.append({'launchId':launch,'intentionalFailure':fail,'journalState':journal['state'],
                        'resourcesAbsent':True,**({'probe':probe} if not fail else {})})
    evidence={'results':results,'modelRequests':0,'productionChanged':False}
    (source/'gateway-evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
    print(json.dumps(evidence))


if __name__=='__main__':main()
