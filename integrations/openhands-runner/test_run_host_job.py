import unittest
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock,patch
from run_host_job import execute_configuration,unique_object,load_configuration


class HostEntryTests(unittest.IsolatedAsyncioTestCase):
    async def test_worker_receives_only_canonical_execution_parameters(self):
        launch='11111111-1111-4111-8111-111111111111'
        root=Path('/srv/jobs')/launch
        review=Path('/run/oria-hq-control')/launch/'review.sock'
        claim=dict(state='claimed',launchId=launch,missionId='mission',workspaceId='workspace',runnerId='runner')
        worker=AsyncMock(return_value={'state':'execution_finished'})
        with patch('run_host_job.load_configuration',return_value=(('/usr/bin/node','protected-script'),root,review)),patch(
            'run_host_job.lifecycle_reader',return_value=lambda:dict(claim=claim,config=dict(imageDigest='pinned',timeoutSeconds=60))),patch(
            'run_host_job.run_permission_job',worker):
            await execute_configuration('/protected.json')
        args=worker.call_args.kwargs
        self.assertEqual(args['job'],dict(launchId=launch,missionId='mission',workspaceId='workspace',runnerId='runner',imageDigest='pinned',timeoutSeconds=60))
        self.assertEqual(args['review_socket'],review)

    async def test_completed_claim_or_wrong_directory_never_dispatches(self):
        for state in ('execution_finished','claimed'):
            worker=AsyncMock()
            with patch('run_host_job.load_configuration',return_value=(('/trusted',),Path('/jobs/wrong'),Path('/control/wrong/review.sock'))),patch(
                'run_host_job.lifecycle_reader',return_value=lambda:dict(claim=dict(state=state,launchId='canonical'),config={})),patch(
                'run_host_job.run_permission_job',worker):
                if state=='claimed':
                    with self.assertRaises(ValueError):await execute_configuration('/protected')
                else:self.assertEqual((await execute_configuration('/protected'))['state'],'not_acquired')
            worker.assert_not_called()

    def test_duplicate_keys_refused(self):
        with self.assertRaises(ValueError):unique_object([('jobRoot','a'),('jobRoot','b')])

    @unittest.skipUnless(os.name=='posix' and getattr(os,'geteuid',lambda:1)()==0,'Linux root filesystem qualification')
    def test_real_host_paths_reject_writable_config_and_existing_socket(self):
        with tempfile.TemporaryDirectory(dir='/root',prefix='hq-entry-test-') as folder:
            root=Path(folder);job=root/'job';job.mkdir();control=root/'control';control.mkdir()
            executable=root/'trusted';executable.write_text('fixture');executable.chmod(0o700)
            config=root/'operator.json'
            config.write_text(json.dumps(dict(lifecycleCommand=[str(executable)],jobRoot=str(job),reviewSocket=str(control/'review.sock'))))
            command,_,_=load_configuration(str(config));self.assertEqual(command,(str(executable),))
            config.chmod(0o666)
            with self.assertRaises(ValueError):load_configuration(str(config))
            config.chmod(0o600);(control/'review.sock').touch()
            with self.assertRaises(ValueError):load_configuration(str(config))


if __name__=='__main__':unittest.main()
