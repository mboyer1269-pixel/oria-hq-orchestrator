"""Real SDK entry-point qualification, synthetic ACP peer, no model or credentials."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from budget_agent import BudgetPermissionAgent
from dossier import digest
from run_mission import execute

with tempfile.TemporaryDirectory() as directory:
    root=Path(directory);repo=root/'repo';repo.mkdir();results=root/'results';results.mkdir()
    def git(*args):
        return subprocess.check_output(['git','-C',str(repo),*args],text=True,stderr=subprocess.DEVNULL).strip()
    git('init');git('-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','--allow-empty','-m','fixture')
    data=json.loads((Path(__file__).parent/'fixtures/hq-memory-dossier.json').read_text())
    data['source']['commitSha']=git('rev-parse','HEAD')
    data['payloadHash']=digest({k:v for k,v in data.items() if k not in ('payloadHash','idempotencyKey')})
    def synthetic_agent(**options):
        options['acp_command']=[sys.executable,'/extension/budget_peer.py']
        return BudgetPermissionAgent(**options)
    result=execute(data,workspace_id=data['mission']['workspaceId'],checkout=repo,results=results,agent_factory=synthetic_agent)
    if result['state']!='agent_returned' or result['independentValidationPassed']:
        raise RuntimeError('Unexpected execution classification')
    if not list((results/'conversation').rglob('*')):
        raise RuntimeError('Conversation persistence missing')
    try:execute(data,workspace_id=data['mission']['workspaceId'],checkout=repo,results=results,agent_factory=synthetic_agent)
    except FileExistsError:pass
    else:raise RuntimeError('Repeated entry accepted')
    print(json.dumps({**result,'actualSdk':True,'syntheticAcpPeer':True,'modelCalls':0,'repeatDenied':True,'conversationPersisted':True}))
