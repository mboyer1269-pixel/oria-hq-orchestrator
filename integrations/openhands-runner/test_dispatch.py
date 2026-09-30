import unittest
from unittest.mock import Mock
from dispatch import dispatch


class DispatchTests(unittest.TestCase):
    def setUp(self):
        self.transitions=[]
        self.state='claimed'
        def transition(before,after,data):
            if self.state!=before:return False
            self.state=after;self.transitions.append((before,after,data));return True
        self.create=Mock(return_value={'containerId':'a'*64,'containerName':'fixture'})
        self.run=Mock(return_value={'exitCode':0,'containerStopped':True})
        self.args=dict(transition=transition,launch_id='fixture',image_digest='fixture',
                       workspace_id='fixture',job_root='fixture',timeout_seconds=30,
                       create=self.create,run=self.run)

    def test_repeat_cannot_start_twice_or_claim_success(self):
        result=dispatch(**self.args)
        self.assertEqual(result['state'],'execution_finished')
        self.assertFalse(result['independentValidationPassed'])
        self.assertEqual(dispatch(**self.args)['state'],'not_acquired')
        self.create.assert_called_once();self.run.assert_called_once()

    def test_unknown_container_record_write_prevents_start(self):
        self.args['transition']=Mock(side_effect=[True,TimeoutError('unknown')])
        self.assertEqual(dispatch(**self.args)['state'],'reconciliation_required')
        self.run.assert_not_called();self.create.assert_called_once()

    def test_creation_timeout_never_retries(self):
        self.create.side_effect=TimeoutError('unknown creation')
        self.assertEqual(dispatch(**self.args)['state'],'reconciliation_required')
        self.assertEqual(self.state,'creation_requested')
        self.assertEqual(dispatch(**self.args)['state'],'not_acquired')
        self.create.assert_called_once();self.run.assert_not_called()

    def test_slow_creation_spends_same_deadline_and_expiry_never_starts(self):
        for elapsed in (7,31):
            self.setUp();clock=[100.0]
            def create(**kwargs):
                clock[0]+=elapsed
                return {'containerId':'a'*64,'containerName':'fixture'}
            self.args.update(create=create,clock=lambda:clock[0])
            result=dispatch(**self.args)
            if elapsed==31:
                self.assertTrue(result['deadlineExceeded']);self.assertFalse(result['started']);self.run.assert_not_called()
                self.assertEqual(self.state,'container_created')
            else:
                self.assertEqual(self.run.call_args.kwargs['deadline_monotonic'],130.0)

    def test_final_write_uncertainty_does_not_repeat_execution(self):
        self.args['transition']=Mock(side_effect=[True,True,True,False])
        self.assertEqual(dispatch(**self.args)['state'],'reconciliation_required')
        self.run.assert_called_once()

    def test_registered_session_can_finish_from_canonical_running_state(self):
        def run(**kwargs):
            self.state='running'
            return {'exitCode':0,'containerStopped':True}
        self.run.side_effect=run
        self.args['read_claim']=lambda:dict(state=self.state,containerId='a'*64)
        result=dispatch(**self.args)
        self.assertEqual(result['state'],'execution_finished')
        self.assertEqual(self.transitions[-1][0],'running')
        self.assertFalse(result['independentValidationPassed'])

    def test_changed_identity_or_cancelled_claim_is_not_overwritten(self):
        for claim in ({'state':'running','containerId':'b'*64},
                      {'state':'cancelled','containerId':'a'*64},None):
            with self.subTest(claim=claim):
                self.setUp()
                self.args['read_claim']=lambda:claim
                result=dispatch(**self.args)
                self.assertEqual(result['state'],'reconciliation_required')
                self.assertEqual(self.state,'start_requested')
                self.run.assert_called_once()

    def test_unknown_canonical_read_never_repeats_execution(self):
        self.args['read_claim']=Mock(side_effect=TimeoutError('unknown read'))
        self.assertEqual(dispatch(**self.args)['state'],'reconciliation_required')
        self.assertEqual(dispatch(**self.args)['state'],'not_acquired')
        self.run.assert_called_once()

if __name__=='__main__':unittest.main()
