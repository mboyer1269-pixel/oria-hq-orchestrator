import copy
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from dossier import prepare, InvalidDossier, digest

FIXTURE = json.loads((Path(__file__).parent/"fixtures"/"hq-dossier.json").read_text(encoding="utf-8"))


class DossierTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.git("init")
        self.git("-c","user.name=Qualification","-c","user.email=qualification@example.invalid",
                 "-c","commit.gpgsign=false","commit","--allow-empty","-m","Synthetic fixture")
        self.commit = self.git("rev-parse","HEAD").strip()
        self.data = copy.deepcopy(FIXTURE)
        self.data["source"]["commitSha"] = self.commit
        self.rehash()

    def git(self,*args):
        return subprocess.run(["git","-C",str(self.root),*args],check=True,capture_output=True,text=True,timeout=5).stdout

    def rehash(self):
        self.data["payloadHash"] = digest({k:v for k,v in self.data.items() if k not in ("payloadHash","idempotencyKey")})

    def receive(self):
        return prepare(self.data,expected_workspace=FIXTURE["mission"]["workspaceId"],
                       expected_executor_version=FIXTURE["executorVersion"],checkout=self.root)

    def test_prepared_does_not_execute(self):
        result=self.receive()
        self.assertEqual(result["status"],"prepared")
        self.assertFalse(result["executionRequested"])
        self.assertFalse(result["approvalSatisfied"])

    def test_missing_commit(self):
        self.data["source"]["commitSha"]="1"*40
        self.rehash()
        with self.assertRaises(InvalidDossier): self.receive()

    def test_workspace_mismatch(self):
        self.data["mission"]["workspaceId"]="wrong"
        with self.assertRaises(InvalidDossier): self.receive()

    def test_tampering(self):
        for mutate in (lambda d:d.update(payloadHash="0"*64),lambda d:d.update(idempotencyKey="bad"),
                       lambda d:d["mission"].update(objective="tampered")):
            original=copy.deepcopy(self.data)
            mutate(self.data)
            with self.assertRaises(InvalidDossier): self.receive()
            self.data=original

    def test_strict_budget(self):
        for value in (True,0,200001,1.5):
            self.data["budget"]["maxTokens"]=value
            with self.assertRaises(InvalidDossier): self.receive()

    def test_unknown_field(self):
        self.data["secret"]="not-accepted"
        with self.assertRaises(InvalidDossier): self.receive()

    def test_git_environment_cannot_redirect_repository(self):
        with tempfile.TemporaryDirectory() as other:
            subprocess.run(["git","-C",other,"init"],check=True,capture_output=True,timeout=5)
            subprocess.run(["git","-C",other,"-c","user.name=Other","-c","user.email=other@example.invalid",
                            "-c","commit.gpgsign=false","commit","--allow-empty","-m","Different commit"],check=True,capture_output=True,timeout=5)
            foreign=subprocess.run(["git","-C",other,"rev-parse","HEAD"],check=True,capture_output=True,text=True,timeout=5).stdout.strip()
            self.data["source"]["commitSha"]=foreign
            self.rehash()
            with patch.dict("os.environ", {"GIT_DIR":str(Path(other)/".git"),
                                           "GIT_WORK_TREE":str(self.root)}):
                with self.assertRaises(InvalidDossier): self.receive()


class MemoryDossierTests(DossierTests):
    def setUp(self):
        super().setUp()
        self.data = json.loads((Path(__file__).parent/"fixtures"/"hq-memory-dossier.json").read_text(encoding="utf-8"))
        self.data["source"]["commitSha"] = self.commit
        self.rehash()

    def receive(self):
        return prepare(self.data, expected_workspace="synthetic-a", expected_executor_version="1.50.0", checkout=self.root)

    def test_memory_tampering_even_with_rehashed_outer_payload(self):
        for patch in ({"content":"{}"}, {"workspaceId":"foreign"}, {"contentChars":1},
                      {"retrievedAtIso":"invalid"}, {"redactionsApplied":True}, {"unknown":1}):
            original=copy.deepcopy(self.data)
            self.data["memory"].update(patch)
            self.rehash()
            with self.assertRaises(InvalidDossier): self.receive()
            self.data=original

    def test_memory_cannot_be_removed_or_downgraded_without_new_payload(self):
        del self.data["memory"]
        with self.assertRaises(InvalidDossier): self.receive()
        self.data["contractVersion"]=1
        with self.assertRaises(InvalidDossier): self.receive()


if __name__=="__main__": unittest.main()
