"""Patch safeguards must remain active with Python -O."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
import apply_patch
import apply_budget_patch


class PatchGuardTests(unittest.TestCase):
    def test_wrong_source_never_modified(self):
        for module in (apply_patch, apply_budget_patch):
            with self.subTest(module=module.__name__), tempfile.TemporaryDirectory() as root:
                source = Path(root) / "sdk.py"
                original = b"# unexpected SDK source\n"
                source.write_bytes(original)
                dist = Mock(version="1.50.0")
                dist.locate_file.return_value = source
                with patch.object(module.importlib.metadata, "distribution", return_value=dist):
                    with self.assertRaises(RuntimeError):
                        module.main()
                self.assertEqual(source.read_bytes(), original)

    def test_wrong_version_never_reads_source(self):
        for module in (apply_patch, apply_budget_patch):
            with self.subTest(module=module.__name__):
                dist = Mock(version="1.51.0")
                with patch.object(module.importlib.metadata, "distribution", return_value=dist):
                    with self.assertRaisesRegex(RuntimeError, "Unsupported SDK version"):
                        module.main()
                dist.locate_file.assert_not_called()


if __name__ == "__main__":
    unittest.main()
