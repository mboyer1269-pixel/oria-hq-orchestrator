import json
import unittest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch
from project_sources import parse_sources,select_source,prepare_configuration


class ProjectSourceTests(unittest.TestCase):
    def setUp(self):
        from pathlib import Path
        self.entry=dict(workspaceId='w',projectId='p',runnerId='r',sourceRoot=str(Path.cwd().resolve()))
        self.observed=dict(claim=dict(workspaceId='w',runnerId='r'),dossier=dict(contractVersion=2,mission=dict(workspaceId='w'),memory=dict(workspaceId='w',projectId='p')))

    def test_exact_project_source_selected(self):
        entries=parse_sources(json.dumps(dict(version=1,entries=[self.entry])))
        self.assertEqual(select_source(entries,self.observed),self.entry['sourceRoot'])

    def test_foreign_or_missing_binding_never_falls_back(self):
        for field in ('workspaceId','projectId','runnerId'):
            with self.assertRaises(ValueError):select_source([{**self.entry,field:'foreign'}],self.observed)
        with self.assertRaises(ValueError):select_source([],self.observed)
        self.observed['dossier']['memory']['workspaceId']='other'
        with self.assertRaises(ValueError):select_source([self.entry],self.observed)

    def test_duplicate_and_extra_authority_refused(self):
        for entries in ([self.entry,self.entry],[{**self.entry,'command':['untrusted']}],[{**self.entry,'sourceRoot':'../repo'}]):
            with self.assertRaises(ValueError):parse_sources(json.dumps(dict(version=1,entries=entries)))
        with self.assertRaises(ValueError):parse_sources('{"version":1,"version":1,"entries":[]}')

    def test_legacy_without_memory_requires_explicit_other_profile(self):
        self.observed['dossier']={'contractVersion':1,'mission':{'workspaceId':'w'}}
        with self.assertRaises(ValueError):select_source([self.entry],self.observed)

    @unittest.skipUnless(os.name=='posix' and getattr(os,'geteuid',lambda:1)()==0,'Linux root filesystem qualification')
    def test_configuration_validates_before_lifecycle_effects(self):
        with tempfile.TemporaryDirectory(dir='/root',prefix='hq-source-test-') as folder:
            root=Path(folder)
            executable=root/'trusted';executable.write_text('fixture');executable.chmod(0o700)
            registry=root/'sources.json';registry.write_text('{}')
            jobs=root/'jobs';jobs.mkdir();controls=root/'controls';controls.mkdir()
            path=root/'prepare.json'
            config=dict(lifecycleCommand=[str(executable)],registryFile=str(registry),jobsRoot=str(jobs),controlRoot=str(controls))
            with patch('project_sources.prepare_configured_project',return_value={'state':'prepared'}) as prepare:
                path.write_text(json.dumps(config));path.chmod(0o600)
                self.assertEqual(prepare_configuration(str(path)),{'state':'prepared'})
                prepare.assert_called_once();prepare.reset_mock()
                for invalid in ({**config,'sourceRoot':'/untrusted'}, {**config,'lifecycleCommand':'shell string'}, {**config,'lifecycleCommand':['relative']}):
                    path.write_text(json.dumps(invalid))
                    with self.assertRaises((ValueError,FileNotFoundError)):prepare_configuration(str(path))
                path.write_text(json.dumps(config));path.chmod(0o666)
                with self.assertRaises(ValueError):prepare_configuration(str(path))
                prepare.assert_not_called()


if __name__=='__main__':unittest.main()
