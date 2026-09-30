"""Read-only canonical mission/gateway observation; not authority to resume."""
from datetime import datetime,timezone
from hq_transition import lifecycle_reader
from provider_gateway import inspect_gateway
import json
import os
from pathlib import Path
import tempfile
import uuid


def publish_report(report,directory):
    from run_host_job import protected_path
    directory=protected_path(directory,directory=True)
    launch=str(uuid.UUID(report['launchId']))
    raw=json.dumps(report).encode()
    if len(raw)>16384:raise ValueError('Oversized recovery report')
    temporary=None
    try:
        with tempfile.NamedTemporaryFile(dir=directory,prefix='.recovery-',delete=False) as stream:
            temporary=Path(stream.name);stream.write(raw);stream.flush();os.fsync(stream.fileno());os.fchmod(stream.fileno(),0o444)
        os.replace(temporary,directory/(launch+'.json'));temporary=None
        fd=os.open(directory,os.O_RDONLY|os.O_DIRECTORY)
        try:os.fsync(fd)
        finally:os.close(fd)
    finally:
        if temporary is not None:temporary.unlink(missing_ok=True)


def recovery_report(*,command,gateway_root,read=None,inspect=inspect_gateway):
    read=read or lifecycle_reader(command,include_config=True)
    first=read();claim=first['claim'];config=first['config']
    identity={key:claim[key] for key in ('launchId','missionId','workspaceId','runnerId')}
    gateway=None
    if 'providerProfile' in config:
        try:gateway=inspect(root=gateway_root,launch_id=claim['launchId'])
        except Exception:gateway={'containerState':'unknown','networkState':'unknown','inspectionIncomplete':True,'reconciliationRequired':True}
    # Two reads detect observed concurrent changes, not every possible race.
    second=read()
    stable=second==first
    return {'version':1,**identity,'observedAt':datetime.now(timezone.utc).isoformat(),
            'canonicalState':claim['state'],'canonicalObservationStable':stable,
            'status':'observed' if stable else 'changed_during_inspection',
            'gateway':gateway,'automaticRetry':False,'resourcesModified':False,
            'resumeAuthorized':False,'independentValidationPassed':False}
