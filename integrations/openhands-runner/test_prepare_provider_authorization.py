"""Preparation refuses an unapproved provider profile before any launch effect."""
import unittest
from pathlib import Path
from unittest.mock import Mock,patch
import prepare_host_job as module
from provider_policy import EXPECTED

LAUNCH='11111111-1111-4111-8111-111111111111'
APPROVED={'profileId':'claude-subscription-v1','policySha256':'a'*64,
          'policyRoot':'/etc/oria-hq/provider-policies','gatewayRoot':'/srv/oria-hq-gateways'}
PROFILE={**EXPECTED,'id':APPROVED['profileId'],'policySha256':APPROVED['policySha256']}


class Reached(Exception):
    """Raised by the dossier verifier fixture: the authorization guard let the job through."""


class PreparationAuthorizationTests(unittest.TestCase):
    def attempt(self,*,config,provider_execution):
        system=Mock();system.name='posix';system.geteuid.return_value=0
        reader=Mock(return_value=lambda:dict(claim={'state':'claimed','launchId':LAUNCH,'payloadHash':'c'*64,'workspaceId':'workspace'},
                                             config=config,dossier={'mission':{'id':'mission'}}))
        verifier=Mock(side_effect=Reached())
        with patch.object(module,'os',system),patch.object(module,'protected_path',lambda raw,directory=False:Path(raw)),patch.object(
                module,'lifecycle_reader',reader),patch.object(module,'prepare',verifier),patch.object(
                module,'prepare_workspace',Mock()):
            with self.assertRaises(Exception) as raised:
                module.prepare_host_job(command=['/usr/bin/node','/opt/trusted.mjs'],source='/srv/source',
                                        jobs_root='/srv/jobs',control_root='/run/control',
                                        provider_execution=provider_execution)
        return raised.exception,reader,verifier

    def test_canonical_profile_without_authorization_never_reaches_preparation(self):
        error,reader,verifier=self.attempt(config={'executorVersion':'1.50.0','providerProfile':PROFILE},provider_execution=None)
        self.assertIsInstance(error,ValueError);verifier.assert_not_called();reader.assert_called_once()

    def test_altered_or_foreign_profile_never_reaches_preparation(self):
        for changed in ({'id':'claude-subscription-v2'},{'policySha256':'b'*64},{'network':'host'}):
            error,_,verifier=self.attempt(config={'executorVersion':'1.50.0','providerProfile':{**PROFILE,**changed}},
                                          provider_execution=APPROVED)
            self.assertIsInstance(error,ValueError);verifier.assert_not_called()

    def test_malformed_authorization_refused_before_the_lifecycle_subprocess(self):
        for broken in ({**APPROVED,'gatewayRoot':'relative'},{**APPROVED,'extra':1},{'profileId':'claude-subscription-v1'}):
            error,reader,verifier=self.attempt(config={'executorVersion':'1.50.0'},provider_execution=broken)
            self.assertIsInstance(error,ValueError);reader.assert_not_called();verifier.assert_not_called()

    def test_gateway_root_sharing_a_runtime_subtree_is_refused_before_creation(self):
        for shared in ('/srv/jobs','/srv/jobs/deeper','/run/control','/srv','/srv/source'):
            error,reader,verifier=self.attempt(config={'executorVersion':'1.50.0','providerProfile':PROFILE},
                                              provider_execution={**APPROVED,'gatewayRoot':shared})
            self.assertIsInstance(error,ValueError)
            # Refused before the lifecycle subprocess, so no launch is claimed and
            # no partial job or control directory can be left behind.
            reader.assert_not_called();verifier.assert_not_called()

    def test_approved_profile_and_legacy_offline_job_both_continue(self):
        for config,authorization in (({'executorVersion':'1.50.0','providerProfile':PROFILE},APPROVED),
                                     ({'executorVersion':'1.50.0'},None)):
            error,_,verifier=self.attempt(config=config,provider_execution=authorization)
            self.assertIsInstance(error,Reached);verifier.assert_called_once()


if __name__=='__main__':unittest.main()
