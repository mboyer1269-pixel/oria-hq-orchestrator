"""Linux-only isolated ownership/credential provisioning checks; no runtime paths."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("review_provision", Path(__file__).with_name("provision-memex-review.py"))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


@unittest.skipUnless(os.name == "posix" and os.geteuid() == 0, "Linux root required for actual ownership checks")
class ProvisionTests(unittest.TestCase):
    def test_scoped_files_and_no_overwrite(self):
        with tempfile.TemporaryDirectory(prefix="hq-review-credential-test-") as temp:
            memex, hq = Path(temp) / "memex", Path(temp) / "hq"
            module.provision(memex, hq, "org:workspace:fixture")
            config = json.loads((memex / "credential.json").read_text())
            self.assertEqual(config["token"], (hq / "token").read_text().strip())
            self.assertRegex(config["token"], r"^opr1\.[A-Za-z0-9_-]{43}$")
            self.assertEqual(config["namespace"], "org:workspace:fixture")
            for directory, name, uid, gid in [(memex, "credential.json", 1000, 1000), (hq, "token", 100, 101)]:
                self.assertEqual(directory.stat().st_mode & 0o777, 0o750)
                self.assertEqual(directory.stat().st_uid, 0)
                file = directory / name
                self.assertEqual(file.stat().st_mode & 0o777, 0o400)
                self.assertEqual((file.stat().st_uid, file.stat().st_gid), (uid, gid))
            with self.assertRaises(ValueError):
                module.provision(memex, hq, "org:workspace:fixture")
            self.assertEqual(config, json.loads((memex / "credential.json").read_text()))

    def test_invalid_paths_and_namespace_leave_no_files(self):
        with tempfile.TemporaryDirectory(prefix="hq-review-credential-test-") as temp:
            first, second = Path(temp) / "one", Path(temp) / "two"
            for namespace in ["*", "org:workspace:", "org:workspace:a\n"]:
                with self.assertRaises(ValueError):
                    module.provision(first, second, namespace)
            with self.assertRaises(ValueError):
                module.provision(first, first, "org:workspace:fixture")
            link = Path(temp) / "link"
            link.symlink_to(Path(temp), target_is_directory=True)
            with self.assertRaises(ValueError):
                module.provision(link / "one", second, "org:workspace:fixture")
            self.assertFalse(first.exists())
            self.assertFalse(second.exists())


if __name__ == "__main__":
    unittest.main()
