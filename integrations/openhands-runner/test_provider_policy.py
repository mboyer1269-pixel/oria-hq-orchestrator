import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from provider_policy import EXPECTED,FILES,load_provider_policy,provider_preflight,validate_manifest


class ProviderPolicyTests(unittest.TestCase):
    def setUp(self):
        self.image='sha256:'+'a'*64
        self.manifest={**EXPECTED,'version':1,'agentNetwork':'none','runtimeImage':self.image,
            'proxyImage':'sha256:'+'b'*64,'relayPort':3129,'socketPath':'/provider/provider.sock',
            'files':{name:hashlib.sha256(b'fixture').hexdigest() for name in FILES}}
        self.raw=json.dumps(self.manifest,sort_keys=True,separators=(',',':')).encode()
        self.profile={**EXPECTED,'id':'test-policy','policySha256':hashlib.sha256(self.raw).hexdigest()}
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
