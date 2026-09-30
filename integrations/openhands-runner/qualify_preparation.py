"""Synthetic HQ dossier to isolated exact-commit workspace, without execution."""
import json
from pathlib import Path
import sys
import tempfile
from dossier import prepare
from workspace import prepare_workspace

if __name__ == "__main__":
    dossier = json.loads((Path(__file__).parent / "fixtures/hq-dossier.json").read_text(encoding="utf-8"))
    validated = prepare(dossier, expected_workspace="synthetic-a",
                        expected_executor_version="1.50.0", checkout=sys.argv[1])
    # This script cleans only its own synthetic TemporaryDirectory, not a job.
    with tempfile.TemporaryDirectory(prefix="hq-preparation-probe-") as root:
        workspace = prepare_workspace(source=sys.argv[1], commit=validated["commitSha"],
                                      server_root=root, job_name="synthetic-mission")
        assert workspace["commitSha"] == dossier["source"]["commitSha"]
        assert (Path(workspace["checkout"]) / "README.md").read_text() == "# Synthetic qualification project\n"
        print(json.dumps({"hqDossierAccepted": True, "exactCommitCheckedOut": True,
                          "clean": workspace["clean"], "executionRequested": False,
                          "approvalSatisfied": False, "modelCalls": 0}))
