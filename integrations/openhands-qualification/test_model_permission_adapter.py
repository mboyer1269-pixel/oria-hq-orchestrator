"""Real SDK execute path / fake ACP, plus isolated cancellation injection."""
import asyncio
import copy
import json
import os
import unittest
from unittest.mock import patch
from openhands.sdk.conversation.exceptions import ConversationRunError
from test_model_selection_probe import ModelSelectionProbeTests
from model_permission_adapter_v1 import qualification_factory, check_compatibility, ModelPermissionAdapterV1
from run_mission import execute
from dossier import digest

class ModelPermissionTests(unittest.TestCase):
    setUp = ModelSelectionProbeTests.setUp

    def run_case(self, scenario='accept', admit=lambda: True, callback=None):
        self.results = self.root / 'results'; self.results.mkdir(exist_ok=True)
        original = copy.deepcopy(self.dossier)
        factory = qualification_factory(dossier=self.dossier, requested_model='fixture-model-2',
            log=self.log, results=self.results, admit=admit, scenario=scenario,
            timeout=0.3, baseline=os.environ.get('ORIA_ADAPTER_BASELINE') == '1')
        try:
            execute(self.dossier, workspace_id=self.dossier['mission']['workspaceId'],
                    checkout=self.checkout, results=self.results, agent_factory=factory,
                    permission_callback=callback)
        except ConversationRunError: pass
        self.assertEqual(original, self.dossier)
        wire = [json.loads(line) for line in self.log.read_text().splitlines()]
        receipts = [json.loads(p.read_text()) for p in self.results.glob('model-receipt-*.json')]
        return wire, receipts

    def test_exact_ack_budget_metadata_default_deny_memory_and_receipt(self):
        wire, receipts = self.run_case()
        prompt = next(i for i,m in enumerate(wire) if m.get('method') == 'session/prompt')
        selection = max(i for i,m in enumerate(wire) if m.get('method') == 'session/set_config_option')
        self.assertLess(selection, prompt)
        self.assertEqual(wire[selection]['params']['value'], 'fixture-model-2')
        self.assertEqual(len(receipts), 1)
        receipt = receipts[0]
        self.assertEqual(receipt['qualificationBindingHash'], digest([self.dossier['payloadHash'],
            'fixture-model-2', self.dossier['memory']['snapshotHash']]))
        self.assertFalse(receipt['providerModelIndependentlyVerified'])
        text = '\n'.join(x.get('text','') for x in wire[prompt]['params']['prompt'])
        self.assertIn(json.dumps(self.dossier['memory'], ensure_ascii=False), text)
        session = next(m for m in wire if m.get('method') == 'session/new')
        options = session['params']['_meta']['claudeCode']['options']
        self.assertEqual(options['maxTurns'], self.dossier['budget']['maxIterations'])
        self.assertEqual(options['maxBudgetUsd'], self.dossier['budget']['maxCostCents']/100)
        self.assertFalse(options['allowDangerouslySkipPermissions'])
        permission = next(m for m in wire if m.get('id') == 'permission-probe')
        self.assertEqual(permission['result']['outcome'], {'outcome':'cancelled'})

    def test_admission_denied_before_prompt(self):
        wire, receipts = self.run_case(admit=lambda: False)
        self.assertFalse(any(m.get('method') == 'session/prompt' for m in wire)); self.assertEqual(receipts, [])

    def test_revoked_budget_after_selection_before_prompt(self):
        decisions = iter([True, False])
        wire, receipts = self.run_case(admit=lambda: next(decisions))
        self.assertFalse(any(m.get('method') == 'session/prompt' for m in wire)); self.assertEqual(receipts, [])

    def test_exact_ack_refusal(self):
        wire, receipts = self.run_case(scenario='mismatch')
        self.assertFalse(any(m.get('method') == 'session/prompt' for m in wire)); self.assertEqual(receipts, [])

    def test_timeout_and_no_automatic_restart(self):
        wire, receipts = self.run_case(scenario='timeout')
        self.assertFalse(any(m.get('method') == 'session/prompt' for m in wire)); self.assertEqual(receipts, [])
        before = self.log.read_bytes()
        with self.assertRaises(FileExistsError):
            execute(self.dossier, workspace_id=self.dossier['mission']['workspaceId'],
                    checkout=self.checkout, results=self.results,
                    agent_factory=lambda **kw: self.fail('No instantiate after started marker'))
        self.assertEqual(before, self.log.read_bytes())
        self.assertEqual(json.loads((self.results/'outcome.json').read_text())['state'], 'execution_error')

    def test_disconnect_before_prompt(self):
        wire, receipts = self.run_case(scenario='disconnect')
        self.assertFalse(any(m.get('method') == 'session/prompt' for m in wire)); self.assertEqual(receipts, [])

    def test_permission_callback_error_denies_tool(self):
        async def callback(**kwargs): raise RuntimeError('Synthetic authority unavailable')
        wire, receipts = self.run_case(callback=callback)
        self.assertEqual(next(m for m in wire if m.get('id') == 'permission-probe')['result']['outcome'], {'outcome':'cancelled'})
        self.assertEqual(len(receipts), 1)

    def test_prompt_timeout_preserves_acknowledgement_not_success(self):
        wire, receipts = self.run_case(scenario='prompt-timeout')
        self.assertEqual(sum(m.get('method') == 'session/prompt' for m in wire), 1)
        self.assertEqual(len(receipts), 1)
        self.assertEqual(receipts[0]['status'], 'acknowledged_before_prompt')
        self.assertFalse(receipts[0]['providerModelIndependentlyVerified'])
        self.assertEqual(json.loads((self.results/'outcome.json').read_text())['state'], 'execution_error')

    def test_invalid_budget_never_starts_peer(self):
        self.dossier['budget']['maxCostCents'] = 0
        self.dossier['payloadHash'] = digest({k:v for k,v in self.dossier.items()
                                             if k not in ('payloadHash','idempotencyKey')})
        from dossier import InvalidDossier
        with self.assertRaises(InvalidDossier): self.run_case()
        self.assertFalse(self.log.exists())

    def test_permission_callback_timeout_denies_tool(self):
        async def callback(**kwargs):
            raise asyncio.TimeoutError('Synthetic authority deadline')
        wire, receipts = self.run_case(callback=callback)
        self.assertEqual(next(m for m in wire if m.get('id') == 'permission-probe')['result']['outcome'], {'outcome':'cancelled'})
        self.assertEqual(len(receipts), 1)

    def test_unsafe_policy_and_mode_rejected(self):
        from pydantic import ValidationError
        for changes in ({'hq_permission_policy':'upstream-auto-allow'},
                        {'acp_session_mode':'bypassPermissions'}):
            with self.assertRaises(ValidationError):
                ModelPermissionAdapterV1(hq_max_iterations=2, hq_max_cost_cents=100,
                                         acp_command=['unused'], **changes)

    def test_incompatible_source_rejected(self):
        with patch('model_permission_adapter_v1.SDK_SHA', '0'*64):
            with self.assertRaisesRegex(RuntimeError, 'Unqualified SDK source'): check_compatibility()
        self.assertFalse(self.log.exists())

    def test_cancellation_during_selection_invalidates_same_instance(self):
        async def case():
            agent = ModelPermissionAdapterV1(hq_max_iterations=2,hq_max_cost_cents=100,acp_command=['unused'])
            agent._admit = lambda: True
            entered = asyncio.Event()
            async def wait_selection(self):
                entered.set(); await asyncio.Future()
            with patch.object(ModelPermissionAdapterV1, 'select_exact_model', wait_selection):
                task = asyncio.create_task(agent._do_acp_prompt([]))
                await entered.wait(); task.cancel()
                with self.assertRaises(asyncio.CancelledError): await task
                self.assertIsNone(agent._selection_receipt)
                with self.assertRaisesRegex(RuntimeError, 'Reconciliation required'): await agent._do_acp_prompt([])
        asyncio.run(case())

if __name__ == '__main__': unittest.main()
