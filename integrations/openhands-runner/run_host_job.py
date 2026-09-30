"""Operator entry point for one already-authorized, already-prepared HQ job.

Root-owned configuration only. Does not claim a mission, grant permissions,
connect a provider, retry execution, or deploy changes.
"""
import argparse
import asyncio
import json
import os
from pathlib import Path
import stat
import sys
from hq_transition import lifecycle_reader
from permission_worker import run_permission_job
from recovery_report import recovery_report,publish_report


def protected_path(raw, *, directory=False):
    path=Path(raw)
    if not path.is_absolute() or path.resolve(strict=True)!=path:
        raise ValueError('Real absolute host path required')
    for parent in (path,*path.parents):
        info=parent.stat()
        if info.st_uid!=0 or info.st_mode & 0o022:
            raise ValueError('Root-owned non-writable host path required')
    info=path.stat()
    if not (stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode)):
        raise ValueError('Unexpected host path type')
    return path


def unique_object(pairs):
    result={}
    for key,value in pairs:
        if key in result:raise ValueError('Duplicate configuration key')
        result[key]=value
    return result


def load_configuration(filename,*,read_only=False):
    if os.name!='posix' or os.geteuid()!=0:
        raise ValueError('Linux root operator required')
    path=protected_path(filename)
    if path.stat().st_size>16384:raise ValueError('Oversized host configuration')
    config=json.loads(path.read_text(encoding='utf-8'),object_pairs_hook=unique_object,
                      parse_constant=lambda _:(_ for _ in ()).throw(ValueError('Nonfinite value')))
    if not isinstance(config,dict) or set(config)!={'lifecycleCommand','jobRoot','reviewSocket'}:
        raise ValueError('Invalid host configuration fields')
    command=config['lifecycleCommand']
    if not isinstance(command,list) or not 1<=len(command)<=32 or any(
            not isinstance(arg,str) or not arg or len(arg)>4096 or '\0' in arg for arg in command):
        raise ValueError('Explicit host command required')
    protected_path(command[0])
    root=protected_path(config['jobRoot'],directory=True)
    review=Path(config['reviewSocket'])
    if not review.is_absolute() or review.name!='review.sock' or root in review.parents:
        raise ValueError('Private control socket outside job required')
    protected_path(str(review.parent),directory=True)
    if os.path.lexists(review) and not read_only:raise ValueError('Existing control socket requires reconciliation')
    return tuple(command),root,review


async def execute_configuration(filename):
    command,root,review=load_configuration(filename)
    observed=await asyncio.to_thread(lifecycle_reader(command,include_config=True))
    claim=observed['claim'];config=observed['config']
    if claim['state']!='claimed':return {'state':'not_acquired','started':False}
    if root.name!=claim['launchId'] or review.parent.name!=claim['launchId']:
        raise ValueError('Host directories must match canonical launch')
    job={key:claim[key] for key in ('launchId','missionId','workspaceId','runnerId')}
    job.update(imageDigest=config['imageDigest'],timeoutSeconds=config['timeoutSeconds'])
    # The worker rereads canonical authority before any Docker effect. A stale
    # initial observation never grants permission on its own.
    return await run_permission_job(command=command,job=job,job_root=root,review_socket=review)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',required=True)
    parser.add_argument('--inspect',action='store_true',help='Read canonical mission and gateway state without execution')
    parser.add_argument('--gateway-root',help='Protected host gateway directory, inspection only')
    parser.add_argument('--report-directory',help='Publish inspection JSON atomically in a protected host directory')
    args=parser.parse_args()
    if bool(args.gateway_root)!=args.inspect:parser.error('--inspect requires --gateway-root; execution does not accept it')
    if args.report_directory and not args.inspect:parser.error('--report-directory requires --inspect')
    try:
        if args.inspect:
            command,root,review=load_configuration(args.config,read_only=True)
            gateway_root=protected_path(args.gateway_root,directory=True)
            report=recovery_report(command=command,gateway_root=gateway_root)
            if root.name!=report['launchId'] or review.parent.name!=report['launchId']:
                raise ValueError('Canonical launch mismatch')
            if args.report_directory:publish_report(report,args.report_directory)
            print(json.dumps(report));return 0 if report['status']=='observed' else 3
        result=asyncio.run(execute_configuration(args.config))
        print(json.dumps(result))
        return 0 if result.get('state')=='execution_finished' else 3
    except (Exception,):
        # Never print trusted command arguments, dossier contents or credentials.
        print(json.dumps({'state':'reconciliation_required','automaticRetry':False}))
        return 2


if __name__=='__main__':sys.exit(main())
