import json
import unittest
import uuid
from types import SimpleNamespace
from unittest.mock import patch
from provider_gateway import inspect_gateway


class InspectionTests(unittest.TestCase):
    def setUp(self):
        self.launch=str(uuid.uuid4());self.name='hq-provider-'+self.launch
        self.journal={'launchId':self.launch,'name':self.name,'state':'ready','containerId':'a'*64,'networkId':'b'*64}

    def inspect(self, replies):
        with patch('provider_gateway.protected_bytes',return_value=json.dumps(self.journal).encode()),patch('provider_gateway.docker',side_effect=[SimpleNamespace(stdout=json.dumps(x) if not isinstance(x,str) else x) for x in replies]) as docker:
            result=inspect_gateway(root='/root/gateways',launch_id=self.launch)
        self.assertTrue(all(c.args[0] in ('ps','inspect','network') for c in docker.call_args_list))
        self.assertFalse(result['resourcesModified']);self.assertFalse(result['automaticRetry'])
        return result

    def test_stale_ready_journal_with_absent_resources(self):
        result=self.inspect(['',''])
        self.assertEqual(result['containerState'],'absent');self.assertFalse(result['reconciliationRequired'])
        self.assertEqual(result['journalState'],'ready')

    def test_stopped_proxy_still_requires_resource_reconciliation(self):
        result=self.inspect(['a'*64,['a'*64,'/'+self.name,{'oria.purpose':'provider-gateway','oria.launch-id':self.launch},'exited'],
                             'b'*64,['b'*64,self.name,{'oria.purpose':'provider-gateway'},{}]])
        self.assertEqual(result['containerState'],'exited');self.assertTrue(result['reconciliationRequired'])

    def test_same_name_foreign_identity_not_trusted(self):
        result=self.inspect(['a'*64,['a'*64,'/'+self.name,{'oria.purpose':'foreign'},'running'],''])
        self.assertEqual(result['containerState'],'identity_mismatch');self.assertTrue(result['reconciliationRequired'])

    def test_daemon_failure_is_unknown_not_absent(self):
        with patch('provider_gateway.protected_bytes',return_value=json.dumps(self.journal).encode()),patch('provider_gateway.docker',side_effect=RuntimeError('offline')):
            result=inspect_gateway(root='/root/gateways',launch_id=self.launch)
        self.assertEqual(result['containerState'],'unknown');self.assertTrue(result['inspectionIncomplete'])
        self.assertTrue(result['reconciliationRequired'])


if __name__=='__main__':unittest.main()
