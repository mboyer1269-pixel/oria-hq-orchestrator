"""Deterministic cross-process checks, using the actual Linux launch lock."""
import multiprocessing as mp
import asyncio
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from launch_lease import hold_launch, LaunchBusy
from reconcile_launch import reconcile, decide
from permission_worker import run_permission_job


def holder(path, ready, release):
    with hold_launch(path):
        ready.set()
        if not release.wait(15):
            raise RuntimeError('Barrier timed out')


@unittest.skipUnless(os.name == 'posix' and getattr(os, 'geteuid', lambda: -1)() == 0,
                     'Root-owned Linux host qualification')
class CoordinationTests(unittest.TestCase):
    def test_executor_cannot_start_during_reconciliation_or_after_closure(self):
        with tempfile.TemporaryDirectory() as tmp:
            lock=Path(tmp)/'launch.lock'
            job=dict(launchId='l',missionId='m',workspaceId='w',runnerId='r',imageDigest='i',timeoutSeconds=60)
            with patch('permission_worker.lifecycle_reader') as reader, \
                 patch('permission_worker.create_job') as create:
                with hold_launch(lock):
                    result=asyncio.run(run_permission_job(command=[],job=job,job_root=tmp,create=create))
                    self.assertEqual(result['state'],'launch_busy')
                    reader.assert_not_called();create.assert_not_called()
                reader.return_value=lambda:{'claim':{**job,'state':'cancelled'},'config':job}
                result=asyncio.run(run_permission_job(command=[],job=job,job_root=tmp,create=create))
                self.assertEqual(result['state'],'not_acquired')
                create.assert_not_called()

    def test_live_executor_blocks_reconciliation_before_docker_observation(self):
        with tempfile.TemporaryDirectory() as tmp:
            lock=Path(tmp)/'launch.lock'
            ready=mp.Event(); release=mp.Event()
            p=mp.Process(target=holder,args=(lock,ready,release));p.start()
            try:
                self.assertTrue(ready.wait(5))
                claim={'launchId':'l','missionId':'m','workspaceId':'w','runnerId':'r','state':'start_requested'}
                with patch('reconcile_launch.lifecycle_reader',return_value=lambda:{'claim':claim}), \
                     patch('reconcile_launch.lifecycle_transition') as transition, \
                     patch('reconcile_launch.observe_mission') as observe:
                    result=reconcile(command=[],job_root=tmp,lease_file=lock,observe=observe)
                    self.assertFalse(result['canonicalTerminal'])
                    observe.assert_not_called()
                    transition.return_value.assert_not_called()
                with self.assertRaises(LaunchBusy):
                    with hold_launch(lock):pass
            finally:
                release.set();p.join(5)
                if p.is_alive():p.kill();p.join()
            self.assertEqual(p.exitcode,0)
            with hold_launch(lock):pass

    def test_crash_releases_lock_but_does_not_authorize_absence_based_closure(self):
        with tempfile.TemporaryDirectory() as tmp:
            lock=Path(tmp)/'launch.lock';ready=mp.Event();release=mp.Event()
            p=mp.Process(target=holder,args=(lock,ready,release));p.start()
            try:
                self.assertTrue(ready.wait(5));p.kill();p.join(5)
                with hold_launch(lock):
                    for stage in ('creation_requested','start_requested','running'):
                        d=decide(claim={'state':stage},mission={'state':'absent'},
                                 evidence={'started':'absent'},timeout_seconds=60)
                        self.assertEqual(d['action'],'none')
                        self.assertEqual(d['reason'],'docker_effect_unresolved')
            finally:
                if p.is_alive():p.kill();p.join()

    def test_second_reconciler_cannot_enter_until_first_releases(self):
        with tempfile.TemporaryDirectory() as tmp:
            lock=Path(tmp)/'launch.lock'
            with hold_launch(lock):
                with self.assertRaises(LaunchBusy):
                    with hold_launch(lock):pass
            with hold_launch(lock):pass

if __name__=='__main__':unittest.main()
