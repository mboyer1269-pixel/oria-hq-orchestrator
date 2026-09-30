"""Private serial host consumer. Canonical HQ claims are the only work queue."""
import argparse
import asyncio
import json
import os
from pathlib import Path, PurePosixPath
import signal
import subprocess
import sys
import threading
from uuid import UUID
from run_host_job import protected_path, unique_object, execute_configuration
from project_sources import prepare_configured_project
from provider_policy import provider_preflight,separate_gateway_root,validate_authorization


def read_json(path):
    path=protected_path(path)
    if path.stat().st_size>16384:raise ValueError('Oversized configuration')
    return json.loads(path.read_text(encoding='utf-8'),object_pairs_hook=unique_object)


def load_config(filename):
    if os.name!='posix' or os.geteuid()!=0:raise ValueError('Linux root required')
    config=read_json(filename)
    base={'bridgeCommand','bridgeScriptsRoot','bridgeConfigRoot','hostConfigRoot','profileFile','registryFile','jobsRoot','controlRoot'}
    # Absent key keeps the installed offline consumer contract byte for byte.
    if not isinstance(config,dict) or set(config) not in (base,base|{'providerExecution'}):
        raise ValueError('Invalid consumer configuration')
    command=config['bridgeCommand']
    if not isinstance(command,list) or not 1<=len(command)<=32 or any(not isinstance(a,str) or not a or len(a)>4096 or '\0' in a for a in command):raise ValueError('Invalid host command')
    protected_path(command[0])
    for key in ('bridgeScriptsRoot','bridgeConfigRoot'):
        value=config[key]
        if not isinstance(value,str) or not value.startswith('/') or str(PurePosixPath(value))!=value or '..' in PurePosixPath(value).parts or '\0' in value:raise ValueError('Absolute bridge path required')
    for key in ('hostConfigRoot','jobsRoot','controlRoot'):config[key]=protected_path(config[key],directory=True)
    provider=config.get('providerExecution')
    if provider is not None:
        validate_authorization(provider)
        runtime=(config['hostConfigRoot'],config['jobsRoot'],config['controlRoot'])
        gateway=protected_path(provider['gatewayRoot'],directory=True)
        separate_gateway_root(protected_path(provider['policyRoot'],directory=True),(*runtime,gateway))
        separate_gateway_root(gateway,runtime)
    config['registryFile']=protected_path(config['registryFile'])
    profile_path=protected_path(config['profileFile'])
    if profile_path.parent!=config['hostConfigRoot']:raise ValueError('Profile must be in mounted host configuration root')
    profile=read_json(profile_path)
    if not isinstance(profile,dict) or set(profile)!={'context','config'}:raise ValueError('Invalid profile')
    # Canonical discovery validates the full profile and executor schema.
    config['profile']=profile
    config['bridgeProfile']=str(PurePosixPath(config['bridgeConfigRoot'])/profile_path.name)
    return config


def discover(config,cursor=None):
    command=[*config['bridgeCommand'],str(PurePosixPath(config['bridgeScriptsRoot'])/'openhands-pending-launches.mjs'),config['bridgeProfile']]
    if cursor:command.append(cursor)
    result=subprocess.run(command,capture_output=True,text=True,timeout=45)
    if result.returncode!=0 or len(result.stdout.encode())>32768:raise RuntimeError('Discovery unavailable')
    data=json.loads(result.stdout,object_pairs_hook=unique_object)
    if not isinstance(data,dict) or data.get('status')!='ready' or not isinstance(data.get('jobs'),list) or len(data['jobs'])>20:raise ValueError('Invalid discovery')
    after=data.get('nextAfterMissionId')
    if after is not None and str(UUID(after))!=after:raise ValueError('Invalid cursor')
    if cursor and after and after<=cursor:raise ValueError('Nonadvancing cursor')
    seen=set()
    for job in data['jobs']:
        if not isinstance(job,dict) or set(job)!={'missionId','launchId','payloadHash','authorizationExpiresAt'}:raise ValueError('Invalid job reference')
        for key in ('missionId','launchId'):
            if str(UUID(job[key]))!=job[key]:raise ValueError('Invalid identity')
        if job['launchId'] in seen:raise ValueError('Repeated discovery job')
        seen.add(job['launchId'])
        digest=job['payloadHash']
        if not isinstance(digest,str) or len(digest)!=64 or any(c not in '0123456789abcdef' for c in digest):raise ValueError('Invalid payload identity')
    return data


def consume(config,job):
    # Refuse unsupported provider execution before allocating a job or checkout.
    # An explicitly authorized profile whose protected policy still matches passes
    # here; preparation and the worker independently recheck canonical authority.
    provider=config.get('providerExecution')
    provider_status=provider_preflight(config['profile']['config'],provider)
    if provider_status is not None:return provider_status
    # Exclusive per-launch directory persists any partial attempt. Never reclaim
    # it automatically after interruption; canonical CAS also guards execution.
    folder=config['hostConfigRoot']/job['launchId']
    folder.mkdir(mode=0o700)
    filename=folder/'lifecycle.json'
    value={**config['profile'],'missionId':job['missionId'],'launchId':job['launchId']}
    fd=os.open(filename,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    with os.fdopen(fd,'w',encoding='utf-8') as stream:
        json.dump(value,stream,allow_nan=False);stream.flush();os.fsync(stream.fileno())
    mapped=str(PurePosixPath(config['bridgeConfigRoot'])/job['launchId']/'lifecycle.json')
    command=[*config['bridgeCommand'],str(PurePosixPath(config['bridgeScriptsRoot'])/'openhands-lifecycle.mjs'),mapped]
    prepared=prepare_configured_project(command=command,registry_file=config['registryFile'],jobs_root=config['jobsRoot'],control_root=config['controlRoot'],
                                        expected_payload_hash=job['payloadHash'],provider_execution=provider)
    return asyncio.run(execute_configuration(prepared['operatorConfig']))


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--config',required=True);parser.add_argument('--watch',action='store_true')
    args=parser.parse_args();stop=threading.Event()
    for sig in (signal.SIGTERM,signal.SIGINT):signal.signal(sig,lambda *_:stop.set())
    try:
        import fcntl
        config=load_config(args.config)
        lock_path=config['hostConfigRoot']/'consumer.lock'
        descriptor=os.open(lock_path,os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
        with os.fdopen(descriptor,'a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            cursor=None
            while not stop.is_set():
                page=discover(config,cursor)
                for job in page['jobs']:
                    if stop.is_set():break
                    try:outcome=consume(config,job)
                    except FileExistsError:
                        print(json.dumps({'state':'reconciliation_required','launchId':job['launchId'],'automaticRetry':False}),flush=True)
                        return 2
                    print(json.dumps({'launchId':job['launchId'],'outcome':outcome}),flush=True)
                    if outcome.get('state')!='execution_finished' or outcome.get('process',{}).get('exitCode')!=0:return 3
                if not args.watch:return 0
                cursor=page['nextAfterMissionId']
                stop.wait(1 if cursor else 5)
        return 0
    except Exception:
        print(json.dumps({'state':'consumer_stopped','automaticRetry':False}),flush=True);return 2


if __name__=='__main__':sys.exit(main())
