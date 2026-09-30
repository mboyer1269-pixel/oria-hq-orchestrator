import copy
import unittest
import os
import tempfile
import json
import uuid
from pathlib import Path
from unittest.mock import Mock
from recovery_report import recovery_report
from recovery_report import publish_report


class RecoveryTests(unittest.TestCase):
    @unittest.skipUnless(os.name=='posix' and hasattr(os,'geteuid') and os.geteuid()==0,'Linux root publisher')
    def test_atomic_protected_publication(self):
        with tempfile.TemporaryDirectory(dir='/root') as directory:
            report={'launchId':str(uuid.uuid4()),'status':'observed'}
            publish_report(report,directory)
            target=Path(directory)/(report['launchId']+'.json')
            self.assertEqual(json.loads(target.read_text()),report)
            self.assertEqual(target.stat().st_mode&0o777,0o444)
            report['status']='changed_during_inspection';publish_report(report,directory)
            self.assertEqual(json.loads(target.read_text()),report)
            self.assertEqual(len(list(Path(directory).iterdir())),1)

    def setUp(self):
        self.observed={'claim':dict(launchId='launch',missionId='mission',workspaceId='workspace',runnerId='runner',state='start_requested'),
                       'config':{'providerProfile':{'id':'policy'}}}

    def test_observation_never_authorizes_retry_or_success(self):
        inspect=Mock(return_value={'containerState':'absent','networkState':'absent'})
        result=recovery_report(command=['trusted'],gateway_root='/root/gateways',read=Mock(return_value=self.observed),inspect=inspect)
        self.assertEqual(result['canonicalState'],'start_requested');self.assertEqual(result['status'],'observed')
        for key in ('resumeAuthorized','automaticRetry','resourcesModified','independentValidationPassed'):self.assertFalse(result[key])
        self.assertNotIn('providerProfile',str(result));inspect.assert_called_once_with(root='/root/gateways',launch_id='launch')

    def test_concurrent_canonical_change_is_reported(self):
        changed=copy.deepcopy(self.observed);changed['claim']['state']='execution_finished'
        result=recovery_report(command=['trusted'],gateway_root='/root/gateways',read=Mock(side_effect=[self.observed,changed]),inspect=Mock(return_value={}))
        self.assertEqual(result['status'],'changed_during_inspection');self.assertFalse(result['canonicalObservationStable'])

    def test_missing_journal_is_unknown(self):
        result=recovery_report(command=['trusted'],gateway_root='/root/gateways',read=Mock(return_value=self.observed),inspect=Mock(side_effect=FileNotFoundError()))
        self.assertEqual(result['gateway']['containerState'],'unknown');self.assertTrue(result['gateway']['reconciliationRequired'])

    def test_offline_config_does_not_inspect_gateway(self):
        self.observed['config']={};inspect=Mock()
        result=recovery_report(command=['trusted'],gateway_root='/root/gateways',read=Mock(return_value=self.observed),inspect=inspect)
        self.assertIsNone(result['gateway']);inspect.assert_not_called()


if __name__=='__main__':unittest.main()
