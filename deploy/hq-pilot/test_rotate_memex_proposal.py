import base64
import importlib.util
import json
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("renew", Path(__file__).with_name("rotate-memex-proposal.py"))
renew = importlib.util.module_from_spec(spec)
spec.loader.exec_module(renew)

def handle(**patch):
    data = dict(sub="hq-contributor", access="read_write", namespaces=[renew.NAMESPACE], exp=4600)
    data.update(patch)
    encoded = base64.urlsafe_b64encode(json.dumps(data).encode()).decode().rstrip("=")
    return "amh1." + encoded + "." + "A" * 43

class RenewalScopeTest(unittest.TestCase):
    def test_expected_short_read_scope(self):
        self.assertEqual(renew.validate_handle(handle() + "\n", 1000), handle())
    def test_overprivileged_foreign_or_expired_refused(self):
        for patch in [dict(access="read_only"), dict(namespaces=["org:other"]), dict(sub="other"), dict(exp=1000), dict(exp=90000)]:
            with self.subTest(patch=patch), self.assertRaises(ValueError):
                renew.validate_handle(handle(**patch), 1000)
    def test_bounded_format(self):
        for value in ["bad", "A" * 8193, "amh1.x." + "A" * 43]:
            with self.subTest(value=value[:12]), self.assertRaises(Exception):
                renew.validate_handle(value, 1000)

if __name__ == "__main__": unittest.main()
