"""Read-only compatibility check for the synthetic HQ-exported dossier."""
import json
from pathlib import Path
import sys
from dossier import prepare

if __name__ == "__main__":
    fixture = json.loads((Path(__file__).parent / "fixtures/hq-dossier.json").read_text(encoding="utf-8"))
    result = prepare(fixture, expected_workspace="synthetic-a",
                     expected_executor_version="1.50.0", checkout=sys.argv[1])
    print(json.dumps({"status": result["status"],
                      "commitVerification": result["commitVerification"],
                      "executionRequested": result["executionRequested"],
                      "approvalSatisfied": result["approvalSatisfied"]}))
