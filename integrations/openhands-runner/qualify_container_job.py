"""Disposable real-Docker rejection check; no account or model required."""
import argparse
import json
import os
from pathlib import Path
import tempfile
import uuid
from container_job import create_job
from supervisor import docker, supervise


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image',required=True)
    args=parser.parse_args()
    container_id=None
    with tempfile.TemporaryDirectory(prefix='hq-container-qualification-') as temporary:
        root=Path(temporary)
        root.chmod(0o755)
        for name in ('checkout','results'):
            path=root/name;path.mkdir();os.chown(path,10001,10001)
        (root/'dossier.json').write_text('{}')
        try:
            created=create_job(launch_id=str(uuid.uuid4()),image_digest=args.image,
                               workspace_id='qualification',job_root=root)
            container_id=created['containerId']
            inspected=json.loads(docker('inspect','--format','{{json .HostConfig}}',container_id).stdout)
            assert inspected['NetworkMode']=='none'
            assert inspected['ReadonlyRootfs'] is True
            assert inspected['Memory']==1073741824
            assert inspected['NanoCpus']==1000000000
            mounts=json.loads(docker('inspect','--format','{{json .Mounts}}',container_id).stdout)
            assert {m['Destination'] for m in mounts}=={'/workspace','/results','/mission.json'}
            assert next(m for m in mounts if m['Destination']=='/mission.json')['RW'] is False
            result=supervise(container_id=container_id,timeout_seconds=20)
            assert result['exitCode']!=0 and result['containerStopped']
            assert not list((root/'results').iterdir())
            logs=docker('logs',container_id)
            assert 'dossier.InvalidDossier: Unexpected contract fields' in logs.stderr
            print(json.dumps({'dockerCreationVerified':True,'invalidDossierRejected':True,
                              'network':'none','modelCalls':0,'supervision':result}))
        finally:
            if container_id:
                docker('rm','-f',container_id)


if __name__=='__main__':main()
