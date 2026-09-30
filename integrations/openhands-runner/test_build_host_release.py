import json
from pathlib import Path
import shutil
import tarfile
import tempfile
import unittest
from build_host_release import release,FILES


class HostReleaseTests(unittest.TestCase):
    def test_release_is_reproducible_and_contains_only_reviewed_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);source=root/'source';source.mkdir()
            for name in FILES:shutil.copyfile(Path(__file__).parent/name,source/name)
            (source/'.env').write_text('synthetic excluded sentinel')
            first=release(source,root/'first');second=release(source,root/'second')
            self.assertEqual(first['sha256'],second['sha256']);self.assertEqual(first['releaseId'],second['releaseId'])
            with tarfile.open(first['archive']) as archive:
                self.assertEqual(set(archive.getnames()),set(FILES)|{'manifest.json'})
                self.assertTrue(all(member.isfile() and member.mode==0o444 for member in archive.getmembers()))
                self.assertEqual(set(json.load(archive.extractfile('manifest.json'))['files']),set(FILES))

    def test_new_local_import_requires_explicit_package_review(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);source=root/'source';source.mkdir()
            for name in FILES:shutil.copyfile(Path(__file__).parent/name,source/name)
            (source/'unreviewed.py').write_text('')
            with (source/'consume_pending.py').open('a') as stream:stream.write('\nimport unreviewed\n')
            with self.assertRaises(ValueError):release(source,root/'out')


if __name__=='__main__':unittest.main()
