import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from provider_policy import (EXPECTED,FILES,PROVIDER_POLICIES,authorized_profile,load_provider_policy,
                             provider_preflight,validate_authorization,validate_manifest,validate_profile)


def build_fixture(provider,image,*,profile_id):
    template=PROVIDER_POLICIES[provider]
    manifest={**template,'version':1,'agentNetwork':'none','runtimeImage':image,
        'proxyImage':'sha256:'+'b'*64,'relayPort':3129,'socketPath':'/provider/provider.sock',
        'files':{name:hashlib.sha256(b'fixture').hexdigest() for name in FILES}}
    raw=json.dumps(manifest,sort_keys=True,separators=(',',':')).encode()
    profile={**template,'id':profile_id,'policySha256':hashlib.sha256(raw).hexdigest()}
    return manifest,raw,profile


class ProviderPolicyTests(unittest.TestCase):
    def setUp(self):
        self.image='sha256:'+'a'*64
        self.manifest,self.raw,self.profile=build_fixture('claude',self.image,profile_id='test-policy')
        self.config={'providerProfile':self.profile,'imageDigest':self.image}

    def test_exact_policy_and_runtime_match(self):
        self.assertEqual(validate_manifest(self.raw,self.profile,self.image),self.manifest)
        with self.assertRaises(ValueError):validate_manifest(self.raw,self.profile,'sha256:'+'c'*64)
        with self.assertRaises(ValueError):validate_manifest(self.raw+b' ',self.profile,self.image)

    def test_matching_hash_cannot_authorize_weakened_or_unknown_policy(self):
        for change in ({'agentNetwork':'host'},{'accountConnectors':'enabled'},{'version':True},
                       {'relayPort':443},{'token':'synthetic'},{'proxyImage':'latest'},
                       {'files':{'../escape':'a'*64}}):
            raw=json.dumps({**self.manifest,**change},sort_keys=True,separators=(',',':')).encode()
            profile={**self.profile,'policySha256':hashlib.sha256(raw).hexdigest()}
            with self.assertRaises(ValueError):validate_manifest(raw,profile,self.image)

    def test_codex_profile_is_explicit_and_matches_only_its_own_template(self):
        codex_image='sha256:'+'d'*64
        codex_manifest,codex_raw,codex_profile=build_fixture('codex',codex_image,profile_id='codex-test-policy')
        self.assertEqual(validate_manifest(codex_raw,codex_profile,codex_image),codex_manifest)
        self.assertEqual(codex_profile['provider'],'codex')
        self.assertNotEqual(codex_profile,self.profile)
        # Weakening the Codex template the same way the Claude template is
        # weakened elsewhere must be refused too - the second entry is its own
        # fully-checked policy, not a copy that happens to validate by accident.
        for change in ({'authentication':'api-key'},{'network':'open'},{'accountConnectors':'enabled'}):
            raw=json.dumps({**codex_manifest,**change},sort_keys=True,separators=(',',':')).encode()
            profile={**codex_profile,'policySha256':hashlib.sha256(raw).hexdigest()}
            with self.assertRaises(ValueError):validate_manifest(raw,profile,codex_image)

    def test_unknown_provider_is_refused_not_silently_widened(self):
        unknown_profile={**self.profile,'provider':'gemini'}
        with self.assertRaises(ValueError):validate_profile(unknown_profile)
        with self.assertRaises(ValueError):validate_manifest(self.raw,unknown_profile,self.image)

    def test_claude_policy_or_relay_can_never_be_presented_as_codex(self):
        codex_image='sha256:'+'d'*64
        codex_manifest,codex_raw,codex_profile=build_fixture('codex',codex_image,profile_id='codex-test-policy')
        # A profile that declares provider "codex" but whose approved digest
        # actually names a Claude-shaped manifest (every other field Claude's,
        # including the manifest's own internal provider field) must never
        # validate: no Claude relay/proxy artifact, however exactly it was
        # qualified, can stand in for Codex just because the surrounding
        # profile fields happen to be identical across both templates.
        raw=json.dumps(self.manifest,sort_keys=True,separators=(',',':')).encode()
        mislabeled_profile={**codex_profile,'policySha256':hashlib.sha256(raw).hexdigest()}
        self.assertIsNone(validate_profile(mislabeled_profile))
        with self.assertRaises(ValueError):validate_manifest(raw,mislabeled_profile,self.image)
        # And the reverse: a Codex-shaped manifest can never satisfy a profile
        # that declares provider "claude", even with a matching digest.
        reversed_profile={**self.profile,'policySha256':codex_profile['policySha256']}
        with self.assertRaises(ValueError):validate_manifest(codex_raw,reversed_profile,codex_image)

    def test_duplicate_keys_noncanonical_json_and_profile_traversal_rejected(self):
        for raw in (self.raw.replace(b'{',b'{"version":1,',1),self.raw+b'\n'):
            with self.assertRaises(ValueError):validate_manifest(raw,{**self.profile,'policySha256':hashlib.sha256(raw).hexdigest()},self.image)
        with self.assertRaises(ValueError):validate_manifest(self.raw,{**self.profile,'id':'../other'},self.image)

    def test_verified_manifest_never_enables_execution(self):
        with patch('provider_policy.load_provider_policy',return_value=self.manifest) as load:
            self.assertEqual(provider_preflight(self.config),{'state':'unsupported_provider_profile','started':False})
            load.assert_called_once_with(self.config)
        with patch('provider_policy.load_provider_policy',side_effect=ValueError('mismatch')):
            self.assertEqual(provider_preflight(self.config),{'state':'invalid_provider_policy','started':False})
        self.assertIsNone(provider_preflight({'imageDigest':self.image}))

    def test_operator_authorization_shape_is_strict(self):
        approved={'profileId':self.profile['id'],'policySha256':self.profile['policySha256'],
                  'policyRoot':'/etc/oria-hq/provider-policies','gatewayRoot':'/srv/oria-hq-gateways'}
        self.assertEqual(validate_authorization(approved),approved)
        for broken in ({**approved,'gatewayRoot':'relative'},{**approved,'gatewayRoot':'/srv/../escape'},
                       {**approved,'gatewayRoot':'/srv/gateways/'},{**approved,'gatewayRoot':''},
                       {**approved,'policyRoot':'relative'},{**approved,'policyRoot':'/etc/../escape'},
                       {**approved,'policyRoot':approved['gatewayRoot']},
                       {**approved,'profileId':'../other'},{**approved,'policySha256':'A'*64},
                       {**approved,'token':'synthetic'},{'profileId':approved['profileId']},None):
            with self.assertRaises(ValueError):validate_authorization(broken)

    def test_authorization_must_name_the_canonical_profile(self):
        approved={'profileId':self.profile['id'],'policySha256':self.profile['policySha256'],
                  'policyRoot':'/etc/oria-hq/provider-policies','gatewayRoot':'/srv/oria-hq-gateways'}
        self.assertEqual(authorized_profile(self.config,approved),self.profile)
        for changed in ({'id':'other-policy'},{'policySha256':'b'*64}):
            with self.assertRaises(ValueError):authorized_profile({**self.config,'providerProfile':{**self.profile,**changed}},approved)
        with self.assertRaises(ValueError):authorized_profile({'imageDigest':self.image},approved)

    def test_approved_policy_clears_preflight_while_unapproved_never_does(self):
        approved={'profileId':self.profile['id'],'policySha256':self.profile['policySha256'],
                  'policyRoot':'/etc/oria-hq/provider-policies','gatewayRoot':'/srv/oria-hq-gateways'}
        with patch('provider_policy.load_provider_policy',return_value=self.manifest) as load:
            self.assertIsNone(provider_preflight(self.config,approved))
            # The approved registry is read, not the compiled-in default.
            load.assert_called_once_with(self.config,approved['policyRoot'])
            # A profile the operator did not approve is refused, not downgraded to
            # the earlier verifier-only refusal, and never allocates a job.
            self.assertEqual(provider_preflight(self.config,{**approved,'policySha256':'b'*64}),
                             {'state':'invalid_provider_policy','started':False})
        with patch('provider_policy.load_provider_policy',side_effect=ValueError('mismatch')):
            self.assertEqual(provider_preflight(self.config,approved),{'state':'invalid_provider_policy','started':False})
        self.assertIsNone(provider_preflight({'imageDigest':self.image},approved))

    @unittest.skipUnless(os.name=='posix' and hasattr(os,'geteuid') and os.geteuid()==0,'Linux protected filesystem')
    def test_real_protected_artifacts_tampering_permissions_and_symlink(self):
        # /tmp is intentionally unacceptable: every ancestor must be protected.
        with tempfile.TemporaryDirectory(dir='/root') as temporary:
            root=Path(temporary);folder=root/self.profile['id'];folder.mkdir(mode=0o700)
            (folder/'policy.json').write_bytes(self.raw)
            for name in FILES:(folder/name).write_bytes(b'fixture')
            self.assertEqual(load_provider_policy(self.config,root),self.manifest)
            artifact=folder/'relay.mjs';artifact.write_bytes(b'changed')
            with self.assertRaises(ValueError):load_provider_policy(self.config,root)
            artifact.write_bytes(b'fixture');artifact.chmod(0o666)
            with self.assertRaises(ValueError):load_provider_policy(self.config,root)
            artifact.chmod(0o600);artifact.unlink();artifact.symlink_to(folder/'squid.conf')
            with self.assertRaises(ValueError):load_provider_policy(self.config,root)
            artifact.unlink();artifact.write_bytes(b'fixture');folder.chmod(0o777)
            with self.assertRaises(ValueError):load_provider_policy(self.config,root)
            folder.chmod(0o700)


if __name__=='__main__':unittest.main()
