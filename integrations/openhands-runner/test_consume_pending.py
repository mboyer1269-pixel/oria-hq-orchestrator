import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
import os
import signal
from unittest.mock import patch,AsyncMock
from consume_pending import discover,consume,main


class ConsumerTests(unittest.TestCase):
    def setUp(self):
        self.job=dict(missionId='11111111-1111-4111-8111-111111111111',launchId='22222222-2222-4222-8222-222222222222',payloadHash='a'*64,authorizationExpiresAt='2026-09-30T12:00:00Z')
        self.config=dict(bridgeCommand=['/trusted/node'],bridgeScriptsRoot='/hq/src/scripts',bridgeProfile='/protected/profile.json')

    def test_discovery_only_accepts_bounded_unique_job_references(self):
        valid=dict(status='ready',jobs=[self.job],nextAfterMissionId=None)
        for data,ok in [(valid,True),({**valid,'jobs':[self.job,self.job]},False),({**valid,'jobs':[{**self.job,'sourceRoot':'/injected'}]},False),({**valid,'jobs':[{**self.job,'launchId':'../escape'}]},False),({**valid,'jobs':[self.job]*21},False)]:
            with patch('consume_pending.subprocess.run',return_value=SimpleNamespace(returncode=0,stdout=json.dumps(data))) as run:
                if ok:self.assertEqual(discover(self.config)['jobs'],[self.job])
                else:
                    with self.assertRaises(ValueError):discover(self.config)
                self.assertEqual(run.call_args.kwargs['timeout'],45)
                self.assertNotIn('shell',run.call_args.kwargs)

    def test_cursor_must_advance_and_subprocess_failure_never_looks_empty(self):
        data=dict(status='ready',jobs=[],nextAfterMissionId=self.job['missionId'])
        with patch('consume_pending.subprocess.run',return_value=SimpleNamespace(returncode=0,stdout=json.dumps(data))):
            with self.assertRaises(ValueError):discover(self.config,self.job['missionId'])
        with patch('consume_pending.subprocess.run',return_value=SimpleNamespace(returncode=2,stdout='{}')):
            with self.assertRaises(RuntimeError):discover(self.config)

    def test_discovered_identity_binds_preparation_and_partial_attempt_never_repeats(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            config={**self.config,'hostConfigRoot':root,'bridgeConfigRoot':'/protected','profile':{'context':{'workspaceId':'w','actorId':'owner','runnerId':'r'},'config':{'fixture':True}},'registryFile':root/'sources.json','jobsRoot':root/'jobs','controlRoot':root/'control'}
            execute=AsyncMock(return_value={'state':'execution_finished'})
            with patch('consume_pending.prepare_configured_project',return_value={'operatorConfig':'/prepared/operator.json'}) as prepare,patch('consume_pending.execute_configuration',execute):
                self.assertEqual(consume(config,self.job),{'state':'execution_finished'})
                self.assertEqual(prepare.call_args.kwargs['expected_payload_hash'],self.job['payloadHash'])
                packet=json.loads((root/self.job['launchId']/'lifecycle.json').read_text())
                self.assertEqual(packet['context'],config['profile']['context']);self.assertEqual(packet['launchId'],self.job['launchId'])
                self.assertEqual(prepare.call_args.kwargs['command'][-1],f"/protected/{self.job['launchId']}/lifecycle.json")
                with self.assertRaises(FileExistsError):consume(config,self.job)
                prepare.assert_called_once();execute.assert_awaited_once()

    @unittest.skipUnless(os.name=='posix','POSIX consumer lock')
    def test_consumer_stops_batch_on_failed_process(self):
        with tempfile.TemporaryDirectory() as folder:
            with patch('sys.argv',['consumer','--config','fixture']),patch('consume_pending.signal.signal'),patch('consume_pending.load_config',return_value={'hostConfigRoot':Path(folder)}),patch('consume_pending.discover',return_value={'jobs':[self.job,{**self.job,'launchId':'33333333-3333-4333-8333-333333333333'}],'nextAfterMissionId':None}),patch('consume_pending.consume',return_value={'state':'execution_finished','process':{'exitCode':1}}) as execute,patch('builtins.print'):
                self.assertEqual(main(),3);execute.assert_called_once()

    @unittest.skipUnless(os.name=='posix','POSIX consumer signal handling')
    def test_watch_stop_finishes_current_job_without_starting_next(self):
        with tempfile.TemporaryDirectory() as folder:
            handlers={}
            def execute(*_):handlers[signal.SIGTERM]();return {'state':'execution_finished','process':{'exitCode':0}}
            with patch('sys.argv',['consumer','--config','fixture','--watch']),patch('consume_pending.signal.signal',side_effect=lambda sig,handler:handlers.update({sig:handler})),patch('consume_pending.load_config',return_value={'hostConfigRoot':Path(folder)}),patch('consume_pending.discover',return_value={'jobs':[self.job,self.job],'nextAfterMissionId':None}),patch('consume_pending.consume',side_effect=execute) as run,patch('builtins.print'):
                self.assertEqual(main(),0);run.assert_called_once()


if __name__=='__main__':unittest.main()
