"""Disposable actual HQ stores + PostgreSQL/PostgREST; no published ports or production DB."""
import json
import hashlib
import argparse
from pathlib import Path
import subprocess
import re
import sys
import time
import uuid
import tempfile
import os
import asyncio
import socket
import shutil
from contextlib import suppress
from concurrent.futures import ThreadPoolExecutor
from supervisor import supervise
from permission_worker import run_permission_job
from prepare_host_job import prepare_host_job
from dispatch import dispatch
from hq_transition import lifecycle_transition, lifecycle_reader
from provider_policy import EXPECTED
from recovery_report import recovery_report,publish_report

PG = "sha256:b0f9560a2de083e2cc7382e75f808c7381a32852a7ec49117deedb300e552b24"
REST = "postgrest/postgrest@sha256:c53043d2c9bdb29c28e7e6d02175320af11495cdea5439f44009c06efe6625fa"
# Harness-only: run from a disposable qualification root instead of installing
# these sources into the active one. Not part of the host release file set.
ROOT = Path(os.environ.get('QUALIFICATION_ROOT') or '/opt/oria-openhands-qualification')


class ScenarioComplete(Exception):
    """Harness-only control flow after a resilience scenario finishes its checks."""


def docker(*args, input=None, check=True):
    return subprocess.run(['docker', *args], input=input, text=True, capture_output=True, check=check, timeout=90)

def named_ids(name):
    """Deterministic-name observation: which containers exist for this launch."""
    return docker('ps','-a','--no-trunc','--filter','name=^/'+name+'$','--format','{{.ID}}',check=False).stdout.split()

def launch_identities(mission_name,proxy_name):
    """Exact identities, not counts: a replaced container must remain visible."""
    return {'mission':named_ids(mission_name),'gateway':named_ids(proxy_name)}

def verify_no_second_effect(*,label,before,after,exit_code,expected_exit,reported_jobs,stderr=''):
    """Refuse a failed re-invocation, a replaced identity, an extra container or new work."""
    problems=[]
    if exit_code!=expected_exit:problems.append('exit '+repr(exit_code)+' instead of '+repr(expected_exit))
    if reported_jobs:problems.append('consumer reported '+repr(reported_jobs)+' job(s)')
    for key in ('mission','gateway'):
        if before[key]!=after[key]:problems.append(key+' identity changed')
        elif len(after[key])>1:problems.append(key+' has '+str(len(after[key]))+' containers')
    if problems:
        # Keep the diagnostic tail: this disposable fixture holds no credentials.
        tail=chr(10).join((stderr or '').splitlines()[-5:])
        raise AssertionError(label+': '+'; '.join(problems)+((chr(10)+'stderr tail:'+chr(10)+tail) if tail else ''))
    return {'missionContainerIds':before['mission'],'gatewayContainerIds':before['gateway'],
            'identitiesUnchanged':True,'reinvocationExit':exit_code,'consumerReportedJobs':reported_jobs}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live-memex',action='store_true')
    parser.add_argument('--lifecycle',action='store_true')
    parser.add_argument('--provider-binding',action='store_true',help='Qualify synthetic policy identity persistence without provider execution')
    parser.add_argument('--synthetic-provider',action='store_true',help='Actual worker/gateway/storage with synthetic ACP, no provider account')
    parser.add_argument('--operator-provider',action='store_true',help='Provider path through the actual consumer, preparation and operator entry')
    parser.add_argument('--interrupted-start',action='store_true',help='Harness-only fault: kill the operator as soon as the container exists')
    parser.add_argument('--lost-completed-response',action='store_true',help='Harness-only fault: discard the response of a completed execution')
    parser.add_argument('--interrupted-run',action='store_true',help='Harness-only fault: kill the operator while the container runs')
    parser.add_argument('--replaced-container',action='store_true',help='Harness-only fault: substitute the container before reconciling')
    parser.add_argument('--reconcile',action='store_true',help='Continue into the real operator reconciliation of the faulted launch')
    parser.add_argument('--recovery-report',action='store_true',help='Publish host report for the actual HQ reader in a read-only mount')
    parser.add_argument('--docker-job',action='store_true')
    parser.add_argument('--valid-dossier',action='store_true')
    parser.add_argument('--permission-worker',action='store_true')
    parser.add_argument('--probe-permission',action='store_true')
    parser.add_argument('--review-service',action='store_true')
    parser.add_argument('--review-control',action='store_true')
    parser.add_argument('--review-host',action='store_true')
    parser.add_argument('--host-entry',action='store_true')
    parser.add_argument('--prepare-host',action='store_true')
    parser.add_argument('--project-source',action='store_true')
    parser.add_argument('--host-consumer',action='store_true')
    parser.add_argument('--consumer-service',action='store_true')
    parser.add_argument('--hq-image',help='Pinned coherent HQ source image; disables individual source overlays')
    args=parser.parse_args()
    if args.recovery_report and not (args.synthetic_provider and args.hq_image):parser.error('--recovery-report requires synthetic provider and coherent HQ image')
    if sum((args.interrupted_start,args.interrupted_run,args.lost_completed_response))>1:parser.error('Run one resilience scenario per invocation')
    if args.replaced_container:args.interrupted_run=True;args.reconcile=True
    if args.interrupted_run and not args.reconcile:parser.error('--interrupted-run exists to qualify recovery; add --reconcile')
    if args.reconcile and not (args.interrupted_start or args.interrupted_run or args.lost_completed_response):parser.error('--reconcile follows a resilience scenario')
    if args.interrupted_start or args.interrupted_run or args.lost_completed_response:args.operator_provider=True
    if args.operator_provider:args.synthetic_provider=True;args.host_consumer=True
    if args.synthetic_provider:
        forbidden=[args.provider_binding,args.consumer_service,args.probe_permission,args.review_service,args.review_control,args.review_host]
        if not args.operator_provider:forbidden+=[args.host_entry,args.host_consumer,args.prepare_host,args.project_source]
        if any(forbidden):parser.error('Synthetic provider mode cannot be combined with these operator modes')
        args.permission_worker=True
    if args.provider_binding:
        if any((args.docker_job,args.permission_worker,args.host_entry,args.host_consumer,args.consumer_service,args.prepare_host,args.project_source,args.probe_permission,args.review_service,args.review_control,args.review_host)):
            parser.error('--provider-binding is a storage qualification, not a provider execution mode')
        args.lifecycle=True
    if args.hq_image and not re.fullmatch(r'sha256:[a-f0-9]{64}',args.hq_image):parser.error('Pinned HQ image required')
    if args.consumer_service:args.host_consumer=True
    if args.host_consumer:args.project_source=True
    if args.project_source:args.prepare_host=True;args.live_memex=True
    if args.prepare_host:args.host_entry=True
    if args.host_entry:
        if args.probe_permission or args.review_host or args.review_control or args.review_service:
            parser.error('--host-entry qualifies the operator entry separately from permission probes')
        args.permission_worker=True
    if args.review_host:args.review_control=True
    if args.review_control:args.review_service=True
    if args.review_service:
        if args.docker_job or args.valid_dossier or args.permission_worker or args.probe_permission:
            parser.error('--review-service currently uses a synthetic runtime identity; do not combine with Docker execution')
        args.lifecycle=True
    if args.probe_permission:args.permission_worker=True
    if args.permission_worker:args.valid_dossier=True
    if args.valid_dossier:args.docker_job=True
    if args.docker_job: args.lifecycle=True
    source=tempfile.TemporaryDirectory(prefix='hq-dispatch-source-',dir='/root' if args.prepare_host else None)
    def git(*argv):return subprocess.check_output(['git','-C',source.name,*argv],text=True,stderr=subprocess.DEVNULL).strip()
    git('init');git('-c','user.name=Qualification','-c','user.email=qualification@example.invalid','commit','--allow-empty','-m','fixture')
    source_commit=git('rev-parse','HEAD')
    ids=[]
    control_processes=[]
    control_directories=[]
    reports=None
    if args.recovery_report:
        reports=tempfile.TemporaryDirectory(prefix='hq-reports-',dir='/root')
        control_directories.append(reports);os.chmod(reports.name,0o755)
    provider_profile=None
    policy_root=None
    gateways=None
    authorization=None
    networks=[]
    expected_container=[None]
    closure_expected=[None]
    if args.synthetic_provider:
        policy_temp=tempfile.TemporaryDirectory(prefix='hq-provider-policies-',dir='/root')
        control_directories.append(policy_temp);policy_root=Path(policy_temp.name)
        folder=policy_root/'synthetic-relay';folder.mkdir()
        original=ROOT/'provider-policy-check/qualified/claude-subscription-v1'
        policy=json.loads((original/'policy.json').read_text())
        policy['runtimeImage']='sha256:ecfafc87bc148d922dd4d43c3c5d3bb80f4a0828e4ff9af22ef80b7bd5c2924d'
        for filename in policy['files']:(folder/filename).write_bytes((original/filename).read_bytes())
        raw=json.dumps(policy,sort_keys=True,separators=(',',':')).encode()
        (folder/'policy.json').write_bytes(raw)
        provider_profile={**EXPECTED,'id':'synthetic-relay','policySha256':hashlib.sha256(raw).hexdigest()}
        gateways=ROOT/'gateways'
        if args.operator_provider:
            # Protected disposable gateway root named by the authorization that the
            # operator configuration carries. No exemption from host validation.
            gateway_temp=tempfile.TemporaryDirectory(prefix='hq-gateways-',dir='/root')
            control_directories.append(gateway_temp);gateways=Path(gateway_temp.name);gateways.chmod(0o700)
            authorization={'profileId':provider_profile['id'],'policySha256':provider_profile['policySha256'],
                           'policyRoot':str(policy_root),'gatewayRoot':str(gateways)}
    volume='oria-postgrest-qualification-'+uuid.uuid4().hex
    docker('volume','create','--label','oria.purpose=postgrest-qualification',volume)
    try:
        pg=docker('create','--label','oria.purpose=hq-postgrest-qualification','--network','none','--read-only','--user','postgres','--cap-drop','ALL',
            '--security-opt','no-new-privileges','--memory','256m','--cpus','0.5','--pids-limit','128',
            '--mount',f'type=volume,src={volume},dst=/var/lib/postgresql/data',
            '--tmpfs','/tmp:rw,nosuid,nodev,size=16m,mode=1777',
            '--tmpfs','/var/run/postgresql:rw,nosuid,nodev,size=8m,mode=1777',
            '-e','POSTGRES_HOST_AUTH_METHOD=trust','-e','PGDATA=/var/lib/postgresql/data/pgdata',PG).stdout.strip()
        ids.append(pg);docker('start',pg)
        def ready():
            deadline=time.monotonic()+20
            while docker('exec',pg,'pg_isready','-h','127.0.0.1','-U','postgres',check=False).returncode:
                if time.monotonic()>deadline: raise RuntimeError('Postgres readiness failed')
                time.sleep(.25)
        ready()
        schema=(ROOT/'hq-postgrest/db/schema.sql').read_text()
        start=schema.index('create table if not exists public.action_ledger (')
        ledger=schema[start:schema.index('\n);',start)+3]
        sql="CREATE SCHEMA auth; CREATE TABLE auth.users(id uuid PRIMARY KEY); INSERT INTO auth.users VALUES('11111111-1111-4111-8111-111111111111');\n"+ledger
        for name in ['0001_missions.sql','0002_typed_ledger_events.sql','0020_action_ledger_workspace_scope.sql']:
            sql+='\n'+(ROOT/'hq-postgrest/db/migrations'/name).read_text()
        sql+='\nCREATE ROLE qualification_service NOLOGIN BYPASSRLS; GRANT USAGE ON SCHEMA public TO qualification_service; GRANT ALL ON ALL TABLES IN SCHEMA public TO qualification_service;'
        docker('exec','-i',pg,'psql','-h','127.0.0.1','-U','postgres','-X','-q','-v','ON_ERROR_STOP=1',input=sql)
        rest=docker('create','--label','oria.purpose=hq-postgrest-qualification','--network','container:'+pg,'--read-only','--cap-drop','ALL','--security-opt','no-new-privileges',
            '--memory','128m','--cpus','0.5','-e','PGRST_DB_URI=postgres://postgres@127.0.0.1/postgres',
            '-e','PGRST_DB_ANON_ROLE=qualification_service','-e','PGRST_DB_SCHEMAS=public',REST).stdout.strip()
        ids.append(rest);docker('start',rest)
        if args.live_memex:
            memex=docker('create','--label','oria.purpose=hq-postgrest-qualification',
                '--network','container:'+pg,'--read-only','--user','0:0','--cap-drop','ALL',
                '--security-opt','no-new-privileges','--memory','256m','--cpus','0.5','--pids-limit','128',
                '--tmpfs','/tmp:rw,nosuid,nodev,size=32m,mode=1777',
                '--mount',f'type=bind,src={ROOT}/openhands-runner,dst=/qualification,readonly',
                '--entrypoint','node','sha256:04c47d5b4572fed80ea1a04a93bf6a525f8dcfa2567897e80bc0eae108ffd367',
                '--experimental-strip-types','/qualification/qualify_memex_service.mjs').stdout.strip()
            ids.append(memex);docker('start',memex)
        def phase(name):
            overlays=[]
            if reports:overlays+=['--mount',f'type=bind,src={reports.name},dst=/run/oria-hq-reports,readonly']
            if args.host_consumer:
                host_config=tempfile.TemporaryDirectory(prefix='hq-consumer-config-',dir='/root')
                control_directories.append(host_config)
                overlays+=['--mount',f'type=bind,src={host_config.name},dst=/hq-host-config,readonly']
            if args.lifecycle and not args.hq_image:
                overlays+=['--mount',f'type=bind,src={ROOT}/lifecycle/openhands-launch-contract.ts,dst=/workspace/hq/src/core/openhands-launch-contract.ts,readonly']
                for file in ('openhands-launch.ts','openhands-lifecycle.ts','openhands-pending-launches.ts','openhands-tool-permission.ts','openhands-tool-decision-store.ts','openhands-tool-admission.ts','openhands-tool-service.ts','openhands-tool-review.ts','openhands-control-client.ts','openhands-tool-inbox.ts'):
                    overlays+=['--mount',f'type=bind,src={ROOT}/lifecycle/{file},dst=/workspace/hq/src/server/missions/{file},readonly']
                overlays+=['--mount',f'type=bind,src={ROOT}/lifecycle/openhands-lifecycle.mjs,dst=/workspace/hq/src/scripts/openhands-lifecycle.mjs,readonly']
                overlays+=['--mount',f'type=bind,src={ROOT}/lifecycle/openhands-pending-launches.mjs,dst=/workspace/hq/src/scripts/openhands-pending-launches.mjs,readonly']
            control=tempfile.TemporaryDirectory(prefix='hq-review-control-')
            control_directories.append(control)
            node_sources=ROOT/'openhands-runner'
            if args.review_control or args.recovery_report:
                fixtures=tempfile.TemporaryDirectory(prefix='hq-review-sources-')
                control_directories.append(fixtures)
                node_sources=Path(fixtures.name);node_sources.chmod(0o755)
                (node_sources/'fixtures').mkdir(mode=0o755)
                for relative in ('qualify_hq_postgrest.mjs','fixtures/hq-memory-dossier.json'):
                    target=node_sources/relative
                    target.write_bytes((ROOT/'openhands-runner'/relative).read_bytes());target.chmod(0o444)
            control_host=None
            node_name='hq-review-node-'+uuid.uuid4().hex
            if args.review_control and name=='seed':
                os.chmod(control.name,0o755)
                os.chown(control.name,1000,1000)
                overlays+=['--mount',f'type=bind,src={control.name},dst=/run/oria-hq-control']
                control_host=subprocess.Popen(['python3',str(ROOT/'openhands-runner/qualify_review_control_host.py'),control.name,node_name])
                control_processes.append(control_host)
            node=docker('create','--name',node_name,'--label','oria.purpose=hq-postgrest-qualification','--user','1000:1000' if args.review_control or (args.recovery_report and name=='verify') else '0:0','--network','container:'+pg,'--read-only','--cap-drop','ALL','--security-opt','no-new-privileges',
                '--memory','512m','--cpus','1','--tmpfs','/tmp:rw,nosuid,nodev,size=64m,mode=1777',
                '--tmpfs','/run/hq-discovery:rw,nosuid,nodev,size=1m,mode=700',
                '-e','QUALIFICATION_LIVE_MEMEX='+('1' if args.live_memex else '0'),
                '-e','QUALIFICATION_LIFECYCLE='+('1' if args.lifecycle else '0'),*overlays,
                '-e','QUALIFICATION_PROVIDER_BINDING='+('1' if args.provider_binding else '0'),
                '-e','QUALIFICATION_RECOVERY_REPORT='+('1' if args.recovery_report else '0'),
                '-e','QUALIFICATION_SYNTHETIC_PROVIDER='+('1' if args.synthetic_provider else '0'),
                '-e','QUALIFICATION_INTERRUPTED_START='+('1' if args.interrupted_start else '0'),
                '-e','QUALIFICATION_CLOSURE_REASON='+(closure_expected[0] or ''),
                '-e','QUALIFICATION_EXPECTED_CONTAINER='+(expected_container[0] or ''),
                '-e','QUALIFICATION_PROVIDER_PROFILE='+json.dumps(provider_profile),
                '-e','QUALIFICATION_REVIEW_SERVICE='+('1' if args.review_service else '0'),
                '-e','QUALIFICATION_REVIEW_CONTROL='+('1' if args.review_control else '0'),
                '-e','QUALIFICATION_REVIEW_HOST='+('1' if args.review_host else '0'),
                '-e','QUALIFICATION_DOCKER_JOB='+('1' if args.docker_job else '0'),
                '-e','QUALIFICATION_VALID_DOSSIER='+('1' if args.valid_dossier else '0'),
                '-e','QUALIFICATION_PERMISSION_WORKER='+('1' if args.permission_worker else '0'),
                '-e','QUALIFICATION_COMMIT='+source_commit,
                '--mount',f'type=bind,src={node_sources},dst=/qualification,readonly',
                '--entrypoint','node',args.hq_image or 'sha256:32f6f90cc1ab149069e4436e0ea025cb07f8730be6b1581677dcb76e7a16be85','/qualification/qualify_hq_postgrest.mjs',name).stdout.strip()
            ids.append(node)
            if args.docker_job and name=='seed':
                docker('start',node)
                for attempt in range(120):
                    ready_job=docker('exec',node,'cat','/tmp/host-ready.json',check=False)
                    if ready_job.returncode==0:break
                    time.sleep(.25)
                else:raise RuntimeError('Host job not ready')
                job=json.loads(ready_job.stdout)
                command=['docker','exec','--user','0:0','-i','-e','NEXT_PUBLIC_SUPABASE_URL='+job['url'],
                         '-e','SUPABASE_SERVICE_ROLE_KEY=synthetic-local-qualification','-e','NODE_ENV=test',
                         node,'node','/workspace/hq/src/scripts/openhands-lifecycle.mjs','/tmp/lifecycle-job.json']
                with suppress(ScenarioComplete),tempfile.TemporaryDirectory(prefix='hq-real-dispatch-',dir='/root' if args.host_entry else None) as temporary:
                    base=Path(temporary);base.chmod(0o755)
                    root=base/job['launchId'] if args.host_entry else base
                    if args.prepare_host:
                        jobs=base/'jobs';jobs.mkdir(mode=0o755)
                        controls=base/'control';controls.mkdir(mode=0o755)
                        command[0]=str(Path(shutil.which('docker')).resolve(strict=True))
                        if args.project_source:
                            registry=base/'project-sources.json'
                            registry.write_text(json.dumps({'version':1,'entries':[{'workspaceId':job['workspaceId'],
                                'projectId':job['dossier']['memory']['projectId'],'runnerId':job['config']['runnerId'],'sourceRoot':source.name}]}))
                            registry.chmod(0o600)
                            preparation=base/'preparation.json'
                            preparation_config=dict(lifecycleCommand=command,registryFile=str(registry),jobsRoot=str(jobs),controlRoot=str(controls))
                            if authorization:preparation_config['providerExecution']=authorization
                            preparation.write_text(json.dumps(preparation_config))
                            preparation.chmod(0o600)
                            if args.host_consumer:
                                profile=Path(host_config.name)/'profile.json'
                                profile.write_text(json.dumps(dict(context=job['context'],config=job['config'])));profile.chmod(0o600)
                                consumer=base/'consumer.json'
                                consumer_config=dict(bridgeCommand=command[:-2],bridgeScriptsRoot='/workspace/hq/src/scripts',
                                    bridgeConfigRoot='/hq-host-config',hostConfigRoot=host_config.name,profileFile=str(profile),
                                    registryFile=str(registry),jobsRoot=str(jobs),controlRoot=str(controls))
                                if authorization:consumer_config['providerExecution']=authorization
                                consumer.write_text(json.dumps(consumer_config));consumer.chmod(0o600)
                                mission_name='hq-openhands-'+job['launchId']
                                proxy_name='hq-provider-'+job['launchId']
                                consume_argv=[sys.executable,str(Path(__file__).with_name('consume_pending.py')),'--config',str(consumer)]
                                def observe(extra=None):
                                    seen={'missionContainers':len(named_ids(mission_name)),
                                          'gatewayContainers':len(named_ids(proxy_name)),
                                          'canonicalState':lifecycle_reader(command)()['state'],
                                          'jobDirectory':(jobs/job['launchId']).exists(),
                                          'perLaunchBridgeConfig':(Path(host_config.name)/job['launchId']).exists(),
                                          'gatewayDirectory':bool(gateways) and (gateways/job['launchId']).exists()}
                                    return {**seen,**(extra or {})}
                                def reconcile_now(label,*,expect_terminal):
                                    """Run the real operator reconciliation command, nothing simulated."""
                                    argv=['python3',str(ROOT/'openhands-runner/reconcile_launch.py'),
                                          '--config',str(jobs/job['launchId']/'operator.json'),
                                          '--gateway-root',str(gateways)]
                                    run=subprocess.run(argv,capture_output=True,text=True,timeout=120)
                                    report=json.loads(run.stdout)
                                    stopped=False
                                    if report.get('steps',[{}])[0].get('reason')=='container_active':
                                        # Explicit operator action, printed as such; never automatic.
                                        docker('stop','--timeout','10',mission_name)
                                        stopped=True
                                        run=subprocess.run(argv,capture_output=True,text=True,timeout=120)
                                        report=json.loads(run.stdout)
                                    assert report['launchId']==job['launchId'],report
                                    assert report['jobFilesRemoved'] is False,report
                                    assert report['automaticRetry'] is False,report
                                    assert report['independentValidationPassed'] is False,report
                                    assert report['canonicalTerminal'] is expect_terminal,report
                                    assert run.returncode==(0 if expect_terminal else 3),(run.returncode,run.stdout,run.stderr)
                                    return {**report,'deliberateStop':stopped}
                                if args.operator_provider:
                                    # Scenario: altered protected policy. The tampering is a harness
                                    # fault on its own disposable copy; production is untouched.
                                    artifact=policy_root/provider_profile['id']/'relay.mjs'
                                    intact=artifact.read_bytes()
                                    artifact.write_bytes(intact+b'\n// qualification tampering\n')
                                    refused=subprocess.run(consume_argv,capture_output=True,text=True,timeout=120)
                                    artifact.write_bytes(intact)
                                    assert refused.returncode==3,(refused.returncode,refused.stdout,refused.stderr)
                                    refusal=json.loads(refused.stdout)
                                    assert refusal['launchId']==job['launchId'],refusal
                                    assert refusal['outcome']=={'state':'invalid_provider_policy','started':False},refusal
                                    before=observe({'consumerExit':refused.returncode})
                                    assert before=={'missionContainers':0,'gatewayContainers':0,'canonicalState':'claimed',
                                        'jobDirectory':False,'perLaunchBridgeConfig':False,'gatewayDirectory':False,
                                        'consumerExit':3},before
                                    print(json.dumps({'alteredPolicyRefusedBeforeEffect':True,'observed':before,
                                                      'launchStillClaimedAndResumable':True}))
                                if args.interrupted_start:
                                    # Scenario: interruption at startup. Only this harness kills the
                                    # operator process, as soon as the container exists; no production
                                    # service is touched. This proves refusal to relaunch after an
                                    # interrupted start, NOT recovery of a finished result.
                                    running=subprocess.Popen(consume_argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
                                    for _ in range(900):
                                        if named_ids(mission_name):break
                                        if running.poll() is not None:
                                            raise RuntimeError('Consumer finished before its container existed: '+running.communicate()[0])
                                        time.sleep(.1)
                                    else:raise RuntimeError('Mission container never appeared')
                                    running.kill();running.communicate(timeout=30)
                                    identities=launch_identities(mission_name,proxy_name)
                                    for cid in identities['mission']+identities['gateway']:
                                        if cid not in ids:ids.append(cid)
                                    networks.append(proxy_name)
                                    interrupted=observe({'consumerExit':running.returncode,'responseReceived':False,
                                                         'missionContainerIds':identities['mission'],
                                                         'gatewayContainerIds':identities['gateway']})
                                    assert len(identities['mission'])==1,interrupted
                                    assert interrupted['canonicalState'] in ('creation_requested','container_created','start_requested','running'),interrupted
                                    operator=jobs/job['launchId']/'operator.json'
                                    # Establish the already-produced effect before any resume, with the
                                    # existing read-only reader. It never authorizes a restart.
                                    inspected=subprocess.run(['python3',str(ROOT/'openhands-runner/run_host_job.py'),
                                        '--config',str(operator),'--inspect','--gateway-root',str(gateways)],
                                        capture_output=True,text=True,timeout=60)
                                    assert inspected.returncode==0,(inspected.returncode,inspected.stdout,inspected.stderr)
                                    evidence=json.loads(inspected.stdout)
                                    assert evidence['launchId']==job['launchId'],evidence
                                    assert evidence['resumeAuthorized'] is False and evidence['automaticRetry'] is False,evidence
                                    assert evidence['gateway']['reconciliationRequired'] is True,evidence
                                    assert evidence['gateway']['containerId']==identities['gateway'][0],(evidence,identities)
                                    # Identical requests again, at the entry and at the consumer.
                                    replayed=subprocess.run(['python3',str(ROOT/'openhands-runner/run_host_job.py'),
                                        '--config',str(operator)],capture_output=True,text=True,timeout=90)
                                    assert replayed.returncode==2,(replayed.returncode,replayed.stdout,replayed.stderr)
                                    assert json.loads(replayed.stdout)=={'state':'reconciliation_required','automaticRetry':False}
                                    again=subprocess.run(consume_argv,capture_output=True,text=True,timeout=120)
                                    verdict=verify_no_second_effect(label='interrupted start re-invocation',
                                        before=identities,after=launch_identities(mission_name,proxy_name),
                                        exit_code=again.returncode,expected_exit=0,
                                        reported_jobs=len(again.stdout.split()),stderr=again.stderr)
                                    after=observe({'entryExit':replayed.returncode,'consumerExit':again.returncode,
                                                   'consumerReportedJobs':verdict['consumerReportedJobs'],
                                                   'missionContainerIds':verdict['missionContainerIds'],
                                                   'gatewayContainerIds':verdict['gatewayContainerIds']})
                                    assert after['canonicalState']==interrupted['canonicalState'],after
                                    expected_container[0]=identities['mission'][0]
                                    print(json.dumps({'interruptedStartRefusesRelaunch':True,'interrupted':interrupted,
                                        'afterIdenticalReplay':after,'reconciliationEvidence':evidence,'verdict':verdict,
                                        'secondContainerCreated':False,'identityReplaced':False,
                                        'explicitReconciliationDemanded':True,'finishedResultRecovered':False}))
                                    if args.reconcile:
                                        closed=reconcile_now('interrupted',expect_terminal=True)
                                        assert closed['canonicalState']=='cancelled',closed
                                        assert closed['closure']['reason']=='interrupted_before_start',closed
                                        assert closed['closure']['containerState'] in ('created','absent'),closed
                                        assert 'process' not in closed,closed
                                        assert closed['gatewayRelease']['journalState']=='released',closed
                                        after_close=launch_identities(mission_name,proxy_name)
                                        assert after_close['mission']==identities['mission'],after_close
                                        assert after_close['gateway']==[],after_close
                                        preserved={name:(jobs/job['launchId']/name).exists()
                                                   for name in ('checkout','results','dossier.json','operator.json')}
                                        assert all(preserved.values()),preserved
                                        journal=json.loads((gateways/job['launchId']/'lifecycle.json').read_text())
                                        assert journal['state']=='released' and journal['releaseErrors']==[],journal
                                        repeat=reconcile_now('already closed',expect_terminal=True)
                                        assert repeat['steps'][0]['state']=='already_final',repeat
                                        assert launch_identities(mission_name,proxy_name)==after_close
                                        expected_container[0]=identities['mission'][0];closure_expected[0]=closed['closure']['reason']
                                        print(json.dumps({'interruptedLaunchClosedOnObservedState':True,'closure':closed['closure'],
                                            'deliberateStop':closed['deliberateStop'],'gatewayRelease':closed['gatewayRelease'],
                                            'workPreserved':preserved,'repeatIsNoOperation':True,
                                            'secondContainerCreated':False,'resultInvented':False}))
                                    raise ScenarioComplete
                                if args.interrupted_run:
                                    # Scenario: the operator dies while the agent container is running.
                                    # Only this harness kills it; the container keeps its own course.
                                    running=subprocess.Popen(consume_argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
                                    for _ in range(900):
                                        ids_now=named_ids(mission_name)
                                        if ids_now and docker('inspect','--format','{{.State.Status}}',ids_now[0],check=False).stdout.strip()=='running':break
                                        if running.poll() is not None:
                                            raise RuntimeError('Consumer finished before its container ran: '+running.communicate()[0])
                                        time.sleep(.1)
                                    else:raise RuntimeError('Mission container never reached running')
                                    running.kill();running.communicate(timeout=30)
                                    identities=launch_identities(mission_name,proxy_name)
                                    for cid in identities['mission']+identities['gateway']:
                                        if cid not in ids:ids.append(cid)
                                    networks.append(proxy_name)
                                    interrupted=observe({'consumerExit':running.returncode,'responseReceived':False,
                                                         'missionContainerIds':identities['mission'],
                                                         'gatewayContainerIds':identities['gateway']})
                                    assert len(identities['mission'])==1,interrupted
                                    assert interrupted['canonicalState'] in ('start_requested','running'),interrupted
                                    if args.replaced_container:
                                        # Demonstrate the existing serialisation instead of asserting it.
                                        # Creating a container is gated by the claimed -> creation_requested
                                        # CAS, so no second creation is reachable past that stage.
                                        gate='refused'
                                        try:
                                            lifecycle_transition(command)('claimed','creation_requested',{})
                                            gate='accepted'
                                        except RuntimeError:pass
                                        assert gate=='refused','A second creation was authorised past claimed'
                                        name_conflict=docker('create','--name',mission_name,'--network','none',
                                            '--entrypoint','/bin/true',job['config']['imageDigest'],check=False)
                                        assert name_conflict.returncode!=0,'Deterministic name accepted a duplicate'
                                        # Replace the container: same name, labels and pinned image, new id.
                                        docker('rm','-f',identities['mission'][0])
                                        decoy=docker('create','--name',mission_name,
                                            '--label','oria.purpose=openhands-supervised-job',
                                            '--label','oria.launch-id='+job['launchId'],
                                            '--network','none','--entrypoint','/bin/true',
                                            job['config']['imageDigest']).stdout.strip()
                                        ids.append(decoy)
                                        assert decoy!=identities['mission'][0],decoy
                                        refused=reconcile_now('replaced container',expect_terminal=False)
                                        assert refused['canonicalState']=='start_requested',refused
                                        assert refused['steps'][0]['reason']=='container_identity_mismatch',refused
                                        assert refused['steps'][0]['identity']=='mismatch',refused
                                        assert 'closure' not in refused,refused
                                        assert refused['gatewayRelease']['attempted'] is False,refused
                                        kept=launch_identities(mission_name,proxy_name)
                                        assert kept['mission']==[decoy],kept
                                        assert kept['gateway']==identities['gateway'],kept
                                        preserved={name:(jobs/job['launchId']/name).exists()
                                                   for name in ('checkout','results','dossier.json','operator.json')}
                                        assert all(preserved.values()),preserved
                                        # Remove the replacement: now nothing claims to be this container.
                                        docker('rm','-f',decoy)
                                        closed=reconcile_now('replaced then absent',expect_terminal=True)
                                        assert closed['canonicalState']=='cancelled',closed
                                        assert closed['closure']['reason']=='result_unrecoverable',closed
                                        assert closed['closure']['containerState']=='absent',closed
                                        assert 'process' not in closed,closed
                                        assert closed['postObservation']['containerState']=='absent',closed
                                        assert closed['gatewayRelease']['journalState']=='released',closed
                                        expected_container[0]=identities['mission'][0];closure_expected[0]=closed['closure']['reason']
                                        print(json.dumps({'replacedContainerRefusedBeforeClosure':True,
                                            'secondCreationRefusedByCanonicalCas':True,
                                            'duplicateDeterministicNameRefusedByDocker':True,
                                            'canonicalContainerId':identities['mission'][0],'observedDecoyId':decoy,
                                            'refusal':{'reason':refused['steps'][0]['reason'],
                                                       'identity':refused['steps'][0]['identity'],
                                                       'gatewayRelease':refused['gatewayRelease']},
                                            'workPreservedDuringRefusal':preserved,
                                            'closureAfterRemoval':closed['closure'],
                                            'resultInvented':False,'independentValidationPassed':False}))
                                        raise ScenarioComplete
                                    # The unsupervised container finishes on its own; nothing restarts it.
                                    for _ in range(1200):
                                        status=docker('inspect','--format','{{.State.Status}}',identities['mission'][0],check=False).stdout.strip()
                                        if status in ('exited','dead'):break
                                        time.sleep(.25)
                                    else:raise RuntimeError('Mission container never stopped')
                                    observed_exit=int(docker('inspect','--format','{{.State.ExitCode}}',identities['mission'][0]).stdout.strip())
                                    recovered=reconcile_now('interrupted run',expect_terminal=True)
                                    assert recovered['canonicalState']=='execution_finished',recovered
                                    assert recovered['steps'][0]['state']=='result_recovered',recovered
                                    assert recovered['process']=={'exitCode':observed_exit,'containerStopped':True,
                                                                  'deadlineExceeded':False},recovered
                                    assert 'closure' not in recovered,recovered
                                    assert recovered['steps'][0]['retainedEvidence']=={'started':'bound','outcome':'present'},recovered
                                    assert recovered['gatewayRelease']['journalState']=='released',recovered
                                    after_recover=launch_identities(mission_name,proxy_name)
                                    assert after_recover['mission']==identities['mission'],after_recover
                                    assert after_recover['gateway']==[],after_recover
                                    saved=json.loads((jobs/job['launchId']/'results/outcome.json').read_text())
                                    started_file=json.loads((jobs/job['launchId']/'results/started.json').read_text())
                                    assert started_file['payloadHash']==job['dossier']['payloadHash'],started_file
                                    assert saved['independentValidationPassed'] is False,saved
                                    repeat=reconcile_now('already recovered',expect_terminal=True)
                                    assert repeat['steps'][0]['state']=='already_final',repeat
                                    assert launch_identities(mission_name,proxy_name)==after_recover
                                    expected_container[0]=identities['mission'][0]
                                    print(json.dumps({'interruptedRunResultRecovered':True,'interrupted':interrupted,
                                        'observedExitCode':observed_exit,'process':recovered['process'],
                                        'retainedEvidence':recovered['steps'][0]['retainedEvidence'],
                                        'gatewayRelease':recovered['gatewayRelease'],'repeatIsNoOperation':True,
                                        'secondContainerCreated':False,'reExecuted':False,
                                        'independentValidationPassed':False}))
                                    raise ScenarioComplete
                                if args.lost_completed_response:
                                    # Scenario: the execution completes, then only the RECEPTION of its
                                    # response is removed in this harness (stdout discarded). The effect
                                    # must be recovered from durable state and retained evidence.
                                    completed=subprocess.run(consume_argv,stdout=subprocess.DEVNULL,
                                        stderr=subprocess.PIPE,text=True,timeout=180)
                                    assert completed.returncode==0,(completed.returncode,completed.stderr)
                                    identities=launch_identities(mission_name,proxy_name)
                                    for cid in identities['mission']+identities['gateway']:
                                        if cid not in ids:ids.append(cid)
                                    assert len(identities['mission'])==1,identities
                                    operator=jobs/job['launchId']/'operator.json'
                                    recovered=subprocess.run(['python3',str(ROOT/'openhands-runner/run_host_job.py'),
                                        '--config',str(operator),'--inspect','--gateway-root',str(gateways)],
                                        capture_output=True,text=True,timeout=60)
                                    assert recovered.returncode==0,(recovered.returncode,recovered.stdout,recovered.stderr)
                                    evidence=json.loads(recovered.stdout)
                                    assert evidence['launchId']==job['launchId'],evidence
                                    assert evidence['canonicalState']=='execution_finished',evidence
                                    assert evidence['resumeAuthorized'] is False,evidence
                                    assert evidence['independentValidationPassed'] is False,evidence
                                    assert evidence['gateway']['containerState']=='absent',evidence
                                    assert evidence['gateway']['networkState']=='absent',evidence
                                    claim=lifecycle_reader(command)()
                                    assert claim['containerId']==identities['mission'][0],(claim,identities)
                                    results=(jobs/job['launchId']/'results/outcome.json').read_bytes()
                                    started=(jobs/job['launchId']/'results/started.json').read_bytes()
                                    # Identical requests again, at the entry and at the consumer.
                                    replayed=subprocess.run(['python3',str(ROOT/'openhands-runner/run_host_job.py'),
                                        '--config',str(operator)],capture_output=True,text=True,timeout=90)
                                    assert replayed.returncode!=0,(replayed.returncode,replayed.stdout)
                                    refusal=json.loads(replayed.stdout)
                                    assert refusal['state'] in ('reconciliation_required','not_acquired'),refusal
                                    assert refusal.get('started',False) is False,refusal
                                    again=subprocess.run(consume_argv,capture_output=True,text=True,timeout=120)
                                    verdict=verify_no_second_effect(label='lost completed response re-invocation',
                                        before=identities,after=launch_identities(mission_name,proxy_name),
                                        exit_code=again.returncode,expected_exit=0,
                                        reported_jobs=len(again.stdout.split()),stderr=again.stderr)
                                    post=lifecycle_reader(command)()
                                    assert post['state']=='execution_finished',post
                                    assert post['containerId']==claim['containerId'],(post,claim)
                                    assert (jobs/job['launchId']/'results/outcome.json').read_bytes()==results
                                    assert (jobs/job['launchId']/'results/started.json').read_bytes()==started
                                    expected_container[0]=identities['mission'][0]
                                    print(json.dumps({'lostCompletedResponse':True,'responsePayloadDiscarded':True,
                                        'recoveredFromDurableStateAndRetainedEvidence':True,'entryRefusal':refusal,
                                        'entryExit':replayed.returncode,'reconciliationEvidence':evidence,
                                        'verdict':verdict,'resultsUnchanged':True,'newExecutionStarted':False,
                                        'identityReplaced':False,'independentValidationPassed':False,
                                        'businessSuccessClaimed':False}))
                                    if args.reconcile:
                                        final=reconcile_now('completed',expect_terminal=True)
                                        assert final['canonicalState']=='execution_finished',final
                                        assert final['steps'][0]['state']=='already_final',final
                                        assert final['steps'][0]['retainedEvidence']=={'started':'bound','outcome':'present'},final
                                        assert 'closure' not in final,final
                                        assert final['process']['exitCode']==0,final
                                        assert launch_identities(mission_name,proxy_name)==identities
                                        assert (jobs/job['launchId']/'results/outcome.json').read_bytes()==results
                                        print(json.dumps({'finishedResultReadBackWithoutExecuting':True,
                                            'canonicalState':final['canonicalState'],'process':final['process'],
                                            'retainedEvidence':final['steps'][0]['retainedEvidence'],
                                            'gatewayRelease':final['gatewayRelease'],'newExecutionStarted':False}))
                                    raise ScenarioComplete
                                if args.consumer_service:
                                    from qualify_consumer_service import run_service
                                    def remember(report):
                                        if report.get('outcome',{}).get('containerId'):ids.append(report['outcome']['containerId'])
                                    report=run_service(consumer,on_report=remember)
                                else:
                                    consumed=subprocess.run(consume_argv,capture_output=True,text=True,timeout=180)
                                    expected=0 if args.operator_provider else 3
                                    assert consumed.returncode==expected,(consumed.returncode,consumed.stdout,consumed.stderr)
                                    report=json.loads(consumed.stdout)
                                    if args.operator_provider:
                                        identities=launch_identities(mission_name,proxy_name)
                                        assert len(identities['mission'])==1,identities
                                        expected_container[0]=identities['mission'][0]
                                        nominal=observe({'consumerExit':consumed.returncode,
                                                         'missionContainerIds':identities['mission'],
                                                         'gatewayContainerIds':identities['gateway']})
                                        assert nominal['canonicalState']=='execution_finished',nominal
                                        assert report['outcome']['containerId']==identities['mission'][0],(report,identities)
                                        print(json.dumps({'nominalOperatorProviderLaunch':True,'observed':nominal}))
                                assert report['launchId']==job['launchId']
                                outcome=report['outcome']
                                if outcome.get('containerId') and outcome['containerId'] not in ids:ids.append(outcome['containerId'])
                                prepared={'operatorConfig':str(jobs/job['launchId']/'operator.json')}
                                print(json.dumps({'actualHostConsumer':True,'serialFailureStopsConsumer':True}))
                            else:
                                prep_process=subprocess.run([sys.executable,str(Path(__file__).with_name('project_sources.py')),'--config',str(preparation)],capture_output=True,text=True,timeout=60)
                                assert prep_process.returncode==0, 'Preparation CLI failed'
                                prepared=json.loads(prep_process.stdout)
                        else:prepared=prepare_host_job(command=command,source=source.name,jobs_root=jobs,control_root=controls,provider_execution=authorization)
                        operator=Path(prepared['operatorConfig']);root=operator.parent
                        try:prepare_host_job(command=command,source=source.name,jobs_root=jobs,control_root=controls,provider_execution=authorization)
                        except FileExistsError:pass
                        except RuntimeError:
                            if not args.host_consumer:raise
                            assert lifecycle_reader(command)()['state']=='execution_finished'
                        else:raise AssertionError('Repeated preparation accepted')
                        assert git('rev-parse','HEAD')==source_commit
                        print(json.dumps({'canonicalPreparation':True,'repeatedPreparationRefused':True,'sourceUnchanged':True,'projectSourceRegistry':args.project_source}))
                    else:
                        if args.host_entry:root.mkdir(mode=0o755)
                        for folder in ('checkout','results'):
                            path=root/folder;path.mkdir();os.chown(path,10001,10001)
                    if args.valid_dossier and not args.prepare_host:
                        subprocess.run(['git','clone','--no-hardlinks',source.name,str(root/'checkout')],check=True,capture_output=True)
                        for path in (root/'checkout').rglob('*'):os.chown(path,10001,10001)
                        (root/'dossier.json').write_text(json.dumps(job['dossier']))
                    elif not args.prepare_host:
                        (root/'dossier.json').write_text('{}')
                    if args.host_entry:
                        if not args.prepare_host:
                            (root/'ipc').mkdir(mode=0o755)
                            review=base/'control'/job['launchId'];review.mkdir(parents=True,mode=0o755)
                            command[0]=str(Path(shutil.which('docker')).resolve(strict=True))
                            operator=base/'operator.json'
                            operator.write_text(json.dumps({'lifecycleCommand':command,'jobRoot':str(root),'reviewSocket':str(review/'review.sock')}))
                            operator.chmod(0o600)
                        if not args.host_consumer:
                            entry=subprocess.run(['python3',str(ROOT/'openhands-runner/run_host_job.py'),'--config',str(operator)],capture_output=True,text=True,timeout=90)
                            outcome=json.loads(entry.stdout)
                            if outcome.get('containerId'):ids.append(outcome['containerId'])
                            assert entry.returncode==0,outcome
                        replay=subprocess.run(['python3',str(ROOT/'openhands-runner/run_host_job.py'),'--config',str(operator)],capture_output=True,text=True,timeout=30)
                        assert replay.returncode!=0
                        assert lifecycle_reader(command)()['containerId']==outcome['containerId']
                        print(json.dumps({'actualOperatorEntry':True,'repeatRefused':True,'sameContainerRetained':True}))
                    elif args.permission_worker:
                        (root/'ipc').mkdir(mode=0o755)
                        def run_with_probe(**parameters):
                            with ThreadPoolExecutor(max_workers=1) as pool:
                                execution=pool.submit(supervise,**parameters)
                                for _ in range(80):
                                    state=docker('inspect','--format','{{.State.Running}}',parameters['container_id']).stdout.strip()
                                    if state=='true':break
                                    if execution.done():raise RuntimeError('Runner exited before permission probe')
                                    time.sleep(.05)
                                else:raise RuntimeError('Runner did not start')
                                request={'session_id':'qualification-session','tool_call':{'toolCallId':'qualification-call','rawInput':{'command':'npm test'}},
                                         'options':[{'optionId':'once','kind':'allow_once'}]}
                                with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as client:
                                    client.settimeout(25);client.connect(str(root/'ipc'/'permission.sock'))
                                    client.sendall(json.dumps(request).encode()+b'\n')
                                    response=json.loads(client.makefile('rb').readline(32768))
                                assert response=={'outcome':{'outcome':'cancelled'}},response
                                observed=lifecycle_reader(command)()
                                assert observed['state']=='running' and observed['sessionId']=='qualification-session'
                                print(json.dumps({'permissionProbeDeniedWithoutApproval':True,'sessionPersistedInHq':True,'probeOrigin':'synthetic-host-client'}))
                                return execution.result()
                        outcome=asyncio.run(run_permission_job(command=command,job={
                            'launchId':job['launchId'],'missionId':job['dossier']['mission']['id'],
                            'workspaceId':job['workspaceId'],'runnerId':job['config']['runnerId'],
                            'imageDigest':job['config']['imageDigest'],'timeoutSeconds':job['config']['timeoutSeconds']},job_root=root,
                            run=run_with_probe if args.probe_permission else supervise,
                            **({'gateway_root':gateways,'policy_root':policy_root,
                                'authorization':{'profileId':provider_profile['id'],
                                    'policySha256':provider_profile['policySha256'],
                                    'policyRoot':str(policy_root),'gatewayRoot':str(gateways)}}
                               if args.synthetic_provider else {})))
                    else:
                        outcome=dispatch(transition=lifecycle_transition(command),read_claim=lifecycle_reader(command),launch_id=job['launchId'],
                            image_digest=job['config']['imageDigest'],workspace_id=job['workspaceId'],
                            job_root=root,timeout_seconds=job['config']['timeoutSeconds'])
                    if outcome.get('containerId') and outcome['containerId'] not in ids:ids.append(outcome['containerId'])
                    assert outcome['state']=='execution_finished',outcome
                    assert outcome['process']['exitCode']==(0 if args.synthetic_provider else 1),outcome
                    assert outcome['process']['containerStopped']
                    if args.valid_dossier:
                        started=json.loads((root/'results/started.json').read_text())
                        assert started['payloadHash']==job['dossier']['payloadHash']
                        assert started['commitSha']==source_commit
                        saved=json.loads((root/'results/outcome.json').read_text())
                        assert saved['state']==('agent_returned' if args.synthetic_provider else 'execution_error'),saved
                        if args.synthetic_provider:
                            assert outcome['process']['exitCode']==0,outcome
                            assert saved['independentValidationPassed'] is False
                            transport=json.loads((root/'results/provider-fixture.json').read_text())
                            assert transport['providerTlsVerified'] and transport['foreignHostDenied']
                            journal=json.loads((gateways/job['launchId']/'lifecycle.json').read_text())
                            assert journal['state']=='closed'
                            recovery=recovery_report(command=command,gateway_root=gateways)
                            assert recovery['status']=='observed' and recovery['canonicalState']=='execution_finished'
                            assert recovery['gateway']['containerState']=='absent' and recovery['gateway']['networkState']=='absent'
                            assert recovery['resumeAuthorized'] is False
                            if reports:publish_report(recovery,reports.name)
                            print(json.dumps({'actualCanonicalRecoveryReport':recovery}))
                            if args.live_memex:
                                conversation_files=[path for path in (root/'results/conversation').rglob('*') if path.is_file()]
                                conversation_text='\n'.join(path.read_text(encoding='utf-8') for path in conversation_files)
                                assert 'Original decision' in conversation_text
                                assert 'FOREIGN_CONTENT_MUST_NOT_APPEAR' not in conversation_text
                                assert 'New decision after capture' not in conversation_text
                                assert job['dossier']['memory']['content']
                                print(json.dumps({'capturedMemexContextInSdkConversation':True,'foreignProjectAbsent':True,'postCaptureMutationAbsent':True,'conversationFiles':len(conversation_files)}))
                            print(json.dumps({'actualWorkerGatewayAndHqStore':True,'syntheticAcp':True,'providerTlsVerified':True,'foreignHostDenied':True,'gatewayClosed':True,'modelRequests':0}))
                        diagnostic=docker('logs',outcome['containerId'],check=False)
                        # This disposable fixture has no credentials or user data.
                        # Print the exception tail only, never general service logs.
                        tail=(diagnostic.stdout+diagnostic.stderr).splitlines()[-8:]
                        print(json.dumps({'isolatedRuntimeDiagnosticTail':tail}))
                        print(json.dumps({'canonicalDossierReachedRunner':True,'exactCommitVerified':True,'noProviderAccount':True}))
                    print(json.dumps({'actualHostDispatch':True,'outcome':outcome}))
                docker('exec',node,'touch','/tmp/host-done')
                waited=docker('wait',node)
                result=docker('logs',node,check=False)
                result.returncode=int(waited.stdout.strip())
            else:
                result=docker('start','-a',node,check=False)
            if control_host:
                if result.returncode:control_host.terminate()
                try:control_exit=control_host.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    control_host.kill();control_host.wait();raise RuntimeError('Control host failed to finish')
                if not result.returncode and control_exit:raise RuntimeError('Control host qualification failed')
            control.cleanup()
            if result.returncode:
                print(result.stdout);print(result.stderr);raise RuntimeError('HQ store qualification failed')
            print(result.stdout.strip())
        phase('seed')
        docker('stop',rest);docker('restart',pg);ready();docker('start',rest)
        phase('verify')
        print(json.dumps({'databaseRestartVerified':True,'publicPorts':False,'productionDatabaseUsed':False}))
    finally:
        for process in control_processes:
            if process.poll() is None:
                process.terminate()
                try:process.wait(timeout=5)
                except subprocess.TimeoutExpired:process.kill();process.wait()
        cleanup=[docker('rm','-f',cid,check=False).returncode for cid in reversed(ids)]
        for network in networks:docker('network','rm',network,check=False)
        for directory in control_directories:directory.cleanup()
        docker('volume','rm',volume)
        source.cleanup()
        if any(cleanup): raise RuntimeError('Qualification container cleanup incomplete')

if __name__=='__main__': main()
