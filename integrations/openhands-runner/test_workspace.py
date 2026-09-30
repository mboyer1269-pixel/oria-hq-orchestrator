import subprocess
import tempfile
from pathlib import Path
import unittest
from workspace import prepare_workspace


class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name)
        self.source=self.base/"source"
        self.source.mkdir()
        self.jobs=self.base/"jobs"
        self.jobs.mkdir()
        self.git("init")
        (self.source/"content.txt").write_text("old",encoding="utf-8")
        self.commit()
        self.old=self.git("rev-parse","HEAD")
        (self.source/"content.txt").write_text("new",encoding="utf-8")
        self.commit()
        self.new=self.git("rev-parse","HEAD")
        (self.source/"untracked.txt").write_text("preserve",encoding="utf-8")

    def git(self,*args):
        return subprocess.run(["git","-C",str(self.source),*args],check=True,capture_output=True,text=True,timeout=5).stdout.strip()

    def commit(self):
        self.git("add","content.txt")
        self.git("-c","user.name=Fixture","-c","user.email=fixture@example.invalid","-c","commit.gpgsign=false","commit","-m","fixture")

    def prepare(self,**kwargs):
        return prepare_workspace(source=self.source,commit=kwargs.get("commit",self.old),
                                 server_root=self.jobs,job_name=kwargs.get("job_name","job-1"))

    def test_exact_old_commit_without_source_changes(self):
        before=self.git("status","--porcelain")
        result=self.prepare()
        self.assertEqual((Path(result["checkout"])/"content.txt").read_text(),"old")
        self.assertFalse((Path(result["checkout"])/"untracked.txt").exists())
        self.assertEqual(self.git("rev-parse","HEAD"),self.new)
        self.assertEqual(self.git("status","--porcelain"),before)
        self.assertEqual((self.source/"content.txt").read_text(),"new")
        self.assertTrue(result["clean"])
        self.assertFalse(result["executionRequested"])

    def test_existing_destination_refused(self):
        (self.jobs/"job-1").mkdir()
        with self.assertRaises(FileExistsError): self.prepare()

    def test_agent_clone_has_no_remote_or_shared_object_store(self):
        result = self.prepare()
        checkout = Path(result["checkout"])
        remotes = subprocess.check_output(["git", "-C", str(checkout), "remote"], text=True)
        self.assertEqual(remotes.strip(), "")
        self.assertFalse((checkout / ".git/objects/info/alternates").exists())
        pushed = subprocess.run(["git", "-C", str(checkout), "push"], capture_output=True, text=True, timeout=5)
        self.assertNotEqual(pushed.returncode, 0)
        self.assertEqual(self.git("rev-parse", "HEAD"), self.new)

    def test_escape_refused(self):
        with self.assertRaises(ValueError): self.prepare(job_name="../escape")

    def test_missing_commit_refused(self):
        with self.assertRaises(subprocess.CalledProcessError): self.prepare(commit="1"*40)
        self.assertFalse((self.jobs/"job-1").exists())

    def test_source_root_destination_refused(self):
        before=self.git("status","--porcelain")
        with self.assertRaises(ValueError):
            prepare_workspace(source=self.source,commit=self.old,server_root=self.source,job_name="job-1")
        self.assertFalse((self.source/"job-1").exists())
        self.assertEqual(self.git("status","--porcelain"),before)

    def test_source_subdirectory_destination_refused(self):
        nested=self.source/"jobs"
        nested.mkdir()
        before=self.git("status","--porcelain")
        with self.assertRaises(ValueError):
            prepare_workspace(source=self.source,commit=self.old,server_root=nested,job_name="job-1")
        self.assertFalse((nested/"job-1").exists())
        self.assertEqual(self.git("status","--porcelain"),before)


if __name__=="__main__": unittest.main()
