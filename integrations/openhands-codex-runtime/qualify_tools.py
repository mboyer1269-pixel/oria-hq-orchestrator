"""Exercise real development tools as non-root; no model or package download."""
import json
import os
from pathlib import Path
import subprocess
import tempfile


def run(args, cwd, *, expected=0):
    result = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=15)
    if result.returncode != expected:
        raise RuntimeError("Development tool returned unexpected status: " + args[0])
    return result.stdout.strip()


assert os.getuid() == 10001
with tempfile.TemporaryDirectory(prefix="hq-tools-") as work:
    root = Path(work)
    (root / "package.json").write_text(json.dumps({"private": True, "type": "module",
        "scripts": {"test": "node --test"}}))
    (root / "sum.js").write_text("export const sum = (a, b) => a + b;\n")
    (root / "sum.test.js").write_text("import test from 'node:test'; import assert from 'node:assert/strict'; import {sum} from './sum.js'; test('sum', () => assert.equal(sum(2,3),5));\n")
    run(["git", "init", "--quiet"], work)
    run(["git", "add", "."], work)
    run(["git", "-c", "user.name=Qualification", "-c", "user.email=qualification@example.invalid",
         "-c", "commit.gpgsign=false", "commit", "--quiet", "-m", "Synthetic baseline"], work)
    run(["npm", "test", "--offline"], work)
    (root / "sum.js").write_text("export const sum = (a, b) => a - b;\n")
    run(["npm", "test", "--offline"], work, expected=1)
    (root / "sum.js").write_text("export const sum = (a, b) => Number(a) + Number(b);\n")
    run(["npm", "test", "--offline"], work)
    assert run(["git", "diff", "--name-only"], work) == "sum.js"
    print(json.dumps({"nonRoot": True, "gitCommitCreated": True, "npmTestPassed": True,
                      "introducedFailureDetected": True, "correctedChangePassed": True,
                      "diffScopedToExpectedFile": True, "modelCalls": 0}))
