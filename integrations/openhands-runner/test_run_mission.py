import copy
import json
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from dossier import digest
from run_mission import execute

class MissionEntryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.repo=self.root/'repo';self.repo.mkdir()
        self.results=self.root/'results';self.results.mkdir()
        self.git('init');self.git('-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','--allow-empty','-m','fixture')
        self.data=json.loads((Path(__file__).parent/'fixtures/hq-memory-dossier.json').read_text(encoding='utf-8'))
        self.data['source']['commitSha']=self.git('rev-parse','HEAD')
        self.data['payloadHash']=digest({k:v for k,v in self.data.items() if k not in ('payloadHash','idempotencyKey')})
        self.agent=Mock();self.conversation=Mock(state=SimpleNamespace(execution_status=SimpleNamespace(value='finished')))
        self.factory=Mock(return_value=self.conversation)

    def git(self,*args):
        return subprocess.check_output(['git','-C',str(self.repo),*args],text=True,stderr=subprocess.DEVNULL).strip()

    def run_job(self):
        return execute(self.data,workspace_id=self.data['mission']['workspaceId'],checkout=self.repo,
                       results=self.results,agent_factory=self.agent,conversation_factory=self.factory)

    def test_return_is_not_success_and_replay_does_not_call_agent(self):
        result=self.run_job()
        self.assertEqual(result['state'],'agent_returned');self.assertFalse(result['independentValidationPassed'])
        self.assertFalse(result['hardTokenLimitEnforced'])
        self.assertEqual(self.factory.call_args.kwargs['max_iteration_per_run'],self.data['budget']['maxIterations'])
        self.assertFalse(self.factory.call_args.kwargs['delete_on_close'])
        self.assertIn(self.data['memory']['snapshotHash'],self.conversation.send_message.call_args.args[0])
        self.assertEqual(json.loads((self.results/'outcome.json').read_text()),result)
        with self.assertRaises(FileExistsError):self.run_job()
        self.agent.assert_called_once();self.conversation.run.assert_called_once()

    def test_dirty_checkout_denied_before_agent_or_start_marker(self):
        (self.repo/'changed.txt').write_text('unreviewed')
        with self.assertRaises(ValueError):self.run_job()
        self.agent.assert_not_called();self.assertFalse((self.results/'started.json').exists())

    def test_error_preserved_and_not_retried(self):
        self.conversation.run.side_effect=RuntimeError('synthetic error')
        with self.assertRaises(RuntimeError):self.run_job()
        self.assertEqual(json.loads((self.results/'outcome.json').read_text())['state'],'execution_error')
        self.conversation.close.assert_called_once()
        with self.assertRaises(FileExistsError):self.run_job()
        self.conversation.run.assert_called_once()

    def test_tampered_dossier_denied_before_agent(self):
        self.data['mission']['objective']='changed'
        with self.assertRaises(ValueError):self.run_job()
        self.agent.assert_not_called()

    def test_missing_runtime_records_failure_without_retry(self):
        with patch.dict('sys.modules', {'openhands.sdk': None}):
            with self.assertRaises(ModuleNotFoundError):
                execute(self.data, workspace_id=self.data['mission']['workspaceId'],
                        checkout=self.repo, results=self.results, agent_factory=self.agent)
        outcome=json.loads((self.results/'outcome.json').read_text())
        self.assertEqual(outcome['state'], 'execution_error')
        self.assertFalse(outcome['independentValidationPassed'])
        self.agent.assert_not_called()
        with self.assertRaises(FileExistsError):self.run_job()
        self.agent.assert_not_called()

if __name__=='__main__':unittest.main()
