import copy
import hashlib
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from dossier import InvalidDossier, digest
from operator_status import CONNECTOR_FILES, inspect_operator, observe_lock
from workspace import prepare_workspace


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
    commit_fixture(source, "fixture")
    commit = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip()
    return source, commit


def commit_fixture(source, message):
    """Disable signing for this fixture commit only. Do not change global Git config."""
    subprocess.check_call(["git", "-C", str(source), "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                           "-c", "commit.gpgsign=false", "commit", "-m", message],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def tree_snapshot(path):
    path = Path(path)
    if not path.exists():
        return []
    rows = []
    for item in sorted(path.rglob("*")):
        info = item.lstat()
        rows.append((item.relative_to(path).as_posix(), stat.S_IFMT(info.st_mode), info.st_size))
    return rows


def unavailable_docker():
    return {"daemon": "unavailable", "reason": "docker_cli_absent", "container": "not_observed"}


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
            self.assertIn("canonical_claim", report["missingEvidence"])
            self.assertIn("docker", report["missingEvidence"])
            self.assertNotIn("python3", report["missingEvidence"])
            self.assertEqual(report["lock"]["status"], "not_requested")

    def test_policy_directory_does_not_verify_authentication(self):
        with tempfile.TemporaryDirectory() as directory:
            policy = Path(directory) / "policies"
            policy.mkdir()
            before = tree_snapshot(policy)
            report = inspect_operator(policy_root=policy, docker_probe=lambda: {"daemon": "available", "serverVersion": "test", "container": "not_observed"})
            self.assertEqual(tree_snapshot(policy), before)
            self.assertTrue(report["prerequisites"]["connectorDirectoryPresent"])
            self.assertFalse(report["prerequisites"]["connectorConfigured"])
            self.assertEqual(report["prerequisites"]["connectorReason"], "connector_content_missing")
            self.assertFalse(report["prerequisites"]["authenticationVerified"])
            self.assertFalse(report["readyForRealMission"])
            self.assertIn("provider_connector", report["missingEvidence"])
            self.assertNotIn(str(policy), json.dumps(report))

    def test_docker_timeout_stays_unavailable(self):
        def fail(_command, **_kwargs):
            raise subprocess.TimeoutExpired("docker", 3)
        report = inspect_operator(which=lambda name: "/usr/bin/docker" if name == "docker" else None, run=fail)
        self.assertEqual(report["docker"], {"daemon": "unavailable", "reason": "docker_probe_failed", "container": "not_observed"})
        for name in ("python3", "node", "git", "flock", "docker"):
            self.assertIn(name, report["missingEvidence"])

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
            before_jobs = tree_snapshot(jobs)
            before_source = tree_snapshot(source)
            with self.assertRaises(InvalidDossier):
                inspect_operator(dossier=dossier, workspace="other-workspace", executor_version="1.50.0",
                                 source=source, jobs_root=jobs, docker_probe=unavailable_docker)
            self.assertEqual(tree_snapshot(jobs), before_jobs)
            self.assertEqual(tree_snapshot(source), before_source)

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

    def test_empty_job_and_policy_are_present_but_not_validated(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            jobs = root / "jobs"
            policy = root / "policies"
            jobs.mkdir()
            policy.mkdir()
            empty = jobs / "job-empty"
            empty.mkdir()
            before = tree_snapshot(root)
            report = inspect_operator(jobs_root=jobs, policy_root=policy, docker_probe=unavailable_docker)
            self.assertEqual(tree_snapshot(root), before)
            self.assertEqual(list(empty.iterdir()), [])
            self.assertEqual(list(policy.iterdir()), [])
            workspace = report["prerequisites"]["isolatedWorkspace"]
            self.assertTrue(workspace["directoryPresent"])
            self.assertFalse(workspace["isolated"])
            self.assertEqual(workspace["reason"], "empty_job_directory")
            self.assertTrue(report["prerequisites"]["connectorDirectoryPresent"])
            self.assertFalse(report["prerequisites"]["connectorConfigured"])
            self.assertEqual(report["prerequisites"]["connectorReason"], "connector_content_missing")
            self.assertIn("isolated_workspace", report["missingEvidence"])
            self.assertIn("provider_connector", report["missingEvidence"])
            self.assertFalse(report["readyForRealMission"])

    def test_commit_identity_mismatch_does_not_touch_checkout(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, old = git_repo(root)
            (source / "README.md").write_text("changed\n", encoding="utf-8")
            subprocess.check_call(["git", "-C", str(source), "add", "README.md"], stdout=subprocess.DEVNULL)
            commit_fixture(source, "second")
            new = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip()
            jobs = root / "jobs"
            jobs.mkdir()
            prepare_workspace(source=source, commit=old, server_root=jobs, job_name="job-1")
            before = tree_snapshot(root)
            report = inspect_operator(dossier=fixture_dossier(new), workspace="synthetic-a", executor_version="1.50.0",
                                      source=source, jobs_root=jobs, docker_probe=unavailable_docker)
            self.assertEqual(tree_snapshot(root), before)
            self.assertFalse(report["prerequisites"]["isolatedWorkspace"]["isolated"])
            self.assertEqual(report["prerequisites"]["isolatedWorkspace"]["reason"], "commit_identity_mismatch")
            self.assertEqual(report["prerequisites"]["isolatedWorkspace"]["observedCommit"], old)
            self.assertFalse(report["readyForRealMission"])
            self.assertNotIn("sentinel-secret-objective-not-for-report", json.dumps(report))

    def test_matching_checkout_and_connector_still_are_not_a_real_mission(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, commit = git_repo(root)
            jobs = root / "jobs"
            jobs.mkdir()
            prepare_workspace(source=source, commit=commit, server_root=jobs, job_name="job-1")
            policy = root / "policies"
            profile = policy / "local-connector"
            profile.mkdir(parents=True)
            contents = {name: f"{name}-bytes\n".encode() for name in CONNECTOR_FILES}
            manifest = {"id": "local-connector", "files": {name: hashlib.sha256(data).hexdigest() for name, data in contents.items()}}
            (profile / "policy.json").write_text(json.dumps(manifest), encoding="utf-8")
            for name, data in contents.items():
                (profile / name).write_bytes(data)
            before = tree_snapshot(root)
            report = inspect_operator(dossier=fixture_dossier(commit), workspace="synthetic-a", executor_version="1.50.0",
                                      source=source, jobs_root=jobs, policy_root=policy, docker_probe=unavailable_docker)
            self.assertEqual(tree_snapshot(root), before)
            self.assertTrue(report["prerequisites"]["isolatedWorkspace"]["isolated"])
            self.assertEqual(report["prerequisites"]["isolatedWorkspace"]["commitSha"], commit)
            self.assertTrue(report["prerequisites"]["connectorConfigured"])
            self.assertFalse(report["prerequisites"]["authenticationVerified"])
            self.assertFalse(report["prerequisites"]["authorizationPresent"])
            self.assertEqual(report["canonicalState"], "unknown")
            self.assertIn("provider_authentication", report["missingEvidence"])
            self.assertIn("canonical_claim", report["missingEvidence"])
            self.assertNotIn("provider_connector", report["missingEvidence"])
            self.assertNotIn("isolated_workspace", report["missingEvidence"])
            self.assertFalse(report["readyForRealMission"])
            self.assertFalse(report["independentValidationPassed"])

    def test_missing_tools_are_named_in_missing_evidence(self):
        report = inspect_operator(which=lambda _name: None, docker_probe=unavailable_docker)
        for name in ("python3", "node", "git", "flock", "docker"):
            self.assertIn(name, report["missingEvidence"])
            if name != "docker":
                self.assertFalse(report["prerequisites"]["tools"][name]["available"])
        self.assertFalse(report["readyForRealMission"])

    def test_incomplete_cli_binding_refuses_without_writing_inspected_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, commit = git_repo(root)
            jobs = root / "jobs"
            policy = root / "policies"
            jobs.mkdir()
            policy.mkdir()
            request = root / "request.json"
            request.write_text(json.dumps(fixture_dossier(commit)), encoding="utf-8")
            before = tree_snapshot(root)
            completed = subprocess.run([sys.executable, str(Path(__file__).with_name("operator_status.py")),
                                        "--dossier", str(request), "--jobs-root", str(jobs), "--policy-root", str(policy)],
                                       capture_output=True, text=True, timeout=10)
            self.assertEqual(completed.returncode, 2)
            self.assertEqual(json.loads(completed.stdout)["reason"], "incomplete_dossier_binding")
            self.assertFalse(json.loads(completed.stdout)["resourcesModified"])
            self.assertNotIn("sentinel-secret-objective-not-for-report", completed.stdout + completed.stderr)
            self.assertEqual(tree_snapshot(root), before)
            self.assertEqual(list(jobs.iterdir()), [])
            self.assertEqual(list(policy.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
