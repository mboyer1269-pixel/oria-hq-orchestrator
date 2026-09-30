"""Build an explicit, reproducible host-only release; never includes credentials."""
import argparse
import ast
import hashlib
import io
import json
from pathlib import Path
import tarfile

FILES=('consume_pending.py','container_job.py','dispatch.py','dossier.py','hq_transition.py',
       'pending_permissions.py','permission_control.py','permission_host.py','permission_transport.py',
       'permission_worker.py','prepare_host_job.py','project_sources.py','provider_policy.py','provider_gateway.py','recovery_report.py','run_host_job.py',
       'session_permissions.py','supervisor.py','workspace.py','oria-hq-consumer.service',
       'consumer.example.json','HOST-CONSUMER.md','HOST-ENTRY.md')


def release(source,output):
    source=Path(source).resolve(strict=True);output=Path(output)
    data={name:(source/name).read_bytes() for name in FILES}
    for name,content in data.items():
        if not name.endswith('.py'):continue
        tree=ast.parse(content,filename=name)
        for node in ast.walk(tree):
            modules=[node.module] if isinstance(node,ast.ImportFrom) else [n.name for n in node.names] if isinstance(node,ast.Import) else []
            for module in modules:
                dependency=(module or '').split('.')[0]+'.py'
                if (source/dependency).is_file() and dependency not in data:raise ValueError('Unpackaged local dependency: '+dependency)
    manifest={'version':1,'files':{name:hashlib.sha256(content).hexdigest() for name,content in sorted(data.items())}}
    raw=json.dumps(manifest,sort_keys=True,separators=(',',':')).encode()
    release_id=hashlib.sha256(raw).hexdigest()
    data['manifest.json']=raw
    output.mkdir(parents=True,exist_ok=True)
    target=output/('oria-hq-host-'+release_id+'.tar')
    with target.open('xb') as stream,tarfile.open(fileobj=stream,mode='w') as archive:
        for name,content in sorted(data.items()):
            entry=tarfile.TarInfo(name);entry.size=len(content);entry.mode=0o444;entry.uid=0;entry.gid=0;entry.mtime=0
            archive.addfile(entry,io.BytesIO(content))
    return {'releaseId':release_id,'archive':str(target.resolve()),'files':len(manifest['files']),'sha256':hashlib.sha256(target.read_bytes()).hexdigest()}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',required=True);args=parser.parse_args()
    print(json.dumps(release(Path(__file__).parent,args.output)))
