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
        with patch('run_host_job.load_configuration',return_value=(('/usr/bin/node','protected-script'),root,review,None)),patch(
            'run_host_job.lifecycle_reader',return_value=lambda:dict(claim=claim,config=dict(imageDigest='pinned',timeoutSeconds=60))),patch(
            'run_host_job.run_permission_job',worker):
            await execute_configuration('/protected.json')
        args=worker.call_args.kwargs
        self.assertEqual(args['job'],dict(launchId=launch,missionId='mission',workspaceId='workspace',runnerId='runner',imageDigest='pinned',timeoutSeconds=60))
        self.assertEqual(args['review_socket'],review)
        # Default configuration stays offline: no gateway root ever reaches the worker.
        self.assertNotIn('gateway_root',args);self.assertNotIn('authorization',args)

    async def test_configured_authorization_and_gateway_root_reach_the_worker(self):
        launch='11111111-1111-4111-8111-111111111111'
        root=Path('/srv/jobs')/launch
        review=Path('/run/oria-hq-control')/launch/'review.sock'
        provider={'profileId':'claude-subscription-v1','policySha256':'a'*64,
                  'policyRoot':'/etc/oria-hq/provider-policies','gatewayRoot':'/srv/oria-hq-gateways'}
        claim=dict(state='claimed',launchId=launch,missionId='mission',workspaceId='workspace',runnerId='runner')
        worker=AsyncMock(return_value={'state':'execution_finished'})
        with patch('run_host_job.load_configuration',return_value=(('/usr/bin/node','protected-script'),root,review,provider)),patch(
            'run_host_job.lifecycle_reader',return_value=lambda:dict(claim=claim,config=dict(imageDigest='pinned',timeoutSeconds=60))),patch(
            'run_host_job.run_permission_job',worker):
            await execute_configuration('/protected.json')
        args=worker.call_args.kwargs
        self.assertEqual(args['gateway_root'],provider['gatewayRoot'])
        self.assertEqual(args['authorization'],provider)
        # The approved policy travels as operator configuration only; the canonical
        # mission identity and the shared deadline keep their single source.
        self.assertEqual(args['job']['launchId'],launch)
        self.assertEqual(args['job']['timeoutSeconds'],60)

    async def test_completed_claim_or_wrong_directory_never_dispatches(self):
        for state in ('execution_finished','claimed'):
            worker=AsyncMock()
            with patch('run_host_job.load_configuration',return_value=(('/trusted',),Path('/jobs/wrong'),Path('/control/wrong/review.sock'),None)),patch(
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
            command,_,_,provider=load_configuration(str(config));self.assertEqual(command,(str(executable),))
            self.assertIsNone(provider)
            config.chmod(0o666)
            with self.assertRaises(ValueError):load_configuration(str(config))
            config.chmod(0o600);(control/'review.sock').touch()
            with self.assertRaises(ValueError):load_configuration(str(config))
            (control/'review.sock').unlink()
            gateway=root/'gateways';gateway.mkdir();policies=root/'policies';policies.mkdir()
            approved={'profileId':'claude-subscription-v1','policySha256':'a'*64,'policyRoot':str(policies),'gatewayRoot':str(gateway)}
            base=dict(lifecycleCommand=[str(executable)],jobRoot=str(job),reviewSocket=str(control/'review.sock'))
            config.write_text(json.dumps({**base,'providerExecution':approved}))
            self.assertEqual(load_configuration(str(config))[3],approved)
            # A gateway root sharing the agent job or the owner review subtree, or a
            # malformed authorization, never produces an executable configuration.
            for broken in ({**approved,'gatewayRoot':str(job)},{**approved,'gatewayRoot':str(control)},
                           {**approved,'policySha256':'invalid'},{**approved,'extra':1},
                           {'profileId':approved['profileId'],'policySha256':approved['policySha256']}):
                config.write_text(json.dumps({**base,'providerExecution':broken}))
                with self.assertRaises(ValueError):load_configuration(str(config))


if __name__=='__main__':unittest.main()
