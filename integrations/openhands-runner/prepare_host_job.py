"""Prepare one canonical authorized HQ job, without executing agent code."""
import json
import os
from pathlib import Path
from hq_transition import lifecycle_reader
from dossier import prepare
from workspace import prepare_workspace
from run_host_job import protected_path


def prepare_host_job(*,command,source,jobs_root,control_root,expected_payload_hash=None):
    if os.name!='posix' or os.geteuid()!=0:raise ValueError('Linux root operator required')
    source=protected_path(source,directory=True)
    jobs=protected_path(jobs_root,directory=True)
    controls=protected_path(control_root,directory=True)
    if jobs==controls or jobs in controls.parents or controls in jobs.parents:
        raise ValueError('Separate job and control roots required')
    if source==jobs or source in jobs.parents or source==controls or source in controls.parents:
        raise ValueError('Runtime roots must be outside source')
    command=tuple(command)
    if not command:raise ValueError('Trusted command required')
    protected_path(command[0])
    observed=lifecycle_reader(command,prepare=True)()
    claim=observed['claim'];config=observed['config'];dossier=observed['dossier']
    if expected_payload_hash is not None and claim['payloadHash']!=expected_payload_hash:
        raise ValueError('Canonical project changed during source selection')
    from uuid import UUID
    launch=claim['launchId']
    if str(UUID(launch))!=launch or claim['state']!='claimed':raise ValueError('Claimed canonical launch required')
    verified=prepare(dossier,expected_workspace=claim['workspaceId'],expected_executor_version=config['executorVersion'],checkout=source)
    if (verified['payloadHash']!=claim['payloadHash'] or verified['commitSha']!=claim['commitSha']
            or dossier['mission']['id']!=claim['missionId']):raise ValueError('Canonical dossier mismatch')
    root=jobs/launch;review=controls/launch
    if os.path.lexists(root) or os.path.lexists(review):raise FileExistsError('Prior preparation requires reconciliation')
    # Exclusive directories retain partial work after any failure; never reuse.
    root.mkdir(mode=0o755);review.mkdir(mode=0o755)
    # Service UMask=0077 must not hide the intentionally traversable job/control
    # paths from the container UID or the HQ review reader.
    root.chmod(0o755);review.chmod(0o755)
    checkout=prepare_workspace(source=source,commit=verified['commitSha'],server_root=root,job_name='checkout')
    tree=Path(checkout['checkout'])
    for parent,dirs,files in os.walk(tree,followlinks=False):
        for name in dirs+files:os.chown(Path(parent)/name,10001,10001,follow_symlinks=False)
    os.chown(tree,10001,10001)
    (root/'results').mkdir(mode=0o700);os.chown(root/'results',10001,10001)
    (root/'ipc').mkdir(mode=0o755)
    (root/'ipc').chmod(0o755)
    def write(filename,value,mode):
        fd=os.open(filename,os.O_WRONLY|os.O_CREAT|os.O_EXCL,mode)
        with os.fdopen(fd,'w',encoding='utf-8') as stream:
            json.dump(value,stream,ensure_ascii=False,allow_nan=False);stream.flush();os.fchmod(stream.fileno(),mode);os.fsync(stream.fileno())
    write(root/'dossier.json',dossier,0o444)
    write(root/'operator.json',dict(lifecycleCommand=list(command),jobRoot=str(root),reviewSocket=str(review/'review.sock')),0o600)
    return {'state':'prepared','operatorConfig':str(root/'operator.json'),'launchId':launch,
            'commitSha':verified['commitSha'],'executionRequested':False}
