"""Qualification only: pinned SDK against the local synthetic peer, never a provider.

This private-hook experiment does not enable dossier v3 or modify the runner.
An ACP acknowledgement is not independent evidence of provider inference.
"""
import asyncio
import importlib.metadata
from pathlib import Path
import sys
from pydantic import PrivateAttr
from openhands.sdk.agent import ACPAgent

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "openhands-runner"))
from dossier import prepare, digest
from run_mission import mission_message


class _ExactModelProbe(ACPAgent):
    _binding: dict = PrivateAttr(default_factory=dict)
    _selection_receipt: dict | None = PrivateAttr(default=None)

    async def select_exact_model(self):
        # The SDK's initial selection is best-effort and discards the response.
        # Reassert on the SAME session before every prompt, including retries.
        self._selection_receipt = None
        requested = self.acp_model
        if (not requested or not self._model_via_config_option
                or requested not in {m.model_id for m in self._available_models or []}
                or self._conn is None or self._session_id is None):
            raise ValueError("Exact model capability not advertised")
        response = await asyncio.wait_for(self._conn.set_config_option(
            config_id="model", value=requested, session_id=self._session_id),
            timeout=self.acp_prompt_timeout)
        raw = response.model_dump(mode="json", by_alias=True)
        options = [o for o in raw.get("configOptions", []) if o.get("id") == "model"]
        if (len(options) != 1 or options[0].get("type") != "select"
                or options[0].get("currentValue") != requested
                or requested not in {o.get("value") for o in options[0].get("options", [])}):
            raise ValueError("Exact model acknowledgement missing or different")
        self._selection_receipt = {**self._binding, "requestedModelId": requested,
            "acpConfirmedModelId": requested, "evidence": "synthetic_adapter_acknowledgement"}

    async def _do_acp_prompt(self, prompt_blocks):
        await self.select_exact_model()
        return await super()._do_acp_prompt(prompt_blocks)


def build_probe(dossier, checkout, workspace_id, requested_model, scenario, log, *, baseline=False):
    """Validate existing v1/v2 envelope; bind a candidate model separately for testing.

    Deliberately NOT a v3 receiver or an authorization/launch path.
    """
    if importlib.metadata.version("openhands-sdk") != "1.50.0":
        raise ValueError("Qualification requires pinned SDK 1.50.0")
    if importlib.metadata.version("agent-client-protocol") != "0.12.1":
        raise ValueError("Qualification requires pinned ACP client 0.12.1")
    prepared = prepare(dossier, expected_workspace=workspace_id,
        expected_executor_version="1.50.0", checkout=checkout)
    peer = Path(__file__).with_name("fake_acp.py").resolve()
    cls = ACPAgent if baseline else _ExactModelProbe
    agent = cls(acp_command=[sys.executable, str(peer), "--model-probe", scenario,
                            "--model-log", str(log)], acp_model=requested_model,
                acp_startup_timeout=5, acp_prompt_timeout=5)
    if not baseline:
        agent._binding = {"payloadHash": prepared["payloadHash"],
            "idempotencyKey": prepared["idempotencyKey"],
            "memorySnapshotHash": dossier.get("memory", {}).get("snapshotHash"),
            "qualificationBindingHash": digest([prepared["payloadHash"], requested_model,
                dossier.get("memory", {}).get("snapshotHash")])}
    return agent, mission_message(dossier)
