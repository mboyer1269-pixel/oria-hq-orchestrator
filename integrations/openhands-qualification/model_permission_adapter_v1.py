"""Qualification-only boundary for SDK 1.50.0 + existing HQ factory patches.

No public pre-prompt selection interceptor exists in this pinned SDK. All private
hook coupling is here; unexpected SDK source fails closed before peer creation.
Caller authorization is simulated, NOT a replacement for durable host authority.
"""
import asyncio
import hashlib
import importlib.metadata
import inspect
import json
import os
from pathlib import Path
import sys
from pydantic import PrivateAttr
from openhands.sdk.agent import ACPAgent
from model_selection_probe import _ExactModelProbe
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'openhands-permission-extension'))
from budget_agent import BudgetPermissionAgent

SDK_SHA = '0c95575be6fddaef11a98ff645a42b2cba3441be244a78a7c0e443aff4513b23'
BOUNDARY = 'hq-model-permission-qualification-v1'


def check_compatibility():
    for package, expected in [('openhands-sdk', '1.50.0'), ('agent-client-protocol', '0.12.1')]:
        if importlib.metadata.version(package) != expected:
            raise RuntimeError('Unqualified dependency version: ' + package)
    source = Path(inspect.getfile(ACPAgent)).read_bytes()
    if hashlib.sha256(source).hexdigest() != SDK_SHA:
        raise RuntimeError('Unqualified SDK source: both existing HQ factory patches required')
    if tuple(inspect.signature(ACPAgent._do_acp_prompt).parameters) != ('self', 'prompt_blocks'):
        raise RuntimeError('Unqualified prompt hook')


class ModelPermissionAdapterV1(BudgetPermissionAgent, _ExactModelProbe):
    _admit: object = PrivateAttr(default=None)
    _receipt_directory: Path | None = PrivateAttr(default=None)
    _failed: bool = PrivateAttr(default=False)
    _sequence: int = PrivateAttr(default=0)

    async def _do_acp_prompt(self, prompt_blocks):
        self._selection_receipt = None
        if self._failed:
            raise RuntimeError('Reconciliation required; no automatic retry')
        try:
            # Sync, trusted admission callback; no async authority or I/O here.
            if self._admit is None or self._admit() is not True:
                raise PermissionError('Launch permission or remaining budget denied')
            await self.select_exact_model()
            # Recheck revocation/budget after awaited model selection.
            if self._admit() is not True:
                raise PermissionError('Launch permission or remaining budget revoked')
            self._sequence += 1
            receipt = {**self._selection_receipt, 'boundary': BOUNDARY,
                       'sessionId': self._session_id, 'sequence': self._sequence,
                       'status': 'acknowledged_before_prompt',
                       'providerModelIndependentlyVerified': False}
            path = self._receipt_directory / ('model-receipt-%04d.json' % self._sequence)
            # Durable evidence before prompt. A crash here is ambiguous, NOT success.
            with path.open('x', encoding='utf-8') as out:
                json.dump(receipt, out); out.flush(); os.fsync(out.fileno())
            fd = os.open(self._receipt_directory, os.O_RDONLY | os.O_DIRECTORY)
            try: os.fsync(fd)
            finally: os.close(fd)
            self._selection_receipt = receipt
            # Skip the probe's second selection, retain the real SDK prompt path.
            return await BudgetPermissionAgent._do_acp_prompt(self, prompt_blocks)
        except BaseException as exc:
            self._failed = True
            self._selection_receipt = None
            # SDK retries OSError/connection failures; this boundary must instead
            # require reconciliation once admission/selection/prompt is uncertain.
            if isinstance(exc, Exception):
                raise RuntimeError('Qualification stopped; reconciliation required') from exc
            raise


def qualification_factory(*, dossier, requested_model, log, results, admit,
                          scenario='accept', timeout=1.0, baseline=False):
    """Factory injected into unchanged execute(); fixed synthetic executable only."""
    check_compatibility()
    from dossier import digest
    binding = {'payloadHash': dossier['payloadHash'], 'idempotencyKey': dossier['idempotencyKey'],
               'memorySnapshotHash': dossier.get('memory', {}).get('snapshotHash')}
    binding['qualificationBindingHash'] = digest([binding['payloadHash'], requested_model,
                                                binding['memorySnapshotHash']])
    def create(**kwargs):
        check_compatibility()
        kwargs.update(acp_command=[sys.executable, str(Path(__file__).with_name('fake_acp.py')),
                    '--model-probe', scenario, '--model-log', str(log), '--permission-probe'],
                      acp_model=requested_model, acp_prompt_timeout=timeout)
        if scenario == 'prompt-timeout':
            kwargs['acp_command'] += ['--cancel-probe', str(Path(results) / 'cancel-receipt.json')]
        agent = (BudgetPermissionAgent if baseline else ModelPermissionAdapterV1)(**kwargs)
        if not baseline:
            agent._binding = dict(binding)
            agent._admit = admit
            agent._receipt_directory = Path(results)
        return agent
    return create
