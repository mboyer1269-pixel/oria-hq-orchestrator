import tempfile
import os
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from container_job import create_job


class ContainerJobTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve()
        (self.root/'checkout').mkdir();(self.root/'results').mkdir()
        (self.root/'dossier.json').write_text('{}')
        self.args=dict(launch_id='11111111-1111-4111-8111-111111111111',
                      image_digest='sha256:'+'a'*64,workspace_id='fixture',job_root=self.root)

    @patch('container_job.docker')
    def test_creates_without_start_or_credentials(self,docker):
        docker.return_value=SimpleNamespace(stdout='b'*64+'\n')
        result=create_job(**self.args)
        self.assertFalse(result['started'])
        args=docker.call_args.args
        self.assertEqual(args[0],'create');self.assertNotIn('start',args)
        self.assertIn('none',args);self.assertNotIn('--env',args)
        self.assertEqual(sum(arg=='--mount' for arg in args),3)

    @patch('container_job.docker')
    @unittest.skipUnless(hasattr(os,'getuid') and os.getuid()==0,'Linux host-owned mount')
    def test_channel_mount_is_readonly_and_world_writable_path_denied(self,docker):
        ipc=self.root/'ipc';ipc.mkdir(mode=0o755)
        docker.return_value=SimpleNamespace(stdout='b'*64)
        create_job(**self.args,permission_channel=True)
        self.assertIn(f'type=bind,src={ipc},dst=/ipc,readonly',docker.call_args.args)
        self.assertEqual(docker.call_args.args[-1],'--permission-channel')
        ipc.chmod(0o777);docker.reset_mock()
        with self.assertRaises(ValueError):create_job(**self.args,permission_channel=True)
        docker.assert_not_called()

    @patch('container_job.docker')
    def test_missing_channel_directory_prevents_creation(self,docker):
        with self.assertRaises((ValueError,FileNotFoundError)):
            create_job(**self.args,permission_channel=True)
        docker.assert_not_called()

    @patch('container_job.docker')
    def test_channel_flag_must_be_host_boolean(self,docker):
        with self.assertRaises(ValueError):create_job(**self.args,permission_channel='true')
        docker.assert_not_called()

    @patch('container_job.docker')
    def test_unpinned_image_rejected_before_docker(self,docker):
        self.args['image_digest']='latest'
        with self.assertRaises(ValueError):create_job(**self.args)
        docker.assert_not_called()

    @patch('container_job.docker')
    def test_unknown_result_never_retries(self,docker):
        docker.return_value=SimpleNamespace(stdout='unknown')
        with self.assertRaises(RuntimeError):create_job(**self.args)
        docker.assert_called_once()

if __name__=='__main__':unittest.main()
