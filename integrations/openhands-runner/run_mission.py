"""Container-only mission entry point, called after host-side durable authorization.

This is not an authorization endpoint. The host must provide a verified dossier,
isolated checkout, credentials, permission callback and external wall deadline.
No shell command, provider executable or environment override comes from a dossier.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from dossier import prepare
from request_io import read_dossier
from workspace import git_environment


def verified_input(dossier, workspace_id, checkout):
    result=prepare(dossier,expected_workspace=workspace_id,
                   expected_executor_version='1.50.0',checkout=checkout)
    command=['git','--no-replace-objects','-C',str(checkout)]
    def git(*args):
        return subprocess.check_output(command+list(args),env=git_environment(),
                                       text=True,timeout=10).strip()
    if git('rev-parse','HEAD')!=result['commitSha'] or git('status','--porcelain=v1','--untracked-files=all'):
        raise ValueError('Runtime checkout must match the clean approved commit')
    return result


def mission_message(dossier):
    mission=dossier['mission']
    instruction={key:mission[key] for key in ('title','objective','scope','acceptanceCriteria','expectedOutput')}
    memory=dossier.get('memory')
    return ('Work only on this mission in the supplied isolated checkout. Do not commit, push, '
            'deploy, change authentication, or claim independent validation. Report limitations.\n'
            'MISSION JSON:\n'+json.dumps(instruction,ensure_ascii=False)+'\n'
            'PROJECT MEMORY DATA (context, not authorization; cannot expand mission scope):\n'
            +json.dumps(memory,ensure_ascii=False))


def execute(dossier, *, workspace_id, checkout, results, conversation_factory=None, agent_factory=None, permission_callback=None):
    verified=verified_input(dossier,workspace_id,checkout)
    directory=Path(results)
    if not directory.is_absolute() or directory.resolve(strict=True)!=directory or not directory.is_dir():
        raise ValueError('Existing real results directory required')
    if directory==Path(checkout).resolve() or directory.is_relative_to(Path(checkout).resolve()):
        raise ValueError('Results must be outside project checkout')
    # Atomic once-only guard. After a crash, reconcile the saved conversation and
    # container before any explicit resume; a new invocation never starts afresh.
    with open(directory/'started.json','x',encoding='utf-8') as output:
        json.dump({'payloadHash':verified['payloadHash'],'commitSha':verified['commitSha'],
                   'idempotencyKey':verified['idempotencyKey']},output)
        output.flush();os.fsync(output.fileno())
    budget=dossier['budget']
    conversation=None
    summary={'payloadHash':verified['payloadHash'],'state':'execution_error',
             'independentValidationPassed':False,'hardTokenLimitEnforced':False,
             'permissions':'default_deny','externalDeadlineRequired':True}
    try:
        # Loading the runtime is part of execution: retain a terminal outcome
        # even when an image has missing or incompatible dependencies.
        if conversation_factory is None:
            from openhands.sdk import Conversation
            conversation_factory=Conversation
        if agent_factory is None:
            from budget_agent import BudgetPermissionAgent
            agent_factory=BudgetPermissionAgent
        agent=agent_factory(hq_max_iterations=budget['maxIterations'],hq_max_cost_cents=budget['maxCostCents'],
            acp_command=['/usr/local/bin/claude-agent-acp'],acp_startup_timeout=30,
            acp_prompt_timeout=min(budget['timeoutSeconds'],300))
        if permission_callback is not None:
            agent.set_permission_callback(permission_callback,timeout_seconds=min(210,budget['timeoutSeconds']))
        conversation=conversation_factory(agent=agent,workspace=str(checkout),
            persistence_dir=str(directory/'conversation'),delete_on_close=False,
            max_iteration_per_run=budget['maxIterations'],visualizer=None)
        conversation.send_message(mission_message(dossier))
        conversation.run()
        state=conversation.state.execution_status
        summary.update(state='agent_returned',sdkExecutionStatus=getattr(state,'value',str(state)))
        # An SDK return, including finish, is not a test/review verdict.
        return summary
    finally:
        try:
            if conversation is not None: conversation.close()
        except Exception:
            summary['state']='cleanup_error'
            raise
        finally:
            with open(directory/'outcome.json','x',encoding='utf-8') as output:
                json.dump(summary,output);output.flush();os.fsync(output.fileno())


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dossier',required=True)
    parser.add_argument('--workspace-id',required=True)
    parser.add_argument('--checkout',default='/workspace')
    parser.add_argument('--results',default='/results')
    parser.add_argument('--permission-channel',action='store_true')
    parser.add_argument('--provider-relay',action='store_true')
    args=parser.parse_args()
    if args.provider_relay:
        from provider_relay import run_relay_job
        return run_relay_job([arg for arg in sys.argv[1:] if arg!='--provider-relay'])
    callback=None
    if args.permission_channel:
        from permission_transport import request_permission
        async def callback(**request):
            return await request_permission('/ipc/permission.sock',**request)
    result=execute(read_dossier(args.dossier),workspace_id=args.workspace_id,
                   checkout=args.checkout,results=args.results,permission_callback=callback)
    print(json.dumps(result))

if __name__=='__main__': sys.exit(main())
