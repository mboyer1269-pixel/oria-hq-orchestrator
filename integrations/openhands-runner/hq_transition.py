"""Local worker bridge to the HQ-owned canonical lifecycle service."""
import json
import subprocess


def lifecycle_reader(command, *, include_config=False, prepare=False):
    """Host command's protected config binds workspace, launch and identity."""
    if not isinstance(command,(list,tuple)) or not command or not all(isinstance(x,str) and x for x in command):
        raise ValueError('Host command required')
    def read():
        result=subprocess.run(command,input=json.dumps({'next':'prepare' if prepare else 'read'}),text=True,
                              capture_output=True,timeout=30,check=False)
        if result.returncode!=0:raise RuntimeError('HQ read not confirmed')
        response=json.loads(result.stdout)
        if response.get('status')!='observed' or not isinstance(response.get('claim'),dict):
            raise RuntimeError('Invalid HQ observation')
        if prepare and not isinstance(response.get('dossier'),dict):raise RuntimeError('Missing canonical dossier')
        if include_config or prepare:
            if not isinstance(response.get('config'),dict):raise RuntimeError('Missing bound configuration')
            return response
        return response['claim']
    return read


def consume_tool_decision(command, request):
    """Trusted host invocation only. Cannot approve; every uncertainty denies."""
    denied={'outcome':{'outcome':'cancelled'}}
    try:
        result=subprocess.run(command,input=json.dumps({'operation':'consume_tool','request':request}),
                              text=True,capture_output=True,timeout=20,check=False)
        if result.returncode!=0:return denied
        response=json.loads(result.stdout)
        if response.get('status')!='permission_response':return denied
        outcome=response.get('outcome',{})
        if outcome.get('outcome')=='cancelled':return denied
        offered={option['optionId'] for option in request['options'] if option['kind'] in ('allow_once','reject_once')}
        if outcome.get('outcome')!='selected' or outcome.get('optionId') not in offered:return denied
        return {'outcome':{'outcome':'selected','optionId':outcome['optionId']}}
    except (ValueError,TypeError,KeyError,AttributeError,subprocess.SubprocessError,OSError):
        return denied


def lifecycle_transition(command):
    """command is a host-selected argv, never supplied by a mission or agent.

    May use a trusted docker exec invocation so Supabase credentials remain in
    the HQ service container. No shell and no automatic retry on unknown writes.
    """
    if not isinstance(command,(list,tuple)) or not command or not all(isinstance(x,str) and x for x in command):
        raise ValueError('Host command required')
    def transition(expected,next_state,data):
        request={'expected':expected,'next':next_state}
        if 'containerId' in data:request['containerId']=data['containerId']
        if 'sessionId' in data:request['sessionId']=data['sessionId']
        if 'process' in data:
            request['process']={key:data['process'][key] for key in ('exitCode','containerStopped','deadlineExceeded')}
        if 'observed' in data:
            request['observed']={key:data['observed'][key] for key in ('containerState','observedAt','reason')}
        result=subprocess.run(command,input=json.dumps(request),text=True,capture_output=True,
                              timeout=30,check=False)
        if result.returncode!=0:
            raise RuntimeError('HQ transition not confirmed; reconcile before retry')
        try:response=json.loads(result.stdout)
        except (ValueError,TypeError):raise RuntimeError('Invalid HQ response') from None
        claim=response.get('claim',{})
        if response.get('status')!='recorded' or claim.get('state')!=next_state:
            raise RuntimeError('HQ transition not confirmed')
        if 'containerId' in request and claim.get('containerId')!=request['containerId']:
            raise RuntimeError('HQ container binding mismatch')
        if 'sessionId' in request and claim.get('sessionId')!=request['sessionId']:
            raise RuntimeError('HQ session binding mismatch')
        return True
    return transition
