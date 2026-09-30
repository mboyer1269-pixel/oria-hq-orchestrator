"""Operator reconciliation of one interrupted HQ launch. Never relaunches.

Reads canonical authority and the observed Docker state, then applies at most
one explicit transition bound to that observation: record a container it can
prove was created, record a result the container already produced, or close a
launch that can no longer produce one. Uncertainty returns a reason and the
next action instead of an invented success. No job file is ever deleted.
"""
import argparse
from contextlib import ExitStack
from datetime import datetime,timezone
import json
from pathlib import Path
import re
import sys
from hq_transition import lifecycle_reader,lifecycle_transition
from launch_lease import LaunchBusy,hold_launch,lease_path
from provider_gateway import TERMINAL_LAUNCH_STATES,release_gateway
from recovery_report import recovery_report,publish_report
from run_host_job import load_configuration,protected_path
from supervisor import docker

FINAL=TERMINAL_LAUNCH_STATES
ACTIVE=('running','paused','restarting','removing')
STAGES=('creation_requested','container_created','start_requested','running')
# Cleanup is only ever allowed on an observation that proves the agent cannot act.
RELEASABLE=('absent','created','exited','dead')
DOCKER_STATES=('created','running','paused','restarting','removing','exited','dead')


def observe_mission(*,launch_id,image_digest):
    """Only a container whose name, labels, launch and image all match counts."""
    name='hq-openhands-'+launch_id
    ids=docker('ps','-a','--no-trunc','--filter','name=^/'+name+'$','--format','{{.ID}}').stdout.split()
    if not ids:return {'state':'absent','containerName':name}
    if len(ids)!=1 or not re.fullmatch(r'[a-f0-9]{64}',ids[0]):
        return {'state':'identity_mismatch','containerName':name,'observedCount':len(ids)}
    observed=json.loads(docker('inspect','--format',
        '[{{json .Id}},{{json .Name}},{{json .Image}},{{json .Config.Labels}},{{json .State.Status}},'
        '{{json .State.ExitCode}},{{json .State.StartedAt}},{{json .State.FinishedAt}}]',ids[0]).stdout)
    identity,observed_name,image,labels,status,exit_code,started_at,finished_at=observed
    labels=labels or {}
    if (identity!=ids[0] or observed_name!='/'+name or image!=image_digest
            or labels.get('oria.purpose')!='openhands-supervised-job'
            or labels.get('oria.launch-id')!=launch_id):
        return {'state':'identity_mismatch','containerName':name,'containerId':ids[0]}
    return {'state':status if status in DOCKER_STATES else 'unknown','containerName':name,
            'containerId':ids[0],'exitCode':exit_code,'startedAt':started_at,'finishedAt':finished_at}


def retained_evidence(job_root,claim):
    """Refuse evidence belonging to another launch, project or commit."""
    path=Path(job_root)/'results'/'started.json'
    if not path.is_file():return {'started':'absent'}
    try:raw=json.loads(path.read_text(encoding='utf-8'))
    except (ValueError,OSError,UnicodeDecodeError):return {'started':'unreadable'}
    if not isinstance(raw,dict):return {'started':'unreadable'}
    if raw.get('payloadHash')!=claim.get('payloadHash') or raw.get('commitSha')!=claim.get('commitSha'):
        return {'started':'foreign'}
    return {'started':'bound','outcome':'present' if (Path(job_root)/'results'/'outcome.json').is_file() else 'absent'}


def deadline_exceeded(claim,mission,timeout_seconds):
    """Observed only; never guessed, so a missing timestamp blocks recording."""
    started=claim.get('startRequestedAt');finished=mission.get('finishedAt')
    if not isinstance(started,str) or not isinstance(finished,str):return None
    if type(timeout_seconds) is not int or not 1<=timeout_seconds<=1800:return None
    try:
        begin=datetime.fromisoformat(started.replace('Z','+00:00'))
        end=datetime.fromisoformat(finished.replace('Z','+00:00'))
    except ValueError:return None
    if end<begin:return None
    return (end-begin).total_seconds()>timeout_seconds


def identity_binding(claim,mission):
    """Bind the observation to the canonical container, not merely to the name.

    A replacement container carrying the same name, labels and image is a
    different container: its state can never justify closing this launch.
    """
    canonical=claim.get('containerId');observed=mission.get('containerId')
    if mission['state']=='absent':return 'absent' if canonical else 'unbound'
    if observed is None or mission['state']=='identity_mismatch':return 'mismatch'
    if canonical is None:return 'uncanonical'
    return 'bound' if observed==canonical else 'mismatch'


def decide(*,claim,mission,evidence,timeout_seconds):
    """Pure decision bound to the observation. Nothing here starts anything."""
    binding=identity_binding(claim,mission)
    def uncertain(reason,action):
        return {'action':'none','state':'reconciliation_uncertain','reason':reason,
                'nextAction':action,'identity':binding}
    state=claim.get('state')
    # The binding is reported even for a terminal claim: cleanup depends on it.
    if state in FINAL:return {'action':'none','state':'already_final','canonicalState':state,'identity':binding}
    if state=='claimed':return {'action':'none','state':'nothing_to_reconcile','canonicalState':state,'identity':binding}
    if state not in STAGES:
        return uncertain('unexpected_canonical_state','Inspect the canonical claim by hand; this host does not interpret its state.')
    if binding=='mismatch':
        return uncertain('container_identity_mismatch','A container named for this launch is not the one the claim records; preserve both and inspect by hand before closing.')
    # Only `creation_requested` legitimately has no recorded identity yet; past
    # that stage a container the claim never bound is not this launch's container.
    if binding=='uncanonical' and state!='creation_requested':
        return uncertain('container_without_canonical_identity','A container exists for a launch past creation whose claim records no identity; inspect it by hand.')
    if mission['state']=='identity_mismatch':
        return uncertain('container_identity_mismatch','A container named for this launch does not match its launch, purpose or image; inspect it by hand.')
    if mission['state']=='unknown':
        return uncertain('container_state_unknown','Docker reported a state this host does not interpret; inspect the container by hand.')
    if mission['state'] in ACTIVE:
        return uncertain('container_active','Let the job deadline stop the container, or stop it deliberately, then reconcile again.')
    if evidence.get('started')=='foreign':
        return uncertain('retained_evidence_foreign','Retained results do not match this payload and commit; preserve them and reconcile by hand.')
    if evidence.get('started')=='unreadable':
        return uncertain('retained_evidence_unreadable','Retained results could not be read; preserve them and reconcile by hand.')
    # A dead client does not cancel a request already accepted by dockerd.
    # Absence is not evidence that a pending create/start can no longer act.
    if mission['state']=='absent' and state in ('creation_requested','start_requested','running'):
        return uncertain('docker_effect_unresolved','Preserve this launch; establish that any in-flight Docker request has settled before operator recovery. Do not retry or close from absence alone.')
    if state=='creation_requested':
        if mission['state']=='absent':
            return {'action':'record_cancelled','expected':state,'reason':'interrupted_before_start','containerState':'absent','identity':binding}
        if mission['state']=='created':
            return {'action':'record_container_created','expected':state,'containerId':mission['containerId'],'identity':binding}
        return uncertain('container_ran_without_recorded_creation','A container for this launch is '+mission['state']
                         +' although its creation was never recorded; inspect its output before closing.')
    if state=='container_created':
        if mission['state'] in ('absent','created','dead'):
            return {'action':'record_cancelled','expected':state,'reason':'interrupted_before_start','containerState':mission['state'],'identity':binding}
        return uncertain('container_ran_without_recorded_start','The container exited without a recorded start; inspect its output before closing.')
    if mission['state']=='exited':
        exceeded=deadline_exceeded(claim,mission,timeout_seconds)
        if exceeded is None:
            return uncertain('deadline_unknown','Container or canonical start timestamps are missing; establish them before recording a result.')
        if not isinstance(mission.get('exitCode'),int) or isinstance(mission.get('exitCode'),bool):
            return uncertain('exit_code_unknown','Docker reported no integer exit code; inspect the container before recording a result.')
        return {'action':'record_execution_finished','expected':state,'containerId':mission['containerId'],
                'process':{'exitCode':mission['exitCode'],'containerStopped':True,'deadlineExceeded':exceeded},'identity':binding}
    if mission['state'] in ('absent','dead'):
        return {'action':'record_cancelled','expected':state,'reason':'result_unrecoverable','containerState':mission['state'],'identity':binding}
    return uncertain('container_never_started','Canonical state expects a started container but it is still created; remove it deliberately, then reconcile as unrecoverable.')


APPLIED={'record_container_created':('container_created','container_created_recorded'),
         'record_execution_finished':('execution_finished','result_recovered'),
         'record_cancelled':('cancelled','launch_closed')}


def apply_decision(decision,*,transition,claim,observed_at):
    """One whitelisted canonical transition. An unconfirmed write never retries."""
    if decision['action']=='none':return decision
    next_state,reported=APPLIED[decision['action']]
    data={}
    if decision['action']=='record_container_created':data['containerId']=decision['containerId']
    elif decision['action']=='record_execution_finished':
        data={'containerId':decision['containerId'],'process':decision['process']}
    else:
        data['observed']={'containerState':decision['containerState'],'observedAt':observed_at,
                          'reason':decision['reason']}
        if claim.get('containerId'):data['containerId']=claim['containerId']
    transition(decision['expected'],next_state,data)
    return {**decision,'state':reported}


def busy_report(claim,*,observed_at,gateway_root):
    """An executor still holds this launch: report where it stands, decide nothing."""
    result={'version':1,'launchId':claim['launchId'],'missionId':claim['missionId'],
            'workspaceId':claim['workspaceId'],'runnerId':claim['runnerId'],
            'state':'launch_busy','canonicalState':claim['state'],'canonicalTerminal':False,
            'reason':'launch_held_by_another_host_path','steps':[],'jobFilesRemoved':False,
            'automaticRetry':False,'independentValidationPassed':False,'observedAt':observed_at,
            'nextAction':('A launch path still holds this launch and may still create or start its '
                          'container; wait for it to finish or end that process, then reconcile again.')}
    if gateway_root is not None:
        result['gatewayRelease']={'attempted':False,'reason':'launch_held_by_another_host_path'}
    return result


def reconcile(*,command,job_root,lease_file,gateway_root=None,steps=2,now=None,
              observe=observe_mission,expect_launch_id=None,lease=hold_launch):
    """At most `steps` transitions, each rebound to a fresh canonical read.

    Every read, decision, transition and removal happens while this launch is
    held, so an executor that can still create or start its container makes the
    whole reconciliation refuse instead of recording a closure behind its back.
    """
    observed_at=(now or datetime.now(timezone.utc)).replace(microsecond=0).isoformat().replace('+00:00','Z')
    transition=lifecycle_transition(command)
    read=lifecycle_reader(command,include_config=True)
    history=[]
    with ExitStack() as guard:
        try:guard.enter_context(lease(lease_file))
        except LaunchBusy:
            claim=read()['claim']
            if expect_launch_id is not None and claim['launchId']!=expect_launch_id:
                raise ValueError('Operator configuration does not name the canonical launch') from None
            return busy_report(claim,observed_at=observed_at,gateway_root=gateway_root)
        return _reconcile_held(command=command,job_root=job_root,gateway_root=gateway_root,steps=steps,
                               observed_at=observed_at,observe=observe,expect_launch_id=expect_launch_id,
                               transition=transition,read=read,history=history)


def _reconcile_held(*,command,job_root,gateway_root,steps,observed_at,observe,expect_launch_id,
                    transition,read,history):
    for _ in range(max(1,steps)):
        observation=read();claim=observation['claim'];config=observation['config']
        # Bound before any transition or removal: a configuration that names
        # another launch must produce no effect at all.
        if expect_launch_id is not None and claim['launchId']!=expect_launch_id:
            raise ValueError('Operator configuration does not name the canonical launch')
        mission=observe(launch_id=claim['launchId'],image_digest=claim['imageDigest'])
        evidence=retained_evidence(job_root,claim)
        decision=decide(claim=claim,mission=mission,evidence=evidence,timeout_seconds=config['timeoutSeconds'])
        history.append({**apply_decision(decision,transition=transition,claim=claim,observed_at=observed_at),
                        'observedMission':mission,'retainedEvidence':evidence})
        if decision['action']=='none':break
    final=read()['claim']
    # Re-observe after the writes: the canonical CAS orders the records, it does
    # not freeze Docker. A world that changed under us is reported, never hidden.
    after=observe(launch_id=final['launchId'],image_digest=final['imageDigest'])
    binding=identity_binding(final,after)
    recorded=[step for step in history if step['action']!='none']
    result={'version':1,'launchId':final['launchId'],'missionId':final['missionId'],
            'workspaceId':final['workspaceId'],'runnerId':final['runnerId'],
            'canonicalState':final['state'],'canonicalTerminal':final['state'] in FINAL,
            'steps':history,'jobFilesRemoved':False,'automaticRetry':False,
            'independentValidationPassed':False,'observedAt':observed_at,
            'postObservation':{'containerState':after['state'],'identity':binding}}
    if 'reconciliation' in final:result['closure']=final['reconciliation']
    if 'process' in final:result['process']=final['process']
    stale=(recorded and (after['state']!=recorded[-1]['observedMission']['state']
                         or after.get('containerId')!=recorded[-1]['observedMission'].get('containerId')))
    if stale:
        result['postObservation']['changedAfterRecording']=True
        result['canonicalTerminal']=False
        result['reason']='observation_changed_after_recording'
        result['nextAction']=('The container observed for this launch changed while the record was written; '
                              'preserve everything and inspect both the container and the canonical claim by hand.')
    if gateway_root is not None:
        # Release only on an observation that proves the agent cannot act and is
        # the container the claim records. Every uncertainty keeps the resources.
        if not result['canonicalTerminal']:
            result['gatewayRelease']={'attempted':False,'reason':'canonical_state_not_terminal'}
        elif after['state'] not in RELEASABLE:
            result['gatewayRelease']={'attempted':False,'reason':'agent_container_not_releasable',
                                      'observedContainerState':after['state']}
        elif binding=='mismatch':
            result['gatewayRelease']={'attempted':False,'reason':'agent_container_identity_mismatch'}
        else:
            try:result['gatewayRelease']={'attempted':True,**release_gateway(
                root=gateway_root,launch_id=final['launchId'],canonical_state=final['state'])}
            except Exception:result['gatewayRelease']={'attempted':True,'released':False,'reconciliationRequired':True}
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',required=True,help='Root-owned operator configuration of the launch')
    parser.add_argument('--gateway-root',help='Protected host gateway root; release its resources once terminal')
    parser.add_argument('--report-directory',help='Publish the resulting observation JSON in a protected directory')
    args=parser.parse_args()
    try:
        # read_only: an interrupted attempt normally leaves its control socket.
        command,root,review,provider=load_configuration(args.config,read_only=True)
        lease_file=lease_path(control_directory=review.parent,job_root=root)
        gateway_root=None
        if args.gateway_root:
            gateway_root=protected_path(args.gateway_root,directory=True)
            if provider is not None and Path(provider['gatewayRoot'])!=gateway_root:
                raise ValueError('Gateway root is not the authorized one')
        # Every binding check precedes reconcile, so a configuration naming
        # another launch cannot write a transition or remove a resource first.
        if root.name!=review.parent.name:
            raise ValueError('Host directories must name the same launch')
        result=reconcile(command=command,job_root=root,lease_file=lease_file,
                         gateway_root=gateway_root,expect_launch_id=root.name)
        if args.report_directory:
            publish_report(recovery_report(command=command,gateway_root=gateway_root or root),args.report_directory)
        print(json.dumps(result))
        return 0 if result['canonicalTerminal'] else 3
    except (Exception,):
        # Never print trusted command arguments, dossier contents or credentials.
        print(json.dumps({'state':'reconciliation_required','automaticRetry':False}))
        return 2


if __name__=='__main__':sys.exit(main())
