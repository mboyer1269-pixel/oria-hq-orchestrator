"""Operator-only preparation CLI. No provider credentials or agent execution."""
import argparse
import json
import subprocess
import sys
from dossier import prepare
from request_io import read_dossier
from workspace import prepare_workspace


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("dossier", "workspace", "executor-version", "source", "jobs-root"):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args()
    dossier = read_dossier(args.dossier)
    verified = prepare(dossier, expected_workspace=args.workspace,
                       expected_executor_version=args.executor_version, checkout=args.source)
    # Deterministic destination prevents silent reuse of a previous attempt.
    key = verified["idempotencyKey"].removeprefix("hq-openhands-v1-")
    checkout = prepare_workspace(source=args.source, commit=verified["commitSha"],
                                 server_root=args.jobs_root, job_name="job-" + key)
    print(json.dumps({**verified, "checkout": checkout["checkout"], "clean": checkout["clean"],
                      "durableLaunchReserved": False, "budgetsEnforced": False}))


if __name__ == "__main__":
    try:
        main()
    except FileExistsError:
        print(json.dumps({"status": "preparation_conflict", "executionRequested": False}), file=sys.stderr)
        sys.exit(3)
    except (ValueError, OSError, subprocess.SubprocessError):
        # Do not expose raw Git output, internal paths or partial dossier content.
        # Any newly created workspace remains available for operator inspection.
        print(json.dumps({"status": "preparation_failed", "executionRequested": False}), file=sys.stderr)
        sys.exit(2)
