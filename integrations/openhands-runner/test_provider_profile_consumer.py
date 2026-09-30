import unittest
from unittest.mock import Mock,patch
from consume_pending import consume


class ProviderProfileConsumerTests(unittest.TestCase):
    def test_unsupported_profile_does_not_allocate_or_prepare_a_job(self):
        for profile in ({'id':'claude-subscription-v1'},None,{}):
            root=Mock()
            with patch('consume_pending.prepare_configured_project') as prepare,patch(
                    'consume_pending.execute_configuration') as execute:
                result=consume({'profile':{'config':{'providerProfile':profile}},'hostConfigRoot':root},{})
            self.assertEqual(result,{'state':'invalid_provider_policy','started':False})
            self.assertEqual(root.mock_calls,[])
            prepare.assert_not_called();execute.assert_not_called()


if __name__=='__main__':unittest.main()
