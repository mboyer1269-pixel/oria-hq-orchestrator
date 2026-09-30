import os
import subprocess
import sys
import time
import unittest
from unittest.mock import Mock,patch
from provider_relay import monitor,run_relay_job,stop


class RelayTests(unittest.TestCase):
    def test_relay_loss_takes_precedence_over_unverified_worker_exit(self):
        self.assertEqual(monitor(Mock(poll=lambda:1),Mock(poll=lambda:0)),70)

    def test_worker_exit_is_preserved_when_transport_alive(self):
        self.assertEqual(monitor(Mock(poll=lambda:None),Mock(poll=lambda:7)),7)

    @unittest.skipUnless(os.name=='posix','Linux process groups')
    def test_real_process_relay_loss_is_observed_and_worker_terminated(self):
        relay=subprocess.Popen([sys.executable,'-c','import time;time.sleep(.1)'],start_new_session=True)
        worker=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)'],start_new_session=True)
        started=time.monotonic()
        try:self.assertEqual(monitor(relay,worker),70)
        finally:stop(worker);stop(relay)
        self.assertIsNotNone(worker.poll());self.assertLess(time.monotonic()-started,5)

    @unittest.skipUnless(os.name=='posix','Linux runtime')
    def test_fixed_proxy_environment_and_account_connectors_disabled(self):
        relay=Mock(pid=111,poll=lambda:None);worker=Mock(pid=222,poll=lambda:0)
        with patch.dict(os.environ,{'HTTPS_PROXY':'http://untrusted','ALL_PROXY':'http://other','NO_PROXY':'*'}),patch(
                'provider_relay.subprocess.Popen',side_effect=[relay,worker]) as spawn,patch(
                'provider_relay.select.select',return_value=([relay.stdout],[],[])),patch(
                'provider_relay.os.read',return_value=b'ready\n'),patch('provider_relay.stop'):
            self.assertEqual(run_relay_job(['--dossier','/mission.json','--workspace-id','fixture']),0)
        environment=spawn.call_args_list[1].kwargs['env']
        self.assertEqual(environment['HTTPS_PROXY'],'http://127.0.0.1:3129')
        self.assertEqual(environment['ENABLE_CLAUDEAI_MCP_SERVERS'],'false')
        self.assertEqual(environment['NO_PROXY'],'');self.assertNotIn('ALL_PROXY',environment)
        self.assertTrue(spawn.call_args_list[1].kwargs['start_new_session'])

    @unittest.skipUnless(os.name=='posix','Linux runtime')
    def test_unready_relay_never_starts_mission(self):
        relay=Mock()
        with patch('provider_relay.subprocess.Popen',return_value=relay) as spawn,patch(
                'provider_relay.select.select',return_value=([],[],[])),patch('provider_relay.stop'):
            self.assertEqual(run_relay_job([]),70)
        spawn.assert_called_once()


if __name__=='__main__':unittest.main()
