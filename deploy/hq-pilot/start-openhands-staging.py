"""Start a separate authenticated HQ candidate on VPS loopback, no agent execution.

Uses existing HQ owner/Supabase configuration only. No provider credentials,
Memex handles, operational mounts, public listener or background-job keys.
This is a candidate using the existing database, NOT a disposable database.
Do not submit mutations when performing a read-only browser qualification.
"""
import argparse
import json
import os
import re
import subprocess
from pathlib import Path

NAME='oria-hq-openhands-staging'
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image',required=True)
    parser.add_argument('--tool-review-candidate',action='store_true',help='Separate candidate on loopback 3334; tool-review execution stays disabled')
    parser.add_argument('--recovery-candidate',action='store_true',help='Read-only report candidate on loopback 3335')
    args=parser.parse_args()
    if args.tool_review_candidate and args.recovery_candidate:parser.error('Choose one candidate')
    name='oria-hq-tool-review-staging' if args.tool_review_candidate else NAME
    port=3334 if args.tool_review_candidate else 3332
    if args.recovery_candidate:name='oria-hq-recovery-staging';port=3335
    if not re.fullmatch(r'sha256:[a-f0-9]{64}',args.image): parser.error('Immutable image ID required')
    old=subprocess.run(['docker','inspect',name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    if old.returncode==0: raise RuntimeError('Existing candidate requires inspection; refusing replacement')
    inspected=json.loads(subprocess.check_output(['docker','inspect','oria-hq-pilot-hq-1'],text=True))[0]
    original=dict(entry.split('=',1) for entry in inspected['Config']['Env'] if '=' in entry)
    allowed=('NEXT_PUBLIC_SUPABASE_URL','NEXT_PUBLIC_SUPABASE_ANON_KEY','SUPABASE_SERVICE_ROLE_KEY',
             'MICHAEL_HQ_OWNER_ID','MICHAEL_HQ_OWNER_EMAIL')
    env=os.environ.copy()
    command=['docker','create','--name',name,'--label','oria.purpose=hq-openhands-staging',
        '--network','oria-hq-egress','--publish',f'127.0.0.1:{port}:3000','--read-only',
        '--cap-drop','ALL','--security-opt','no-new-privileges:true','--cpus','1.5',
        '--memory','1536m','--memory-swap','1536m','--pids-limit','128',
        '--tmpfs','/tmp:rw,nosuid,nodev,size=128m,mode=1777',
        '--log-opt','max-size=10m','--log-opt','max-file=2']
    if args.recovery_candidate:
        reports=Path('/opt/oria-openhands-qualification/recovery-reports')
        reports.mkdir(mode=0o755,exist_ok=True)
        if reports.resolve()!=reports or any(p.stat().st_uid!=0 or p.stat().st_mode&0o022 for p in (reports,*reports.parents)):
            raise RuntimeError('Protected reports directory required')
        command+=['--mount',f'type=bind,src={reports},dst=/run/oria-hq-reports,readonly']
    for key in allowed:
        if not original.get(key): raise RuntimeError('Existing owner/persistence configuration incomplete')
        env[key]=original[key];command+=['--env',key]
    settings={'ORIA_ENABLE_OPENHANDS_CONFIRMATION':'1','ORIA_HQ_PUBLIC_ORIGIN':f'http://localhost:{port}',
        'ORIA_ENABLE_OPENHANDS_TOOL_REVIEW':'0',
        'MISSION_DURABLE_DRAFTS':'false','ORIA_ALLOW_DEV_USER_FALLBACK':'false',
        'ORIA_UNSAFE_ALLOW_FILE_DOCUMENT_STORE_IN_PROD':'false'}
    for key,value in settings.items():command+=['--env',key+'='+value]
    command.append(args.image)
    container=subprocess.check_output(command,env=env,text=True).strip()
    subprocess.run(['docker','start',container],check=True,stdout=subprocess.DEVNULL)
    print(json.dumps({'container':container,'loopbackPort':port,'agentExecutionEnabled':False,
        'providerCredentialsCopied':False,'database':'existing HQ; qualification must remain read-only'}))

if __name__=='__main__':main()
