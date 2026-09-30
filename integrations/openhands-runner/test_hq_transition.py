import json
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from hq_transition import lifecycle_transition, lifecycle_reader, consume_tool_decision


class TransitionTests(unittest.TestCase):
    @patch('hq_transition.subprocess.run')
    def test_read_requires_confirmed_observation_and_never_retries(self,run):
        claim={'state':'running','containerId':'a'*64}
        run.return_value=SimpleNamespace(returncode=0,stdout=json.dumps({'status':'observed','claim':claim}))
        self.assertEqual(lifecycle_reader(['node'])(),claim)
        self.assertEqual(json.loads(run.call_args.kwargs['input']),{'next':'read'})
        for value in ({'status':'recorded','claim':claim},{'status':'observed','claim':None}):
            run.reset_mock()
            run.return_value=SimpleNamespace(returncode=0,stdout=json.dumps(value))
            with self.assertRaises(RuntimeError):lifecycle_reader(['node'])()
            run.assert_called_once()

    @patch('hq_transition.subprocess.run')
    def test_consumption_allows_only_exact_offered_once_option(self,run):
        request={'options':[{'optionId':'once','kind':'allow_once'}]}
        for option,expected in [('once','selected'),('other','cancelled')]:
            run.return_value=SimpleNamespace(returncode=0,stdout=json.dumps({'status':'permission_response','outcome':{'outcome':'selected','optionId':option}}))
            self.assertEqual(consume_tool_decision(['node'],request)['outcome']['outcome'],expected)
        run.side_effect=TimeoutError('unknown')
        self.assertEqual(consume_tool_decision(['node'],request)['outcome']['outcome'],'cancelled')

    @patch('hq_transition.subprocess.run')
    def test_wrong_recorded_session_is_not_accepted(self,run):
        run.return_value=SimpleNamespace(returncode=0,stdout=json.dumps({'status':'recorded','claim':{'state':'running','containerId':'a'*64,'sessionId':'other'}}))
        with self.assertRaises(RuntimeError):
            lifecycle_transition(['node'])('start_requested','running',{'containerId':'a'*64,'sessionId':'expected'})

    @patch('hq_transition.subprocess.run')
    def test_only_contract_fields_are_sent(self,run):
        run.return_value=SimpleNamespace(returncode=0,stdout=json.dumps({'status':'recorded','claim':{'state':'execution_finished','containerId':'a'*64}}))
        callback=lifecycle_transition(['node','trusted.mjs','job.json'])
        self.assertTrue(callback('start_requested','execution_finished',{'containerId':'a'*64,'state':'ignored','process':{'exitCode':0,'containerStopped':True,'deadlineExceeded':False,'elapsedSeconds':1}}))
        sent=json.loads(run.call_args.kwargs['input'])
        self.assertNotIn('state',sent);self.assertNotIn('elapsedSeconds',sent['process'])

    @patch('hq_transition.subprocess.run')
    def test_unknown_response_never_retries(self,run):
        for stdout,code in [('invalid',0),('{"status":"recorded"}',0),('{}',3)]:
            run.reset_mock();run.return_value=SimpleNamespace(returncode=code,stdout=stdout)
            with self.assertRaises(RuntimeError):lifecycle_transition(['node'])('claimed','creation_requested',{})
            run.assert_called_once()

if __name__=='__main__':unittest.main()
