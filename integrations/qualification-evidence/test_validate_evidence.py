"""Adversarial checks for the offline admission-report validator."""

import json
import subprocess
import sys
import unittest
from pathlib import Path

from validate_evidence import EXIT_CODES, validate_report

ROOT = Path(__file__).resolve().parent
FIXTURES = ROOT / "fixtures" / "synthetic"
COMMIT = "a" * 40
OTHER = "b" * 40
DIGEST = "sha256:" + "ab" * 32
CLI = [sys.executable, str(ROOT / "validate_evidence.py")]


def output(phase, commit=COMMIT, exit_code=0):
    return {
        "command": f"psql -c {phase}",
        "expectedExitCode": exit_code,
        "exitCode": exit_code,
        "testedCommit": commit,
        "phase": phase,
    }


def assertion(name, expected=True, observed=True):
    return {"id": name, "passed": True, "expected": expected, "observed": observed}


def coherent_real_report():
    return {
        "schemaVersion": 2,
        "fixtureClass": "collected",
        "testedCommit": COMMIT,
        "limits": ["Historique de migration incomplet.", "Aucune mission réelle n'est revendiquée."],
        "database": {
            "backendKind": "postgresql",
            "engine": "postgresql",
            "implementation": "postgresql+postgrest",
            "selectVersion": "PostgreSQL 17.11 on x86_64",
            "postgrestVersion": "13.0.0",
            "imageDigests": [DIGEST],
            "migrationsApplied": ["0001_admission.sql"],
            "migrationHistoryComplete": False,
            "sqlConstraint": {
                "name": "admission_identity_unique",
                "definition": "UNIQUE (identity)",
                "catalogSource": "pg_constraint",
            },
        },
        "scenarios": [
            {
                "id": "same_request_concurrent",
                "status": "real",
                "testedCommit": COMMIT,
                "rowCount": 1,
                "secondExecutionStarted": False,
                "assertions": [assertion("single_row", 1, 1), assertion("both_callers_same_row")],
                "outputs": [output("concurrent")],
                "limits": ["Deux appels seulement."],
            },
            {
                "id": "divergent_payload",
                "status": "real",
                "testedCommit": COMMIT,
                "secondPayloadStored": False,
                "assertions": [assertion("payload_conflict_refused"), assertion("stored_payload_unchanged")],
                "outputs": [output("divergent", exit_code=409)],
                "limits": ["Payload synthétique."],
            },
            {
                "id": "lost_response_after_commit",
                "status": "real",
                "testedCommit": COMMIT,
                "procedure": "commit_then_drop_response_then_replay",
                "assertions": [
                    assertion("committed_before_loss"),
                    assertion("response_dropped_after_commit"),
                    assertion("replay_creates_nothing"),
                ],
                "outputs": [output("commit"), output("drop_response", exit_code=1), output("replay")],
                "limits": ["La perte est injectée par le banc, pas par le réseau."],
            },
            {
                "id": "restart",
                "status": "real",
                "testedCommit": COMMIT,
                "assertions": [
                    assertion("sql_count_before_restart", 1, 1),
                    assertion("sql_count_after_restart", 1, 1),
                ],
                "outputs": [output("count_before_restart"), output("restart_database"), output("count_after_restart")],
                "limits": ["Un redémarrage du processus PostgreSQL du banc."],
            },
            {
                "id": "protected_identity",
                "status": "real",
                "testedCommit": COMMIT,
                "bodyWorkspaceUsed": False,
                "assertions": [assertion("workspace_from_protected_context"), assertion("foreign_workspace_denied")],
                "outputs": [output("foreign_workspace")],
                "limits": ["Identités synthétiques."],
            },
            {
                "id": "admission_authorization_execution",
                "status": "real",
                "testedCommit": COMMIT,
                "admissionMeansExecution": False,
                "stateCounts": {"admitted": 1, "authorized": 0, "executed": 0},
                "assertions": [assertion("states_observed_separately")],
                "outputs": [output("state_counts")],
                "limits": ["L'exécution n'a pas été lancée."],
            },
        ],
    }


def codes(document):
    return [item["code"] for item in document["reasons"]]


def run_cli(path):
    completed = subprocess.run(CLI + [str(path)], check=False, capture_output=True, text=True)
    return completed.returncode, json.loads(completed.stdout)


class ValidatorTests(unittest.TestCase):
    def assert_closed(self, document):
        self.assertFalse(document["readyForProduction"])
        self.assertFalse(document["authenticatesExecution"])
        self.assertNotIn("ready_for_production", document["verdict"])
        self.assertIn("ne prouve pas", " ".join(document["limits"]))

    def test_coherent_json_is_reviewable_and_not_authentication(self):
        document = validate_report(coherent_real_report())
        self.assertEqual(document["verdict"], "reviewable")
        self.assertEqual(document["reasons"], [])
        self.assert_closed(document)

    def test_disk_fixtures_are_synthetic_and_never_reviewable(self):
        paths = sorted(FIXTURES.glob("*.json"))
        self.assertGreaterEqual(len(paths), 6)
        for path in paths:
            report = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(report["fixtureClass"], "synthetic", path.name)
            document = validate_report(report)
            self.assertNotEqual(document["verdict"], "reviewable", path.name)
            self.assert_closed(document)

    def test_map_mock_and_createserver_cannot_be_real(self):
        for backend, implementation, select_version in (
            ("map", "Map", "Map"),
            ("mock", "mock", "PostgreSQL 17.11"),
            ("http-in-process", "http.createServer", "PostgreSQL 17.11"),
            ("postgresql", "postgresql+postgrest", "PostgreSQL 17.11 via http.createServer"),
        ):
            report = coherent_real_report()
            report["database"]["backendKind"] = backend
            report["database"]["implementation"] = implementation
            report["database"]["selectVersion"] = select_version
            document = validate_report(report)
            self.assertEqual(document["verdict"], "refused", backend)
            self.assertIn("backend_map_or_mock", codes(document))

    def test_missing_digest_migration_or_constraint_is_refused(self):
        cases = []
        missing_digest = coherent_real_report()
        missing_digest["database"]["imageDigests"] = []
        cases.append(missing_digest)
        missing_migration = coherent_real_report()
        missing_migration["database"]["migrationsApplied"] = []
        cases.append(missing_migration)
        lookup_constraint = coherent_real_report()
        lookup_constraint["database"]["sqlConstraint"] = {
            "name": "app",
            "definition": "application lookup then insert",
            "catalogSource": "pg_constraint",
        }
        cases.append(lookup_constraint)
        code_constraint = coherent_real_report()
        code_constraint["database"]["sqlConstraint"]["catalogSource"] = "test-source"
        cases.append(code_constraint)
        for report in cases:
            document = validate_report(report)
            self.assertEqual(document["verdict"], "refused")
            self.assertTrue(set(codes(document)) & {"missing_image_digest", "missing_migrations", "constraint_not_observed", "constraint_not_unique"})

    def test_lookup_labeled_lost_response_is_refused(self):
        report = coherent_real_report()
        scenario = next(item for item in report["scenarios"] if item["id"] == "lost_response_after_commit")
        scenario["procedure"] = "lookup_before_create"
        scenario["assertions"] = [{"id": "lookup_before_create", "passed": True, "expected": True, "observed": True}]
        scenario["outputs"] = [output("lookup")]
        document = validate_report(report)
        self.assertEqual(document["verdict"], "refused")
        self.assertIn("simple_lookup_labeled_lost_response", codes(document))

    def test_different_commits_are_refused(self):
        report = coherent_real_report()
        report["scenarios"][0]["testedCommit"] = OTHER
        report["scenarios"][1]["outputs"][0]["testedCommit"] = OTHER
        document = validate_report(report)
        self.assertEqual(document["verdict"], "refused")
        self.assertIn("mixed_commits", codes(document))

    def test_restart_without_sql_counts_is_refused(self):
        report = coherent_real_report()
        scenario = next(item for item in report["scenarios"] if item["id"] == "restart")
        scenario["assertions"] = [assertion("sql_count_before_restart", 1, 1)]
        scenario["outputs"] = [output("count_before_restart")]
        document = validate_report(report)
        self.assertEqual(document["verdict"], "refused")
        self.assertIn("restart_count_assertion_missing", codes(document))

    def test_disagreeing_restart_counts_are_refused(self):
        report = coherent_real_report()
        scenario = next(item for item in report["scenarios"] if item["id"] == "restart")
        scenario["assertions"][1]["expected"] = 2
        scenario["assertions"][1]["observed"] = 2
        document = validate_report(report)
        self.assertEqual(document["verdict"], "refused")
        self.assertIn("restart_counts_disagree", codes(document))

    def test_failed_or_contradictory_assertion_is_not_reviewable(self):
        failed = coherent_real_report()
        failed["scenarios"][0]["assertions"][0]["passed"] = False
        document = validate_report(failed)
        self.assertEqual(document["verdict"], "refused")
        self.assertIn("assertion_failed", codes(document))
        contradicted = coherent_real_report()
        contradicted["scenarios"][0]["assertions"][0]["observed"] = 0
        document = validate_report(contradicted)
        self.assertEqual(document["verdict"], "refused")
        self.assertIn("assertion_contradiction", codes(document))
        both = coherent_real_report()
        both["scenarios"][0]["assertions"][0]["passed"] = False
        both["scenarios"][0]["assertions"][0]["observed"] = 0
        document = validate_report(both)
        self.assertEqual(document["verdict"], "refused")
        self.assertIn("assertion_failed", codes(document))
        self.assertIn("assertion_contradiction", codes(document))

    def test_malformed_and_negative_values_are_refused(self):
        cases = []
        string_passed = coherent_real_report()
        string_passed["scenarios"][0]["assertions"][0]["passed"] = "true"
        cases.append(string_passed)
        mixed_types = coherent_real_report()
        mixed_types["scenarios"][0]["assertions"][0]["expected"] = True
        mixed_types["scenarios"][0]["assertions"][0]["observed"] = 1
        cases.append(mixed_types)
        missing_observed = coherent_real_report()
        del missing_observed["scenarios"][0]["assertions"][0]["observed"]
        cases.append(missing_observed)
        negative_count = coherent_real_report()
        negative_count["scenarios"][0]["assertions"][0]["expected"] = -1
        negative_count["scenarios"][0]["assertions"][0]["observed"] = -1
        cases.append(negative_count)
        negative_exit = coherent_real_report()
        negative_exit["scenarios"][0]["outputs"][0]["expectedExitCode"] = -1
        negative_exit["scenarios"][0]["outputs"][0]["exitCode"] = -1
        cases.append(negative_exit)
        negative_state = coherent_real_report()
        negative_state["scenarios"][-1]["stateCounts"]["executed"] = -1
        cases.append(negative_state)
        exit_mismatch = coherent_real_report()
        exit_mismatch["scenarios"][1]["outputs"][0]["exitCode"] = 0
        cases.append(exit_mismatch)
        for report in cases:
            document = validate_report(report)
            self.assertEqual(document["verdict"], "refused")
            self.assertTrue(set(codes(document)) & {"assertion_malformed", "negative_value", "assertion_contradiction"})

    def test_schema_v1_cannot_stay_reviewable(self):
        report = coherent_real_report()
        report["schemaVersion"] = 1
        document = validate_report(report)
        self.assertEqual(document["verdict"], "incomplete")
        self.assertIn("schema_obsolete", codes(document))

    def test_admission_is_not_execution(self):
        report = coherent_real_report()
        scenario = next(item for item in report["scenarios"] if item["id"] == "admission_authorization_execution")
        scenario["admissionMeansExecution"] = True
        scenario["stateCounts"] = {"admitted": 1}
        document = validate_report(report)
        self.assertEqual(document["verdict"], "refused")
        self.assertIn("admission_confused_with_execution", codes(document))

    def test_self_certification_and_declared_verdict_are_ignored(self):
        report = coherent_real_report()
        report["verdict"] = "reviewable"
        report["database"]["backendKind"] = "map"
        document = validate_report(report)
        self.assertEqual(document["verdict"], "refused")
        produced = coherent_real_report()
        produced["readyForProduction"] = True
        produced["authenticatesExecution"] = True
        document = validate_report(produced)
        self.assertEqual(document["verdict"], "refused")
        self.assertIn("self_certified_production", codes(document))
        self.assertIn("self_certified_authentication", codes(document))
        self.assert_closed(document)

    def test_simulated_not_run_failed_and_missing_stay_incomplete(self):
        simulated = coherent_real_report()
        simulated["fixtureClass"] = "synthetic"
        for scenario in simulated["scenarios"]:
            scenario["status"] = "simulated"
        self.assertEqual(validate_report(simulated)["verdict"], "incomplete")
        not_run = coherent_real_report()
        not_run["scenarios"][0]["status"] = "not_run"
        self.assertEqual(validate_report(not_run)["verdict"], "incomplete")
        failed = coherent_real_report()
        failed["scenarios"][0]["status"] = "failed"
        self.assertEqual(validate_report(failed)["verdict"], "incomplete")
        missing = coherent_real_report()
        missing["scenarios"] = missing["scenarios"][1:]
        self.assertEqual(validate_report(missing)["verdict"], "incomplete")

    def test_synthetic_label_blocks_an_otherwise_coherent_real_report(self):
        report = coherent_real_report()
        report["fixtureClass"] = "synthetic"
        document = validate_report(report)
        self.assertEqual(document["verdict"], "refused")
        self.assertIn("synthetic_labeled_real", codes(document))

    def test_cli_exit_codes_never_mean_production(self):
        code, document = run_cli(FIXTURES / "map-as-real.json")
        self.assertEqual(code, EXIT_CODES["refused"])
        self.assertEqual(document["verdict"], "refused")
        self.assert_closed(document)
        invalid = FIXTURES / "not-json.json"
        invalid.write_text("{", encoding="utf-8")
        self.addCleanup(invalid.unlink)
        code, document = run_cli(invalid)
        self.assertEqual(code, EXIT_CODES["incomplete"])
        self.assertEqual(document["verdict"], "incomplete")
        self.assertNotIn(0, EXIT_CODES.values())

    def test_validator_source_does_not_open_a_database_or_network(self):
        source = (ROOT / "validate_evidence.py").read_text(encoding="utf-8")
        for banned in ("import socket", "import urllib", "import subprocess", "psycopg", "docker"):
            self.assertNotIn(banned, source)


if __name__ == "__main__":
    unittest.main()
