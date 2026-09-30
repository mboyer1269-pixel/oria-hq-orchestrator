import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from dossier import digest


class PreparationCLITests(unittest.TestCase):
    def test_prepare_then_conflict_preserves_first_checkout(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            source.mkdir()
            jobs = root / "jobs"
            jobs.mkdir()
            def git(*args):
                return subprocess.check_output(["git", "-C", str(source), *args], text=True, stderr=subprocess.DEVNULL).strip()
            git("init")
            (source / "README.md").write_text("synthetic\n")
            git("add", "README.md")
            git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "-c", "commit.gpgsign=false", "commit", "-m", "fixture")
            data = json.loads((Path(__file__).parent / "fixtures/hq-dossier.json").read_text(encoding="utf-8"))
            data = copy.deepcopy(data)
            data["source"]["commitSha"] = git("rev-parse", "HEAD")
            data["payloadHash"] = digest({k: v for k, v in data.items() if k not in ("payloadHash", "idempotencyKey")})
            request = root / "request.json"
            request.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            command = [sys.executable, str(Path(__file__).with_name("prepare_job.py")),
                       "--dossier", str(request), "--workspace", "synthetic-a", "--executor-version", "1.50.0",
                       "--source", str(source), "--jobs-root", str(jobs)]
            first = subprocess.run(command, capture_output=True, text=True, timeout=20)
            self.assertEqual(first.returncode, 0, first.stderr)
            checkout = Path(json.loads(first.stdout)["checkout"])
            (checkout / "agent-work.txt").write_text("preserve work")
            second = subprocess.run(command, capture_output=True, text=True, timeout=20)
            self.assertEqual(second.returncode, 3)
            self.assertEqual(json.loads(second.stderr)["status"], "preparation_conflict")
            self.assertEqual((checkout / "agent-work.txt").read_text(), "preserve work")
            self.assertEqual(len(list(jobs.iterdir())), 1)


if __name__ == "__main__":
    unittest.main()
