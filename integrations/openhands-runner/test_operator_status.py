import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from dossier import digest
from operator_status import inspect_operator, observe_lock


def fixture_dossier(commit):
    data = json.loads((Path(__file__).parent / "fixtures/hq-dossier.json").read_text(encoding="utf-8"))
    data = copy.deepcopy(data)
    data["mission"]["objective"] = "sentinel-secret-objective-not-for-report"
    data["source"]["commitSha"] = commit
    data["payloadHash"] = digest({key: value for key, value in data.items() if key not in ("payloadHash", "idempotencyKey")})
    return data


def git_repo(root):
    source = root / "source"
    source.mkdir()
    subprocess.check_call(["git", "-C", str(source), "init"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    (source / "README.md").write_text("synthetic\n", encoding="utf-8")
    subprocess.check_call(["git", "-C", str(source), "add", "README.md"], stdout=subprocess.DEVNULL)
    subprocess.check_call(["git", "-C", str(source), "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                           "-c", "commit.gpgsign=false", "commit", "-m", "fixture"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    commit = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip()
    return source, commit


class OperatorStatusTests(unittest.TestCase):
    def test_environment_inspection_has_no_effects_and_hides_secrets(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            before = sorted(root.iterdir())
            with patch.dict(os.environ, {"ORIA_TEST_SECRET": "super-secret-token"}):
                report = inspect_operator(docker_probe=lambda: {"daemon": "unavailable", "reason": "docker_cli_absent", "container": "not_observed"})
            self.assertEqual(sorted(root.iterdir()), before)
            encoded = json.dumps(report)
            self.assertNotIn("super-secret-token", encoded)
            self.assertFalse(report["resourcesModified"])
            self.assertFalse(report["readyForRealMission"])
            self.assertFalse(report["prerequisites"]["authenticationVerified"])
            self.assertFalse(report["prerequisites"]["authorizationPresent"])
            self.assertEqual(report["canonicalState"], "unknown")
            self.assertEqual(report["docker"]["container"], "not_observed")
            self.assertNotEqual(report["docker"]["daemon"], "absent")
            self.assertIn("provider_authentication", report["missingEvidence"])
            self.assertIn("docker_daemon", report["missingEvidence"])
            self.assertEqual(report["lock"]["status"], "not_requested")

    def test_policy_directory_does_not_verify_authentication(self):
        with tempfile.TemporaryDirectory() as directory:
            policy = Path(directory) / "policies"
            policy.mkdir()
            report = inspect_operator(policy_root=policy, docker_probe=lambda: {"daemon": "available", "serverVersion": "test", "container": "not_observed"})
            self.assertTrue(report["prerequisites"]["connectorConfigured"])
            self.assertFalse(report["prerequisites"]["authenticationVerified"])
            self.assertNotIn(str(policy), json.dumps(report))

    def test_docker_timeout_stays_unavailable(self):
        def fail(_command, **_kwargs):
            raise subprocess.TimeoutExpired("docker", 3)
        report = inspect_operator(which=lambda name: "/usr/bin/docker" if name == "docker" else None, run=fail)
        self.assertEqual(report["docker"], {"daemon": "unavailable", "reason": "docker_probe_failed", "container": "not_observed"})

    def test_invented_container_absence_is_rejected(self):
        with self.assertRaises(ValueError):
            inspect_operator(docker_probe=lambda: {"daemon": "unavailable", "container": "absent"})

    def test_missing_lock_is_not_created(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "launch.lock"
            self.assertEqual(observe_lock(missing), {"status": "absent", "created": False})
            self.assertFalse(missing.exists())

    def test_held_lock_is_observed_without_taking_it(self):
        import fcntl
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "launch.lock"
            descriptor = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
            try:
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
                mode = path.stat().st_mode
                observed = observe_lock(path)
                self.assertEqual(observed["status"], "held")
                self.assertFalse(observed["created"])
                self.assertEqual(path.stat().st_mode, mode)
            finally:
                fcntl.flock(descriptor, fcntl.LOCK_UN)
                os.close(descriptor)

    def test_foreign_workspace_refuses_before_creating_a_job(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, commit = git_repo(root)
            jobs = root / "jobs"
            jobs.mkdir()
            dossier = fixture_dossier(commit)
            before = list(jobs.iterdir())
            with self.assertRaises(Exception):
                inspect_operator(dossier=dossier, workspace="other-workspace", executor_version="1.50.0",
                                 source=source, jobs_root=jobs,
                                 docker_probe=lambda: {"daemon": "unavailable", "reason": "docker_cli_absent", "container": "not_observed"})
            self.assertEqual(list(jobs.iterdir()), before)

    def test_valid_dossier_reports_budget_without_objective_or_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, commit = git_repo(root)
            jobs = root / "jobs"
            jobs.mkdir()
            dossier = fixture_dossier(commit)
            report = inspect_operator(dossier=dossier, workspace="synthetic-a", executor_version="1.50.0",
                                      source=source, jobs_root=jobs,
                                      docker_probe=lambda: {"daemon": "unavailable", "reason": "docker_cli_absent", "container": "not_observed"})
            encoded = json.dumps(report)
            self.assertNotIn("sentinel-secret-objective-not-for-report", encoded)
            self.assertEqual(report["mission"]["id"], dossier["mission"]["id"])
            self.assertEqual(report["executor"]["version"], "1.50.0")
            self.assertTrue(report["prerequisites"]["budgetDefined"])
            self.assertFalse(report["prerequisites"]["authorizationPresent"])
            self.assertFalse(report["executionRequested"])
            self.assertEqual(report["prerequisites"]["isolatedWorkspace"]["status"], "not_prepared")
            self.assertEqual(list(jobs.iterdir()), [])

    def test_cli_rejects_force_without_writing(self):
        with tempfile.TemporaryDirectory() as directory:
            jobs = Path(directory) / "jobs"
            jobs.mkdir()
            completed = subprocess.run([sys.executable, str(Path(__file__).with_name("operator_status.py")),
                                        "--jobs-root", str(jobs), "--force"], capture_output=True, text=True, timeout=5)
            self.assertNotEqual(completed.returncode, 0)
            self.assertEqual(list(jobs.iterdir()), [])

    def test_cli_repeat_is_stable(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, commit = git_repo(root)
            request = root / "request.json"
            request.write_text(json.dumps(fixture_dossier(commit)), encoding="utf-8")
            command = [sys.executable, str(Path(__file__).with_name("operator_status.py")),
                       "--dossier", str(request), "--workspace", "synthetic-a", "--executor-version", "1.50.0",
                       "--source", str(source)]
            first = subprocess.run(command, capture_output=True, text=True, timeout=10)
            second = subprocess.run(command, capture_output=True, text=True, timeout=10)
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual(json.loads(first.stdout)["mission"], json.loads(second.stdout)["mission"])
            self.assertFalse(json.loads(first.stdout)["resourcesModified"])


if __name__ == "__main__":
    unittest.main()
