import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock,patch
from consume_pending import consume

APPROVED={'profileId':'claude-subscription-v1','policySha256':'a'*64,
          'policyRoot':'/etc/oria-hq/provider-policies','gatewayRoot':'/srv/oria-hq-gateways'}
PROFILE={'id':APPROVED['profileId'],'policySha256':APPROVED['policySha256'],'provider':'claude',
         'authentication':'subscription','network':'restricted-proxy','accountConnectors':'disabled'}
LAUNCH='11111111-1111-4111-8111-111111111111'


class ProviderProfileConsumerTests(unittest.TestCase):
    def refused(self,config,expected):
        root=Mock()
        with patch('consume_pending.prepare_configured_project') as prepare,patch(
                'consume_pending.execute_configuration') as execute:
            result=consume({**config,'hostConfigRoot':root},{})
        self.assertEqual(result,expected)
        # Nothing is allocated: no per-launch directory, checkout or execution.
        self.assertEqual(root.mock_calls,[])
        prepare.assert_not_called();execute.assert_not_called()

    def test_unsupported_profile_does_not_allocate_or_prepare_a_job(self):
        for profile in ({'id':'claude-subscription-v1'},None,{}):
            self.refused({'profile':{'config':{'providerProfile':profile}}},
                         {'state':'invalid_provider_policy','started':False})

    def test_profile_without_operator_authorization_keeps_the_earlier_refusal(self):
        with patch('provider_policy.load_provider_policy',return_value={}):
            self.refused({'profile':{'config':{'providerProfile':PROFILE}}},
                         {'state':'unsupported_provider_profile','started':False})

    def test_profile_other_than_the_authorized_one_is_refused_before_allocation(self):
        for changed in ({'id':'claude-subscription-v2'},{'policySha256':'b'*64},{'network':'host'}):
            with patch('provider_policy.load_provider_policy',return_value={}):
                self.refused({'profile':{'config':{'providerProfile':{**PROFILE,**changed}}},'providerExecution':APPROVED},
                             {'state':'invalid_provider_policy','started':False})

    def test_authorized_profile_is_carried_into_preparation_once(self):
        with tempfile.TemporaryDirectory() as folder:
            host=Path(folder)
            config={'profile':{'context':{},'config':{'providerProfile':PROFILE}},'providerExecution':APPROVED,
                    'hostConfigRoot':host,'bridgeCommand':['/usr/bin/node'],'bridgeScriptsRoot':'/opt/scripts',
                    'bridgeConfigRoot':'/config','registryFile':Path('/etc/sources.json'),
                    'jobsRoot':Path('/srv/jobs'),'controlRoot':Path('/run/control')}
            job={'launchId':LAUNCH,'missionId':'mission','payloadHash':'c'*64,'authorizationExpiresAt':'2026-09-30T00:00:00Z'}
            execute=Mock(return_value='coroutine')
            with patch('provider_policy.load_provider_policy',return_value={}),patch(
                    'consume_pending.prepare_configured_project',
                    return_value={'operatorConfig':'/srv/jobs/'+LAUNCH+'/operator.json'}) as prepare,patch(
                    'consume_pending.execute_configuration',execute),patch(
                    'consume_pending.asyncio.run',return_value={'state':'execution_finished'}) as runner:
                result=consume(config,job)
            execute.assert_called_once_with('/srv/jobs/'+LAUNCH+'/operator.json')
            runner.assert_called_once_with('coroutine')
            self.assertEqual(result,{'state':'execution_finished'})
            self.assertEqual(prepare.call_args.kwargs['provider_execution'],APPROVED)
            self.assertEqual(prepare.call_args.kwargs['expected_payload_hash'],job['payloadHash'])
            written=json.loads((host/LAUNCH/'lifecycle.json').read_text(encoding='utf-8'))
            # The canonical lifecycle file carries the mission profile, never the
            # operator authorization or the host gateway path.
            self.assertEqual(written['config']['providerProfile'],PROFILE)
            self.assertNotIn('providerExecution',written)
            self.assertNotIn(APPROVED['gatewayRoot'],json.dumps(written))


if __name__=='__main__':unittest.main()
