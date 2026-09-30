"""Unknown Docker outcomes must not become successful or retried executions."""
import subprocess
import unittest
from unittest.mock import Mock, patch
import supervisor

CID = "a" * 64


class SupervisorTests(unittest.TestCase):
    def test_setup_time_is_subtracted_and_external_deadline_cannot_extend_budget(self):
        for external,expected in ((105.0,3.0),(1000.0,8.0)):
            with patch.object(supervisor.time,'monotonic',side_effect=[100.0,100.5,101.0,102.0,103.0]),patch.object(
                    supervisor,'docker',return_value=Mock(stdout='openhands-supervised-job')),patch.object(
                    supervisor,'state',side_effect=[{'Status':'created'},{'Status':'exited','Running':False,'ExitCode':0}]),patch.object(
                    supervisor.subprocess,'run') as start:
                supervisor.supervise(container_id=CID,timeout_seconds=10,deadline_monotonic=external)
            self.assertEqual(start.call_args.kwargs['timeout'],expected)

    def test_inspections_share_remaining_budget(self):
        with patch.object(supervisor.time,'monotonic',side_effect=[100.0,100.5,101.5,102.0,103.0]),patch.object(
                supervisor,'docker',return_value=Mock(stdout='openhands-supervised-job')) as docker,patch.object(
                supervisor,'state',side_effect=[{'Status':'created'},{'Status':'exited','Running':False,'ExitCode':0}]) as state,patch.object(
                supervisor.subprocess,'run') as start:
            supervisor.supervise(container_id=CID,timeout_seconds=10,deadline_monotonic=103.0)
        self.assertEqual(docker.call_args_list[0].kwargs['timeout'],2.5)
        self.assertEqual(state.call_args_list[0].kwargs['timeout'],1.5)
        self.assertEqual(start.call_args.kwargs['timeout'],1.0)

    def test_slow_inspection_does_not_start_or_retry(self):
        with patch.object(supervisor.time,'monotonic',side_effect=[100.0,100.5]),patch.object(
                supervisor,'docker',side_effect=subprocess.TimeoutExpired('docker inspect',0.5)) as docker,patch.object(
                supervisor.subprocess,'run') as start:
            with self.assertRaises(subprocess.TimeoutExpired):
                supervisor.supervise(container_id=CID,timeout_seconds=1)
        self.assertEqual(docker.call_args.kwargs['timeout'],0.5)
        docker.assert_called_once()
        start.assert_not_called()

    def test_inspection_exhausts_deadline_without_starting(self):
        with patch.object(supervisor.time,'monotonic',side_effect=[100.0,111.0]),patch.object(
                supervisor,'docker',return_value=Mock(stdout='openhands-supervised-job')),patch.object(
                supervisor,'state',return_value={'Status':'created'}),patch.object(supervisor.subprocess,'run') as start:
            with self.assertRaises(TimeoutError):supervisor.supervise(container_id=CID,timeout_seconds=10)
        start.assert_not_called()

    def test_untrusted_identifiers_and_limits_rejected_before_docker(self):
        for arguments in ({"container_id": "job-name", "timeout_seconds": 1},
                          {"container_id": CID, "timeout_seconds": True},
                          {"container_id": CID, "timeout_seconds": 1801}):
            with self.subTest(arguments=arguments), patch.object(supervisor, "docker") as docker:
                with self.assertRaises(ValueError):
                    supervisor.supervise(**arguments)
                docker.assert_not_called()

    def test_wrong_owner_never_starts(self):
        with patch.object(supervisor, "docker", return_value=Mock(stdout="another-service")), \
             patch.object(supervisor.subprocess, "run") as start:
            with self.assertRaises(ValueError):
                supervisor.supervise(container_id=CID, timeout_seconds=1)
            start.assert_not_called()

    def test_daemon_lost_after_start_propagates_unknown_without_retry(self):
        with patch.object(supervisor, "docker", return_value=Mock(stdout="openhands-supervised-job")), \
             patch.object(supervisor, "state", side_effect=[{"Status": "created"},
                 subprocess.TimeoutExpired("docker inspect", 10)]), \
             patch.object(supervisor.subprocess, "run") as start:
            with self.assertRaises(subprocess.TimeoutExpired):
                supervisor.supervise(container_id=CID, timeout_seconds=1)
            start.assert_called_once()

    def test_stop_failure_is_not_reported_as_stopped(self):
        with patch.object(supervisor, "docker", side_effect=[Mock(stdout="openhands-supervised-job"),
                 subprocess.CalledProcessError(1, "docker stop")]), \
             patch.object(supervisor, "state", side_effect=[{"Status": "created"},
                 {"Status": "running", "Running": True}]), \
             patch.object(supervisor.subprocess, "run", side_effect=subprocess.TimeoutExpired("docker start", 1)) as start:
            with self.assertRaises(subprocess.CalledProcessError):
                supervisor.supervise(container_id=CID, timeout_seconds=1)
            start.assert_called_once()

    def test_failed_start_does_not_become_success(self):
        with patch.object(supervisor, "docker", return_value=Mock(stdout="openhands-supervised-job")), \
             patch.object(supervisor, "state", side_effect=[{"Status": "created"},
                 {"Status": "created", "Running": False}]), \
             patch.object(supervisor.subprocess, "run", return_value=Mock(returncode=1)):
            with self.assertRaisesRegex(RuntimeError, "requires reconciliation"):
                supervisor.supervise(container_id=CID, timeout_seconds=1)


if __name__ == "__main__":
    unittest.main()
