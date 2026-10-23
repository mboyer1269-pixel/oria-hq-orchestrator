"""Real pinned SDK / synthetic stdio ACP. No inference or credentials."""
import copy
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from openhands.sdk import Conversation
from openhands.sdk.conversation.exceptions import ConversationRunError
from model_selection_probe import build_probe
from dossier import digest, InvalidDossier


class ModelSelectionProbeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.checkout = self.root / "checkout"
        self.checkout.mkdir()
        def git(*args):
            return subprocess.check_output(["git", "-C", str(self.checkout), *args],
                stderr=subprocess.DEVNULL, text=True).strip()
        git("init")
        git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
            "commit", "--allow-empty", "-m", "Synthetic qualification")
        self.dossier = json.loads((Path(__file__).resolve().parents[1] /
            "openhands-runner/fixtures/hq-memory-dossier.json").read_text())
        self.dossier["source"]["commitSha"] = git("rev-parse", "HEAD")
        self.dossier["payloadHash"] = digest({k: v for k, v in self.dossier.items()
            if k not in ("payloadHash", "idempotencyKey")})
        self.log = self.root / "wire.jsonl"

    def run_case(self, model="fixture-model-2", scenario="accept", turns=1):
        original = copy.deepcopy(self.dossier)
        agent, message = build_probe(self.dossier, self.checkout,
            self.dossier["mission"]["workspaceId"], model, scenario, self.log,
            baseline=os.environ.get("ORIA_PROBE_BASELINE") == "1")
        conversation = Conversation(agent=agent, workspace=str(self.checkout))
        try:
            for _ in range(turns):
                conversation.send_message(message)
                try:
                    conversation.run()
                except (ValueError, ConversationRunError):
                    # The SDK wraps a failed pre-prompt gate as ConversationRunError.
                    pass
            receipt = getattr(agent, "_selection_receipt", None)
        finally:
            agent.close()
        self.assertEqual(self.dossier, original)
        wire = [json.loads(line) for line in self.log.read_text().splitlines()]
        return wire, receipt

    def test_exact_acknowledgement_precedes_prompt_and_binds_unchanged_memory(self):
        wire, receipt = self.run_case()
        prompts = [i for i, item in enumerate(wire) if item.get("method") == "session/prompt"]
        self.assertEqual(len(prompts), 1)
        selections = [i for i, item in enumerate(wire) if item.get("method") == "session/set_config_option"]
        self.assertTrue(selections)
        self.assertLess(max(selections), prompts[0])
        self.assertEqual(wire[max(selections)]["params"]["value"], "fixture-model-2")
        self.assertEqual(wire[max(selections)]["params"]["sessionId"],
                         wire[prompts[0]]["params"]["sessionId"])
        texts = '\n'.join(block.get("text", "") for block in wire[prompts[0]]["params"]["prompt"])
        self.assertIn(json.dumps(self.dossier["memory"], ensure_ascii=False), texts)
        self.assertIsNotNone(receipt)
        self.assertEqual(receipt["qualificationBindingHash"], digest([self.dossier["payloadHash"],
            "fixture-model-2", self.dossier["memory"]["snapshotHash"]]))
        self.assertEqual(receipt["payloadHash"], self.dossier["payloadHash"])
        self.assertEqual(receipt["memorySnapshotHash"], self.dossier["memory"]["snapshotHash"])
        self.assertEqual(receipt["requestedModelId"], receipt["acpConfirmedModelId"])
        self.assertEqual(receipt["evidence"], "synthetic_adapter_acknowledgement")

    def test_refuses_before_prompt(self):
        for model, scenario in [(None, "accept"), ("unknown-model-9", "accept"),
                                ("fixture-model-2", "missing-ack"),
                                ("fixture-model-2", "absent"),
                                ("fixture-model-2", "mismatch"),
                                ("fixture-model-2", "reject")]:
            with self.subTest(model=model, scenario=scenario):
                if self.log.exists(): self.log.unlink()
                wire, receipt = self.run_case(model, scenario)
                self.assertFalse(any(m.get("method") == "session/prompt" for m in wire))
                self.assertIsNone(receipt)

    def test_default_is_literal_and_each_turn_requires_acknowledgement(self):
        wire, receipt = self.run_case("default", turns=2)
        prompts = [i for i, m in enumerate(wire) if m.get("method") == "session/prompt"]
        self.assertEqual(len(prompts), 2)
        previous = -1
        for index in prompts:
            selections = [m for m in wire[previous + 1:index]
                if m.get("method") == "session/set_config_option"]
            self.assertTrue(selections)
            self.assertEqual(selections[-1]["params"]["value"], "default")
            previous = index
        self.assertIsNotNone(receipt)
        self.assertEqual(receipt["acpConfirmedModelId"], "default")

    def test_invalid_dossier_never_starts_peer(self):
        for mutation in ("memory", "hash", "workspace", "v3"):
            with self.subTest(mutation=mutation):
                d = copy.deepcopy(self.dossier)
                if mutation == "memory": d["memory"]["content"] = "altered"
                elif mutation == "hash": d["payloadHash"] = "0" * 64
                elif mutation == "workspace": d["memory"]["workspaceId"] = "foreign"
                else: d.update(contractVersion=3, foundationModelId="fixture-model-2")
                with self.assertRaises(InvalidDossier):
                    build_probe(d, self.checkout, self.dossier["mission"]["workspaceId"],
                        "fixture-model-2", "accept", self.log)
                self.assertFalse(self.log.exists())


if __name__ == "__main__": unittest.main()
