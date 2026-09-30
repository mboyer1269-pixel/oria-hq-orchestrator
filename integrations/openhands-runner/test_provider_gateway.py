import hashlib
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock,patch
import uuid
from provider_gateway import provider_gateway
from provider_policy import EXPECTED,FILES


@unittest.skipUnless(os.name=='posix' and hasattr(os,'geteuid') and os.geteuid()==0,'Linux protected gateway paths')
class GatewayTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir='/root');self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.policies=self.root/'policies';self.policies.mkdir()
        folder=self.policies/'test';folder.mkdir()
        raw=b'fixture';digest=hashlib.sha256(raw).hexdigest()
        policy={**EXPECTED,'version':1,'agentNetwork':'none','runtimeImage':'sha256:'+'a'*64,
            'proxyImage':'sha256:'+'b'*64,'relayPort':3129,'socketPath':'/provider/provider.sock','files':dict.fromkeys(FILES,digest)}
        manifest=json.dumps(policy,sort_keys=True,separators=(',',':')).encode()
        (folder/'policy.json').write_bytes(manifest)
        for name in FILES:(folder/name).write_bytes(raw)
        self.config={'imageDigest':policy['runtimeImage'],'timeoutSeconds':10,'providerProfile':{**EXPECTED,'id':'test','policySha256':hashlib.sha256(manifest).hexdigest()}}
        self.launch=str(uuid.uuid4())
        self.args={'config':self.config,'launch_id':self.launch,'root':self.root,'policy_root':self.policies}
        def call(*args,**kwargs):return SimpleNamespace(stdout=('c'*64 if args[0]=='network' else 'd'*64)+'\n')
        self.docker=Mock(side_effect=call)

    def journal(self):return json.loads((self.root/self.launch/'lifecycle.json').read_text())

    def test_closes_on_success_and_retains_record_without_retry(self):
        with patch('provider_gateway.docker',self.docker),patch('provider_gateway.wait_ready'):
            with provider_gateway(**self.args) as gateway:
                self.assertEqual(gateway['containerId'],'d'*64)
                self.assertEqual(self.journal()['state'],'ready')
                self.assertEqual(self.journal()['lifetimeSeconds'],25)
            self.assertEqual(self.journal()['state'],'closed')
            count=self.docker.call_count
            with self.assertRaises(FileExistsError):
                with provider_gateway(**self.args):pass
            self.assertEqual(self.docker.call_count,count)
        self.assertEqual(self.docker.call_args_list[-2].args,('rm','-f','d'*64))
        self.assertEqual(self.docker.call_args_list[-1].args,('network','rm','c'*64))
        created=next(call.args for call in self.docker.call_args_list if call.args[0]=='create')
        self.assertIn('/usr/bin/timeout',created);self.assertIn('--kill-after=5s',created);self.assertIn('25s',created)

    def test_body_failure_closes_known_resources(self):
        with patch('provider_gateway.docker',self.docker),patch('provider_gateway.wait_ready'):
            with self.assertRaisesRegex(RuntimeError,'synthetic failure'):
                with provider_gateway(**self.args):raise RuntimeError('synthetic failure')
        self.assertEqual(self.journal()['state'],'closed')

    def test_creation_consuming_deadline_cleans_without_start(self):
        clock=[100.0]
        def call(*args,**kwargs):
            if args[0]=='create':clock[0]=111.0
            return SimpleNamespace(stdout=('c'*64 if args[0]=='network' else 'd'*64))
        self.docker.side_effect=call
        with patch('provider_gateway.time.monotonic',side_effect=lambda:clock[0]),patch('provider_gateway.docker',self.docker):
            with self.assertRaises(TimeoutError):
                with provider_gateway(**self.args,deadline_monotonic=110):pass
        self.assertFalse(any(call.args[0]=='start' for call in self.docker.call_args_list))
        self.assertEqual(self.journal()['state'],'closed')
        self.assertEqual(self.docker.call_args_list[-2].args,('rm','-f','d'*64))

    def test_preparation_commands_consume_same_remaining_budget(self):
        clock=[100.0]
        def call(*args,**kwargs):
            if args[:2]==('network','create'):clock[0]+=2
            elif args[0]=='create':clock[0]+=3
            return SimpleNamespace(stdout=('c'*64 if args[0]=='network' else 'd'*64))
        self.docker.side_effect=call
        with patch('provider_gateway.time.monotonic',side_effect=lambda:clock[0]),patch('provider_gateway.docker',self.docker),patch('provider_gateway.wait_ready') as ready:
            with provider_gateway(**self.args,deadline_monotonic=110):pass
        creates=[call for call in self.docker.call_args_list if call.args[0] in ('network','create','start')][:3]
        self.assertEqual([call.kwargs['timeout'] for call in creates],[10,8,5])
        self.assertEqual(ready.call_args.kwargs['timeout'],5)

    def test_uncertain_create_never_starts_or_removes_unknown_container(self):
        self.docker.side_effect=[SimpleNamespace(stdout='c'*64),RuntimeError('lost reply'),SimpleNamespace(stdout='')]
        with patch('provider_gateway.docker',self.docker):
            with self.assertRaisesRegex(RuntimeError,'lost reply'):
                with provider_gateway(**self.args):pass
        self.assertEqual(self.journal()['state'],'reconciliation_required')
        self.assertFalse(any(call.args[0] in ('start','rm') for call in self.docker.call_args_list))

    def test_cleanup_failure_is_not_reported_as_closed(self):
        def call(*args,**kwargs):
            if args[0]=='rm':raise RuntimeError('daemon unavailable')
            return SimpleNamespace(stdout=('c'*64 if args[0]=='network' else 'd'*64))
        self.docker.side_effect=call
        with patch('provider_gateway.docker',self.docker),patch('provider_gateway.wait_ready'):
            with self.assertRaisesRegex(RuntimeError,'reconciliation'):
                with provider_gateway(**self.args):pass
        self.assertEqual(self.journal()['state'],'reconciliation_required')

    def test_invalid_policy_has_no_resource_effect(self):
        self.config['providerProfile']['policySha256']='f'*64
        with patch('provider_gateway.docker',self.docker):
            with self.assertRaises(ValueError):
                with provider_gateway(**self.args):pass
        self.docker.assert_not_called();self.assertFalse((self.root/self.launch).exists())

    def test_long_socket_path_refused_before_resource_creation(self):
        root=self.root/('long-'*15);root.mkdir()
        with patch('provider_gateway.docker',self.docker):
            with self.assertRaisesRegex(ValueError,'socket path limit'):
                with provider_gateway(**{**self.args,'root':root}):pass
        self.docker.assert_not_called();self.assertFalse((root/self.launch).exists())

    def test_unbounded_or_noninteger_deadline_refused_before_resources(self):
        for duration in (None,True,0,1801,1.5,'30'):
            with patch('provider_gateway.docker',self.docker):
                with self.assertRaisesRegex(ValueError,'deadline'):
                    with provider_gateway(**{**self.args,'config':{**self.config,'timeoutSeconds':duration}}):pass
        self.docker.assert_not_called();self.assertFalse((self.root/self.launch).exists())


if __name__=='__main__':unittest.main()
