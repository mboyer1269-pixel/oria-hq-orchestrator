import tempfile
from pathlib import Path
import unittest
from request_io import read_dossier, MAX_DOSSIER_BYTES


class RequestIOTests(unittest.TestCase):
    def read(self, content):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "request.json"
            path.write_bytes(content)
            return read_dossier(path)

    def test_valid_unicode(self):
        self.assertEqual(self.read('{"title":"é🧪"}'.encode()), {"title": "é🧪"})

    def test_duplicate_fields_at_any_depth(self):
        for body in (b'{"a":1,"a":2}', b'{"mission":{"id":1,"id":2}}'):
            with self.assertRaises(ValueError): self.read(body)

    def test_invalid_or_oversized_input(self):
        for body in (b'{"n":NaN}', b'{"n":Infinity}', b'\xff', b' ' * (MAX_DOSSIER_BYTES + 1)):
            with self.assertRaises(ValueError): self.read(body)


if __name__ == "__main__":
    unittest.main()
