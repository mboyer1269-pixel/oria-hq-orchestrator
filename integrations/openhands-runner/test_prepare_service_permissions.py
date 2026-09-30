import os
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch
from prepare_host_job import prepare_host_job


@unittest.skipUnless(os.name=='posix' and getattr(os,'geteuid',lambda:1)()==0,'Linux root service permissions')
class ServicePreparationPermissions(unittest.TestCase):
    def test_restrictive_service_umask_preserves_agent_read_and_private_config(self):
        with tempfile.TemporaryDirectory(dir='/root',prefix='hq-umask-test-') as folder:
            base=Path(folder);source=base/'source';source.mkdir();jobs=base/'jobs';jobs.mkdir();controls=base/'controls';controls.mkdir()
            launch='11111111-1111-4111-8111-111111111111'
            claim=dict(launchId=launch,state='claimed',workspaceId='w',missionId='mission',payloadHash='a'*64,commitSha='b'*40)
            dossier={'mission':{'id':'mission'}}
            def checkout(**args):
                target=args['server_root']/args['job_name'];target.mkdir();return {'checkout':str(target)}
            previous=os.umask(0o077)
            try:
                with patch('prepare_host_job.lifecycle_reader',return_value=lambda:dict(claim=claim,config={'executorVersion':'1.50.0'},dossier=dossier)),patch('prepare_host_job.prepare',return_value={'payloadHash':'a'*64,'commitSha':'b'*40}),patch('prepare_host_job.prepare_workspace',side_effect=checkout):
                    prepare_host_job(command=[str(Path('/usr/bin/true').resolve())],source=source,jobs_root=jobs,control_root=controls)
            finally:os.umask(previous)
            root=jobs/launch
            for target,mode in [(root,0o755),(controls/launch,0o755),(root/'ipc',0o755),(root/'dossier.json',0o444),(root/'operator.json',0o600),(root/'results',0o700)]:
                self.assertEqual(stat.S_IMODE(target.stat().st_mode),mode,str(target))
            self.assertEqual((root/'results').stat().st_uid,10001)
            self.assertEqual((root/'dossier.json').stat().st_uid,0)


if __name__=='__main__':unittest.main()
