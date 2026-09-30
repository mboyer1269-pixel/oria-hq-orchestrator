"""Reconciliation must be bound to the observation and never relaunch."""
from contextlib import contextmanager
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock,patch
import reconcile_launch
from reconcile_launch import decide,deadline_exceeded,reconcile,retained_evidence

LAUNCH='11111111-1111-4111-8111-111111111111'
IMAGE='sha256:'+'a'*64
CLAIM={'launchId':LAUNCH,'missionId':'mission','workspaceId':'w','runnerId':'runner','imageDigest':IMAGE,
       'payloadHash':'c'*64,'commitSha':'b'*40,'startRequestedAt':'2026-09-30T12:00:00Z',
       'containerId':'d'*64,'state':'container_created'}
UNRECORDED={'containerId':None}
BOUND={'started':'bound','outcome':'present'}


@contextmanager
def unheld(path):
    """Coordination itself is qualified in test_launch_coordination."""
    yield path


def container(state,**extra):
    return {'state':state,'containerName':'hq-openhands-'+LAUNCH,'containerId':'d'*64,
            'exitCode':0,'startedAt':'2026-09-30T12:00:01Z','finishedAt':'2026-09-30T12:00:11Z',**extra}


def call(claim_state,mission,evidence=BOUND,timeout=60,**claim):
    merged={**CLAIM,**claim,'state':claim_state}
    return decide(claim={key:value for key,value in merged.items() if value is not None},
                  mission=mission,evidence=evidence,timeout_seconds=timeout)


class DecisionTests(unittest.TestCase):
    def test_terminal_and_unstarted_launches_need_no_transition(self):
        for state in ('execution_finished','cancelled','succeeded','failed'):
            self.assertEqual(call(state,container('exited')),
                             {'action':'none','state':'already_final','canonicalState':state,'identity':'bound'})
        self.assertEqual(call('claimed',{'state':'absent'}),
                         {'action':'none','state':'nothing_to_reconcile','canonicalState':'claimed','identity':'absent'})

    def test_created_running_and_stopped_containers_are_distinguished(self):
        self.assertEqual(call('container_created',container('created'))['action'],'record_cancelled')
        self.assertEqual(call('container_created',container('created'))['containerState'],'created')
        for state in ('running','paused','restarting','removing'):
            decision=call('container_created',container(state))
            self.assertEqual(decision['action'],'none')
            self.assertEqual(decision['reason'],'container_active')
            self.assertIn('deliberately',decision['nextAction'])
        recovered=call('start_requested',container('exited',exitCode=3))
        self.assertEqual(recovered['action'],'record_execution_finished')
        self.assertEqual(recovered['process'],{'exitCode':3,'containerStopped':True,'deadlineExceeded':False})

    def test_closure_reason_follows_the_canonical_stage(self):
        for state in ('container_created',):
            decision=call(state,{'state':'absent'})
            self.assertEqual((decision['action'],decision['reason']),('record_cancelled','interrupted_before_start'))
        for state in ('start_requested','running'):
            for mission in (container('dead'),):
                decision=call(state,mission)
                self.assertEqual((decision['action'],decision['reason']),('record_cancelled','result_unrecoverable'))
        stuck=call('start_requested',container('created'))
        self.assertEqual(stuck['action'],'none')
        self.assertEqual(stuck['reason'],'container_never_started')

    def test_creation_requested_records_the_container_it_can_prove(self):
        decision=call('creation_requested',container('created'),containerId=None)
        self.assertEqual(decision,{'action':'record_container_created','expected':'creation_requested',
                                   'containerId':'d'*64,'identity':'uncanonical'})
        self.assertEqual(call('creation_requested',container('exited'),containerId=None)['reason'],
                         'container_ran_without_recorded_creation')

    def test_foreign_unreadable_or_unidentified_evidence_blocks_every_transition(self):
        for evidence in ({'started':'foreign'},{'started':'unreadable'}):
            decision=call('container_created',container('created'),evidence=evidence)
            self.assertEqual(decision['action'],'none')
            self.assertTrue(decision['reason'].startswith('retained_evidence_'))
            self.assertIn('preserve',decision['nextAction'])
        for state in ('identity_mismatch','unknown'):
            decision=call('container_created',container(state))
            self.assertEqual(decision['action'],'none')
            self.assertIn(decision['reason'],('container_identity_mismatch','container_state_unknown'))
        self.assertEqual(call('reconciliation_required',container('exited'))['reason'],'unexpected_canonical_state')

    def test_a_result_is_never_recorded_on_guessed_timing_or_exit_code(self):
        self.assertIsNone(deadline_exceeded(CLAIM,container('exited',finishedAt='0001-01-01T00:00:00Z'),60))
        self.assertIsNone(deadline_exceeded({**CLAIM,'startRequestedAt':None},container('exited'),60))
        self.assertIsNone(deadline_exceeded(CLAIM,container('exited'),0))
        self.assertTrue(deadline_exceeded(CLAIM,container('exited',finishedAt='2026-09-30T12:02:00Z'),60))
        for mission in (container('exited',finishedAt='0001-01-01T00:00:00Z'),container('exited',exitCode=None)):
            decision=call('start_requested',mission)
            self.assertEqual(decision['action'],'none')
            self.assertIn(decision['reason'],('deadline_unknown','exit_code_unknown'))


class RetainedEvidenceTests(unittest.TestCase):
    def test_evidence_must_match_this_payload_and_commit(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'results').mkdir()
            self.assertEqual(retained_evidence(root,CLAIM),{'started':'absent'})
            started=root/'results'/'started.json'
            started.write_text(json.dumps({'payloadHash':CLAIM['payloadHash'],'commitSha':CLAIM['commitSha']}))
            self.assertEqual(retained_evidence(root,CLAIM),{'started':'bound','outcome':'absent'})
            (root/'results'/'outcome.json').write_text('{}')
            self.assertEqual(retained_evidence(root,CLAIM),{'started':'bound','outcome':'present'})
            started.write_text(json.dumps({'payloadHash':'f'*64,'commitSha':CLAIM['commitSha']}))
            self.assertEqual(retained_evidence(root,CLAIM),{'started':'foreign'})
            started.write_text('not json')
            self.assertEqual(retained_evidence(root,CLAIM),{'started':'unreadable'})


class ReconcileTests(unittest.TestCase):
    def run_reconcile(self,states,mission,claim=None,claims=None,**kwargs):
        """states: canonical states returned by successive reads."""
        self.recorded=[]
        sequence=list(states)
        def transition(expected,next_state,data):
            self.recorded.append((expected,next_state,data));return True
        def reader(command,include_config=False):
            def read():
                state=sequence.pop(0) if len(sequence)>1 else sequence[0]
                merged={**CLAIM,**(claim or {}),**((claims or {}).get(state,{})),'state':state}
                return {'claim':{k:v for k,v in merged.items() if v is not None},'config':{'timeoutSeconds':60}}
            return read
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'results').mkdir()
            (root/'results'/'started.json').write_text(json.dumps(
                {'payloadHash':CLAIM['payloadHash'],'commitSha':CLAIM['commitSha']}))
            watcher=kwargs.pop('observe_callable',None) or (lambda **_:mission)
            try:
                with patch.object(reconcile_launch,'lifecycle_transition',return_value=transition),patch.object(
                        reconcile_launch,'lifecycle_reader',side_effect=reader):
                    result=reconcile(command=['trusted'],job_root=root,observe=watcher,
                                     lease_file=root/'launch.lock',lease=unheld,**kwargs)
            finally:
                # Recorded even on refusal: a refused reconciliation must keep the work.
                self.preserved=(root/'results'/'started.json').is_file()
        return result

    def test_closing_an_interrupted_launch_uses_the_observed_identity_once(self):
        result=self.run_reconcile(['container_created','cancelled'],container('created'),
                                  claim={'containerId':'d'*64})
        self.assertEqual(len(self.recorded),1)
        expected,next_state,data=self.recorded[0]
        self.assertEqual((expected,next_state),('container_created','cancelled'))
        self.assertEqual(data['containerId'],'d'*64)
        self.assertEqual(data['observed']['reason'],'interrupted_before_start')
        self.assertEqual(data['observed']['containerState'],'created')
        self.assertEqual(result['canonicalState'],'cancelled')
        self.assertTrue(result['canonicalTerminal'])
        self.assertIs(result['jobFilesRemoved'],False)
        self.assertIs(result['automaticRetry'],False)
        self.assertIs(result['independentValidationPassed'],False)
        self.assertTrue(self.preserved)

    def test_recovering_a_finished_result_records_the_observed_process(self):
        result=self.run_reconcile(['start_requested','execution_finished'],container('exited',exitCode=0),
                                  claim={'containerId':'d'*64})
        self.assertEqual(len(self.recorded),1)
        expected,next_state,data=self.recorded[0]
        self.assertEqual((expected,next_state),('start_requested','execution_finished'))
        self.assertEqual(data['process'],{'exitCode':0,'containerStopped':True,'deadlineExceeded':False})
        self.assertEqual(result['canonicalState'],'execution_finished')
        self.assertEqual(result['steps'][0]['state'],'result_recovered')

    def test_an_already_final_launch_is_read_back_without_any_transition(self):
        result=self.run_reconcile(['execution_finished'],container('exited'))
        self.assertEqual(self.recorded,[])
        self.assertEqual(result['steps'][0]['state'],'already_final')
        self.assertTrue(result['canonicalTerminal'])

    def test_an_active_container_is_never_closed_and_keeps_the_gateway(self):
        result=self.run_reconcile(['container_created'],container('running'),gateway_root='/protected')
        self.assertEqual(self.recorded,[])
        self.assertEqual(result['steps'][0]['reason'],'container_active')
        self.assertFalse(result['canonicalTerminal'])
        self.assertEqual(result['gatewayRelease'],{'attempted':False,'reason':'canonical_state_not_terminal'})
        self.assertTrue(self.preserved)

    def test_an_unrecorded_creation_is_recorded_then_closed_in_one_bounded_pass(self):
        result=self.run_reconcile(['creation_requested','container_created','cancelled'],container('created'),
                                  claims={'creation_requested':UNRECORDED})
        self.assertEqual([step[1] for step in self.recorded],['container_created','cancelled'])
        self.assertEqual(result['canonicalState'],'cancelled')

    def test_a_closure_carries_the_identity_the_claim_holds_and_no_other(self):
        self.run_reconcile(['container_created','cancelled'],{'state':'absent'})
        expected,next_state,data=self.recorded[0]
        self.assertEqual(data['containerId'],'d'*64)
        self.assertEqual(data['observed']['containerState'],'absent')
        self.run_reconcile(['creation_requested'],{'state':'absent'},
                           claims={'creation_requested':UNRECORDED})
        self.assertEqual(self.recorded,[])



if __name__=='__main__':unittest.main()


class GatewayReleaseTests(unittest.TestCase):
    def test_release_requires_a_terminal_launch_and_verified_identity(self):
        from provider_gateway import release_gateway
        for state in ('claimed','creation_requested','container_created','start_requested','running'):
            with self.assertRaises(ValueError):
                release_gateway(root='/protected',launch_id=LAUNCH,canonical_state=state,
                                observed={'containerState':'exited','networkState':'present'})
        for observed in ({'containerState':'identity_mismatch','networkState':'present'},
                         {'containerState':'exited','networkState':'identity_mismatch'},
                         {'containerState':'unknown','networkState':'unknown','inspectionIncomplete':True}):
            with self.assertRaises(RuntimeError):
                release_gateway(root='/protected',launch_id=LAUNCH,canonical_state='cancelled',observed=observed)

    def test_an_active_agent_container_keeps_every_gateway_resource(self):
        released=Mock()
        with patch.object(reconcile_launch,'release_gateway',released):
            for state in ('running','paused','restarting','removing'):
                result=ReconcileTests.run_reconcile(ReconcileTests(),['execution_finished'],
                                                   container(state),gateway_root='/protected')
                self.assertEqual(result['gatewayRelease'],{'attempted':False,
                    'reason':'agent_container_not_releasable','observedContainerState':state})
        released.assert_not_called()


class NoEffectTests(unittest.TestCase):
    """Each of these reproduced a real defect before the fix; none may write."""

    def test_a_replacement_container_never_justifies_a_closure_or_a_release(self):
        replaced={'state':'created','containerName':'hq-openhands-'+LAUNCH,'containerId':'b'*64}
        for state in ('container_created','start_requested','running','creation_requested'):
            decision=call(state,replaced)
            self.assertEqual(decision['action'],'none',state)
            self.assertEqual(decision['identity'],'mismatch',state)
            self.assertEqual(decision['reason'],'container_identity_mismatch',state)
        # Even a terminal claim reports the divergence, so cleanup can refuse.
        self.assertEqual(call('execution_finished',replaced)['identity'],'mismatch')
        harness=ReconcileTests()
        result=ReconcileTests.run_reconcile(harness,['container_created'],replaced,gateway_root='/protected')
        self.assertEqual(harness.recorded,[])
        self.assertFalse(result['canonicalTerminal'])
        self.assertEqual(result['gatewayRelease'],{'attempted':False,'reason':'canonical_state_not_terminal'})
        self.assertTrue(harness.preserved)
        finished=ReconcileTests.run_reconcile(harness,['execution_finished'],replaced,gateway_root='/protected')
        self.assertEqual(harness.recorded,[])
        self.assertEqual(finished['gatewayRelease'],{'attempted':False,'reason':'agent_container_identity_mismatch'})

    def test_a_configuration_naming_another_launch_produces_no_effect(self):
        harness=ReconcileTests()
        with self.assertRaises(ValueError):
            ReconcileTests.run_reconcile(harness,['container_created'],container('created'),
                                         gateway_root='/protected',
                                         expect_launch_id='22222222-2222-4222-8222-222222222222')
        self.assertEqual(harness.recorded,[])
        self.assertTrue(harness.preserved)

    def test_an_uncertain_observation_keeps_every_resource(self):
        harness=ReconcileTests()
        for state in ('unknown','identity_mismatch'):
            result=ReconcileTests.run_reconcile(harness,['execution_finished'],container(state),
                                                gateway_root='/protected')
            self.assertEqual(harness.recorded,[])
            self.assertEqual(result['gatewayRelease']['attempted'],False)
            self.assertIn(result['gatewayRelease']['reason'],
                          ('agent_container_not_releasable','agent_container_identity_mismatch'))

    def test_a_container_appearing_after_the_record_is_reported_not_hidden(self):
        harness=ReconcileTests()
        observations=[{'state':'absent','containerName':'hq-openhands-'+LAUNCH},
                      container('running',containerId='b'*64)]
        def observe(**_):return observations.pop(0) if len(observations)>1 else observations[0]
        result=ReconcileTests.run_reconcile(harness,['start_requested'],None,
                                            gateway_root='/protected',observe_callable=observe)
        self.assertEqual(harness.recorded,[])
        self.assertEqual(result['steps'][0]['reason'],'docker_effect_unresolved')
        self.assertFalse(result['canonicalTerminal'])
        self.assertEqual(result['canonicalState'],'start_requested')
        self.assertEqual(result['gatewayRelease'],{'attempted':False,'reason':'canonical_state_not_terminal'})
