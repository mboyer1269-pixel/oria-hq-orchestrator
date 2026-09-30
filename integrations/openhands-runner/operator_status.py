"""Read-only operator readiness. Never reconciles, executes, or calls a model.

Exit 0 means an inspection report was produced. It does not mean a mission
succeeded, a container is absent, or a provider account was authenticated.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
from pathlib import Path

from dossier import InvalidDossier, prepare
from provider_policy import EXPECTED, FILES, validate_manifest
from request_io import read_dossier
from workspace import git_environment



def _version(path, run):
    try:
        completed = run([path, "--version"], capture_output=True, text=True, timeout=3)
    except (OSError, subprocess.TimeoutExpired):
        return {"available": False, "reason": "version_probe_failed"}
    line = ((completed.stdout or completed.stderr or "").strip().splitlines() or [""])[0][:80]
    if completed.returncode != 0 or not line:
        return {"available": False, "reason": "version_probe_failed"}
    return {"available": True, "version": line}


def probe_tools(*, which=shutil.which, run=subprocess.run):
    tools = {}
    for name in ("python3", "node", "git", "flock"):
        path = which(name)
        tools[name] = _version(path, run) if path else {"available": False, "reason": "missing"}
    return tools


def probe_docker(*, which=shutil.which, run=subprocess.run):
    """Daemon reachability only. Unavailability is not container absence."""
    if not which("docker"):
        return {"daemon": "unavailable", "reason": "docker_cli_absent", "container": "not_observed"}
    try:
        completed = run(["docker", "info", "--format", "{{.ServerVersion}}"],
                        capture_output=True, text=True, timeout=3)
    except (OSError, subprocess.TimeoutExpired):
        return {"daemon": "unavailable", "reason": "docker_probe_failed", "container": "not_observed"}
    version = (completed.stdout or "").strip().splitlines()[:1]
    if completed.returncode != 0 or not version or len(version[0]) > 64:
        return {"daemon": "unavailable", "reason": "docker_daemon_unreachable", "container": "not_observed"}
    return {"daemon": "available", "serverVersion": version[0], "container": "not_observed"}


def observe_lock(path, *, locks_text=None):
    """Report a lease without creating or locking it."""
    if path is None:
        return {"status": "not_requested"}
    target = Path(path)
    if target.is_symlink() or (target.exists() and not target.is_file()):
        return {"status": "unknown", "reason": "unexpected_lock_path"}
    if not target.exists():
        return {"status": "absent", "created": False}
    info = target.stat()
    try:
        text = Path("/proc/locks").read_text(encoding="utf-8") if locks_text is None else locks_text
    except OSError:
        return {"status": "unknown", "reason": "lock_table_unreadable"}
    needle = f"{os.major(info.st_dev):02x}:{os.minor(info.st_dev):02x}:{info.st_ino}"
    held = False
    for line in text.splitlines():
        fields = line.split()
        if len(fields) < 6 or ":" not in fields[5]:
            return {"status": "unknown", "reason": "lock_table_unreadable"}
        if fields[5] == needle:
            held = True
    return {"status": "held" if held else "free", "created": False}


def _regular_bytes(path, limit):
    info = path.lstat()
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise ValueError("nonregular connector file")
    if not 1 <= info.st_size <= limit:
        raise ValueError("connector file size")
    data = path.read_bytes()
    if len(data) != info.st_size:
        raise ValueError("connector file changed")
    return data


def _profile_consistent(folder):
    """True only for the one real registry format, checked by its own validator.

    `provider_policy.validate_manifest` is the single definition of that format,
    so the inspector reuses it instead of restating it. Two inputs the inspector
    cannot know are taken from what it can observe: the profile identity is the
    registry directory name, and the runtime image is the manifest's own. This
    therefore proves internal consistency and artifact integrity, never agreement
    with a canonical mission configuration or an authenticated account.
    """
    if folder.is_symlink() or not folder.is_dir():
        return False
    try:
        raw = _regular_bytes(folder / "policy.json", 16384)
        manifest = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
        return False
    if not isinstance(manifest, dict) or not isinstance(manifest.get("runtimeImage"), str):
        return False
    profile = {**EXPECTED, "id": folder.name, "policySha256": hashlib.sha256(raw).hexdigest()}
    try:
        validate_manifest(raw, profile, manifest["runtimeImage"])
    except (ValueError, TypeError, KeyError):
        return False
    for name, digest in manifest["files"].items():
        try:
            content = _regular_bytes(folder / name, 65536)
        except (OSError, ValueError):
            return False
        if hashlib.sha256(content).hexdigest() != digest:
            return False
    return True


def observe_connector(policy_root):
    """Presence of a directory is not a configured connector."""
    if policy_root is None:
        return {"directoryPresent": False, "configured": False, "reason": "not_requested"}
    policy = Path(policy_root)
    if policy.is_symlink() or not policy.is_dir():
        return {"directoryPresent": False, "configured": False, "reason": "policy_root_not_directory"}
    children = [child for child in policy.iterdir() if not child.name.startswith(".")]
    if not children:
        return {"directoryPresent": True, "configured": False, "reason": "connector_content_missing"}
    validated = [child.name for child in children if _profile_consistent(child)]
    if len(validated) != 1:
        return {"directoryPresent": True, "configured": False, "reason": "connector_identity_not_validated"}
    return {"directoryPresent": True, "configured": True, "reason": "manifest_bytes_match"}


def _git(checkout, *args):
    return subprocess.run(["git", "--no-replace-objects", "-C", str(checkout), *args],
                          capture_output=True, text=True, timeout=5, env=git_environment())


def _observe_checkout(job, expected_commit, source):
    described = {"status": "present", "directoryPresent": True, "isolated": False, "jobName": job.name}
    if not any(job.iterdir()):
        described["reason"] = "empty_job_directory"
        return described
    if source is not None:
        origin = Path(source).resolve()
        resolved = job.resolve()
        if resolved == origin or origin in resolved.parents or resolved in origin.parents:
            described["reason"] = "not_outside_source"
            return described
    top = _git(job, "rev-parse", "--show-toplevel")
    head = _git(job, "rev-parse", "HEAD")
    status = _git(job, "status", "--porcelain=v1", "--untracked-files=all")
    git_dir = _git(job, "rev-parse", "--absolute-git-dir")
    if top.returncode or head.returncode or status.returncode or git_dir.returncode:
        described["reason"] = "checkout_not_validated"
        return described
    if Path(top.stdout.strip()).resolve() != job.resolve() or status.stdout.strip():
        described["reason"] = "checkout_not_clean" if status.stdout.strip() else "checkout_not_validated"
        return described
    commit = head.stdout.strip()
    if not re.fullmatch(r"[a-f0-9]{40}|[a-f0-9]{64}", commit):
        described["reason"] = "checkout_not_validated"
        return described
    alternates = Path(git_dir.stdout.strip()) / "objects" / "info" / "alternates"
    if alternates.exists():
        described["reason"] = "shared_object_store"
        return described
    if expected_commit is not None and commit != expected_commit:
        described["reason"] = "commit_identity_mismatch"
        described["observedCommit"] = commit
        return described
    described["isolated"] = True
    described["commitSha"] = commit
    described["reason"] = "clean_checkout_identity"
    return described


def _workspace(jobs_root, *, expected_commit=None, source=None):
    if jobs_root is None:
        return {"status": "not_requested", "directoryPresent": False, "isolated": False}
    root = Path(jobs_root)
    if root.is_symlink() or not root.is_dir():
        return {"status": "unknown", "directoryPresent": False, "isolated": False, "reason": "jobs_root_not_directory"}
    jobs = [child for child in root.iterdir() if child.name.startswith("job-")]
    if not jobs:
        return {"status": "not_prepared", "directoryPresent": False, "isolated": False}
    if len(jobs) != 1 or jobs[0].is_symlink() or not jobs[0].is_dir():
        return {"status": "unknown", "directoryPresent": True, "isolated": False, "reason": "ambiguous_job_directory"}
    return _observe_checkout(jobs[0], expected_commit, source)


def inspect_operator(*, dossier=None, workspace=None, executor_version=None, source=None,
                     jobs_root=None, lock_path=None, policy_root=None, which=shutil.which,
                     run=subprocess.run, locks_text=None, docker_probe=None):
    identity = None
    budget_defined = False
    expected_commit = None
    if dossier is not None:
        verified = prepare(dossier, expected_workspace=workspace,
                           expected_executor_version=executor_version, checkout=source)
        identity = {"missionId": dossier["mission"]["id"], "workspaceId": dossier["mission"]["workspaceId"],
                    "executor": dossier["executor"], "executorVersion": dossier["executorVersion"],
                    "commitSha": verified["commitSha"]}
        expected_commit = verified["commitSha"]
        budget_defined = True
    connector = observe_connector(policy_root)
    docker = docker_probe() if docker_probe is not None else probe_docker(which=which, run=run)
    if docker.get("container") != "not_observed":
        raise ValueError("Docker inspection must not invent a container observation")
    tools = probe_tools(which=which, run=run)
    workspace_state = _workspace(jobs_root, expected_commit=expected_commit, source=source)
    missing = []
    for name in ("python3", "node", "git", "flock"):
        if not tools[name].get("available"):
            missing.append(name)
    if docker["daemon"] != "available":
        missing.append("docker")
    # This command never observes the canonical store or a provider account.
    missing.extend(["provider_authentication", "execution_authorization", "canonical_claim"])
    if not connector["configured"]:
        missing.append("provider_connector")
    if not budget_defined:
        missing.append("budget")
    if not workspace_state.get("isolated"):
        missing.append("isolated_workspace")
    report = {
        "version": 1,
        "mode": "inspect",
        "outcome": "inspection_completed",
        "readyForRealMission": False,  # canonical claim and provider authentication are never proved here
        "resourcesModified": False,
        "executionRequested": False,
        "automaticRetry": False,
        "independentValidationPassed": False,
        "mission": None if identity is None else {"id": identity["missionId"], "workspaceId": identity["workspaceId"],
                                                 "commitSha": identity["commitSha"]},
        "executor": {"name": None if identity is None else identity["executor"],
                     "version": None if identity is None else identity["executorVersion"]},
        "canonicalState": "unknown",
        "canonicalSource": "unavailable",
        "docker": docker,
        "lock": observe_lock(lock_path, locks_text=locks_text),
        "prerequisites": {
            "tools": tools,
            "connectorDirectoryPresent": connector["directoryPresent"],
            "connectorConfigured": connector["configured"],
            "connectorReason": connector["reason"],
            "authenticationVerified": False,
            "authorizationPresent": False,
            "budgetDefined": budget_defined,
            "isolatedWorkspace": workspace_state,
            "plannedValidations": [
                "python -m unittest discover -s integrations/openhands-runner -p test_*.py",
                "node --test integrations/antigravity/runner.test.mjs integrations/antigravity/paperclip-adapter.test.mjs",
            ],
        },
        "blockCategory": "real_mission_not_ready",
        "nextAction": ("Inspection only. A configuration file does not prove authentication. "
                       "Do not reconcile, execute, or infer container absence while Docker or the canonical claim is unavailable."),
        "missingEvidence": missing,
    }
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dossier")
    parser.add_argument("--workspace")
    parser.add_argument("--executor-version")
    parser.add_argument("--source")
    parser.add_argument("--jobs-root")
    parser.add_argument("--lock")
    parser.add_argument("--policy-root")
    args = parser.parse_args(argv)
    supplied = [args.dossier, args.workspace, args.executor_version, args.source]
    if any(supplied) and not all(supplied):
        print(json.dumps({"status": "refused", "reason": "incomplete_dossier_binding", "resourcesModified": False}))
        return 2
    try:
        dossier = read_dossier(args.dossier) if args.dossier else None
        report = inspect_operator(dossier=dossier, workspace=args.workspace,
                                  executor_version=args.executor_version, source=args.source,
                                  jobs_root=args.jobs_root, lock_path=args.lock, policy_root=args.policy_root)
    except (InvalidDossier, ValueError, OSError, subprocess.SubprocessError):
        print(json.dumps({"status": "refused", "reason": "inspection_refused", "resourcesModified": False}))
        return 2
    print(json.dumps(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
