import base64
import importlib.util
import json
from pathlib import Path
import unittest
import os
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('project_rotation',Path(__file__).with_name('rotate-project-memory-read.py'))
rotation=importlib.util.module_from_spec(spec)
spec.loader.exec_module(rotation)

def envelope(**changes):
    payload={'sub':rotation.SUBJECT,'access':'read_only','namespaces':[rotation.NAMESPACE],'exp':4500}
    payload.update(changes)
    encoded=base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip('=')
    # Synthetic signature: this test checks narrowing, not signature validation.
    return 'amh1.'+encoded+'.'+'a'*43

class ScopeTests(unittest.TestCase):
    def test_exact_project(self):
        token=envelope()
        self.assertEqual(rotation.validate_handle(token,1000),token)

    def test_broad_foreign_write_or_bad_expiry_rejected(self):
        for change in ({'namespaces':['org:workspace:michael-hq']},
                       {'namespaces':[rotation.NAMESPACE,'org:project:foreign']},
                       {'namespaces':['org:project:foreign']},
                       {'access':'read_write'},{'sub':'other'},
                       {'exp':True},{'exp':1000},{'exp':10000}):
            with self.subTest(change=change),self.assertRaises(ValueError):
                rotation.validate_handle(envelope(**change),1000)

@unittest.skipUnless(os.name=='posix' and getattr(os,'geteuid',lambda:-1)()==0,'Requires isolated Linux root fixture')
class AtomicRotationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='hq-project-handle-test-')
        self.directory=Path(self.temp.name)
        os.chown(self.directory,0,1000);os.chmod(self.directory,0o750)
        self.handle=self.directory/'handle'
        self.handle.write_text('previous-synthetic-handle\n')
        self.original_inode=self.handle.stat().st_ino

    def tearDown(self):self.temp.cleanup()

    def invoke(self,output,code=0):
        with patch.object(rotation,'DIRECTORY',self.directory),patch.object(rotation.time,'time',return_value=1000),patch.object(rotation.subprocess,'run',return_value=SimpleNamespace(returncode=code,stdout=output)) as run:
            rotation.rotate()
            args=run.call_args.args[0]
            self.assertEqual(args[-3:],[rotation.SUBJECT,rotation.NAMESPACE,'3600'])
            self.assertEqual(run.call_args.kwargs['timeout'],20)

    def test_success_replaces_atomically_and_limits_reader_permissions(self):
        token=envelope();self.invoke(token)
        info=self.handle.stat()
        self.assertEqual(self.handle.read_text(),token+'\n')
        self.assertNotEqual(info.st_ino,self.original_inode)
        self.assertEqual((info.st_uid,info.st_gid,info.st_mode&0o777),(1000,1000,0o400))
        self.assertEqual(list(self.directory.glob('.handle-*')),[])

    def test_signer_failure_keeps_previous_handle(self):
        with self.assertRaises(RuntimeError):self.invoke('',1)
        self.assertEqual(self.handle.read_text(),'previous-synthetic-handle\n')
        self.assertEqual(self.handle.stat().st_ino,self.original_inode)

    def test_wrong_scope_keeps_previous_handle(self):
        with self.assertRaises(ValueError):self.invoke(envelope(namespaces=['org:workspace:michael-hq']))
        self.assertEqual(self.handle.read_text(),'previous-synthetic-handle\n')
        self.assertEqual(self.handle.stat().st_ino,self.original_inode)

if __name__=='__main__':unittest.main()
