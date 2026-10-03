"""Metadata-only fixtures; no credential file, CLI login, Docker or provider I/O."""
import asyncio
from contextlib import contextmanager
import copy
import hashlib
import json
import os
from pathlib import Path
import socket
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock,Mock,patch
from provider_policy import (EXPECTED,validate_authorization,validate_auth_context,
                             bound_auth_context,inspect_auth_directory)
from container_job import create_job
from permission_worker import run_permission_job
from run_host_job import load_configuration


def context(**changes):
    return dict(reference='claude-account-a',provider='claude',workspaceId='workspace-a',
                profileId='claude-profile',policySha256='a'*64,directory='/protected/auth',**changes)


def authorization(auth=None):
    return dict(profileId='claude-profile',policySha256='a'*64,policyRoot='/policies',
                gatewayRoot='/gateways',authContext=context() if auth is None else auth)


def config():
    return dict(providerProfile={**EXPECTED,'id':'claude-profile','policySha256':'a'*64},
                permissionPolicy='deny',imageDigest='sha256:'+'a'*64,timeoutSeconds=30)


@contextmanager
def unheld(_path):
    yield


class AuthContractTests(unittest.IsolatedAsyncioTestCase):
    def test_reference_binds_only_claude_workspace_profile_and_policy(self):
        approved=authorization()
        self.assertEqual(bound_auth_context(config(),approved,'workspace-a'),approved['authContext'])
        for change in ({'provider':'codex'},{'profileId':'other'},{'policySha256':'b'*64},
                       {'reference':'../other'},{'token':'forbidden-value'},
                       {'directory':'/root/a,readonly=false'},{'directory':'/root/a/../b'}):
            with self.assertRaises(ValueError):validate_authorization(authorization({**context(),**change}))
        for workspace,change in (('other',{}),('workspace-a',{'permissionPolicy':'review'}),
                                 ('workspace-a',{'providerProfile':{**config()['providerProfile'],'id':'other'}})):
            with self.assertRaises(ValueError):bound_auth_context({**config(),**change},approved,workspace)

    async def test_mismatched_authentication_refuses_before_effects(self):
        job=dict(launchId='launch',missionId='mission',workspaceId='workspace-a',runnerId='runner',
                 imageDigest='sha256:'+'a'*64,timeoutSeconds=30)
        for change in ({'permissionPolicy':'review'}, {'permissionPolicy':None},
                       {'providerProfile':{**config()['providerProfile'],'id':'other'}}):
            create=Mock();run=Mock()
            with patch('permission_worker.lifecycle_reader',return_value=lambda:dict(claim={**job,'state':'claimed'},config={**config(),**change})),patch(
                    'permission_worker.load_provider_policy'),patch('permission_worker.provider_gateway') as gateway,patch(
                    'permission_worker.lifecycle_transition') as transition,patch('permission_worker.inspect_auth_directory') as inspect:
                result=await run_permission_job(command=['trusted'],job=job,job_root='/job',create=create,run=run,
                    authorization=authorization(),gateway_root='/gateways',policy_root='/policies',lease=unheld)
            self.assertEqual(result,{'state':'invalid_provider_policy','started':False})
            create.assert_not_called();run.assert_not_called();gateway.assert_not_called();transition.assert_not_called();inspect.assert_not_called()

    async def test_worker_passes_exact_context_and_refuses_changed_binding_before_creation(self):
        job=dict(launchId='launch',missionId='mission',workspaceId='workspace-a',runnerId='runner',
                 imageDigest='sha256:'+'a'*64,timeoutSeconds=30)
        for changed in (False,True):
            reads=0;approved=authorization();create=Mock(return_value={'containerId':'b'*64,'containerName':'job'})
            def reader(_command,include_config=False):
                def read():
                    nonlocal reads
                    reads+=1
                    latest=config()
                    if changed and reads>1:latest['providerProfile']['policySha256']='b'*64
                    return dict(claim={**job,'state':'claimed'},config=latest)
                return read if include_config else lambda:dict(state='claimed')
            def dispatch(**kwargs):
                kwargs['create'](launch_id=job['launchId'],workspace_id=job['workspaceId'],image_digest=job['imageDigest'],
                    job_root='/job',deadline_monotonic=100)
                return {'state':'fixture_created'}
            @contextmanager
            def gateway(**_kwargs):yield {'fixture':True}
            with patch('permission_worker.lifecycle_reader',side_effect=reader),patch('permission_worker.load_provider_policy'),patch(
                    'permission_worker.inspect_auth_directory',return_value=(1,2)),patch('permission_worker.provider_gateway',side_effect=gateway),patch(
                    'permission_worker.dispatch',side_effect=dispatch),patch('permission_worker.lifecycle_transition'):
                result=await run_permission_job(command=['trusted'],job=job,job_root='/job',create=create,
                    authorization=approved,gateway_root='/gateways',policy_root='/policies',lease=unheld)
            if changed:
                self.assertEqual(result['state'],'reconciliation_required');create.assert_not_called()
            else:
                self.assertEqual(result['state'],'fixture_created')
                self.assertEqual(create.call_args.kwargs['auth_context'],approved['authContext'])
                self.assertEqual(create.call_args.kwargs['auth_directory_identity'],(1,2))
                self.assertEqual(create.call_args.kwargs['permission_policy'],'deny')
            self.assertNotIn('/protected/auth',json.dumps(result))
            self.assertNotIn('claude-account-a',json.dumps(result))


@unittest.skipUnless(os.name=='posix' and getattr(os,'geteuid',lambda:1)()==0,'Linux root metadata tests')
class AuthDirectoryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir='/root',prefix='hq-auth-fixture-');self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.auth=self.root/'auth';self.auth.mkdir(mode=0o700);os.chown(self.auth,10001,10001)
        self.context={**context(),'directory':str(self.auth)}

    def test_metadata_only_private_directory_no_file_reads_or_listing(self):
        with patch.object(Path,'read_bytes',side_effect=AssertionError('file read')),patch.object(
                Path,'read_text',side_effect=AssertionError('file read')),patch.object(Path,'iterdir',side_effect=AssertionError('listing')):
            identity=inspect_auth_directory(self.context)
        self.assertEqual(identity,(self.auth.stat().st_dev,self.auth.stat().st_ino))
        for mode in (0o777,0o755,0o600):
            self.auth.chmod(mode)
            with self.assertRaises(ValueError):inspect_auth_directory(self.context)
        self.auth.chmod(0o700)
        link=self.root/'linked';link.symlink_to(self.auth)
        with self.assertRaises(ValueError):inspect_auth_directory({**self.context,'directory':str(link)})

    def test_parent_may_be_the_leafs_own_owner_but_never_a_third_uid(self):
        # Matches the real deployment shape confirmed empirically against
        # the actual candidate image: the dedicated account's own HOME
        # directly owns the leaf's parent (uid10001, mode755 - no group/
        # other write), because the official CLI itself writes
        # ~/.claude.json and ~/.claude.json.lock there on every invocation,
        # even plain --version/auth status. Demanding every ancestor be
        # root-owned would refuse every real deployment, not just an
        # unusually lax one.
        home=self.root/'home';home.mkdir(mode=0o755);os.chown(home,10001,10001)
        leaf=home/'.claude';leaf.mkdir(mode=0o700);os.chown(leaf,10001,10001)
        own_context={**context(),'directory':str(leaf)}
        identity=inspect_auth_directory(own_context)
        self.assertEqual(identity,(leaf.stat().st_dev,leaf.stat().st_ino))
        # A THIRD uid - neither root nor the leaf's own owner - is still
        # refused outright, even with otherwise-identical safe mode bits.
        os.chown(home,65534,65534)
        with self.assertRaises(ValueError):inspect_auth_directory(own_context)
        # Restoring the leaf's own owner on the parent is accepted again...
        os.chown(home,10001,10001)
        inspect_auth_directory(own_context)
        # ...but a group/other write bit on that same-uid parent is still
        # refused - "same owner as the leaf" never substitutes for "not
        # writable by anyone else".
        home.chmod(0o775)
        with self.assertRaises(ValueError):inspect_auth_directory(own_context)

    def test_host_config_rejects_overlap_before_any_launch(self):
        job=self.root/'job';job.mkdir();control=self.root/'control';control.mkdir()
        policies=self.root/'policies';policies.mkdir();gateway=self.root/'gateway';gateway.mkdir()
        executable=self.root/'trusted';executable.write_text('fixture');executable.chmod(0o700)
        approved={**authorization(self.context),'policyRoot':str(policies),'gatewayRoot':str(gateway)}
        filename=self.root/'operator.json'
        operator=dict(lifecycleCommand=[str(executable)],jobRoot=str(job),reviewSocket=str(control/'review.sock'),providerExecution=approved)
        filename.write_text(json.dumps(operator));filename.chmod(0o600)
        self.assertEqual(load_configuration(filename)[3]['authContext'],self.context)
        nested=job/'auth';nested.mkdir(mode=0o700);os.chown(nested,10001,10001)
        operator['providerExecution']['authContext']={**self.context,'directory':str(nested)}
        filename.write_text(json.dumps(operator))
        with self.assertRaises(ValueError):load_configuration(filename)

    def test_actual_create_arguments_mount_only_auth_directory_readonly(self):
        job=self.root/'job';job.mkdir();(job/'checkout').mkdir();(job/'results').mkdir();(job/'dossier.json').write_text('{}')
        launch='11111111-1111-4111-8111-111111111111';folder=self.root/launch;folder.mkdir()
        ipc=folder/'ipc';ipc.mkdir(mode=0o700);os.chown(ipc,10001,10001)
        sock=socket.socket(socket.AF_UNIX);self.addCleanup(sock.close);sock.bind(str(ipc/'provider.sock'))
        os.chown(ipc/'provider.sock',10001,10001);(ipc/'provider.sock').chmod(0o600)
        relay=folder/'relay.mjs';relay.write_bytes(b'fixture')
        image='sha256:'+'a'*64;proxy='sha256:'+'c'*64
        provider=dict(containerId='c'*64,networkId='d'*64,ipcPath=str(ipc),relayPath=str(relay),
            policy=dict(provider='claude',runtimeImage=image,proxyImage=proxy,files={'relay.mjs':hashlib.sha256(b'fixture').hexdigest()}))
        args=dict(launch_id=launch,image_digest=image,workspace_id='workspace-a',job_root=job,
                  provider=provider,auth_context=self.context,permission_policy='deny',auth_directory_identity=inspect_auth_directory(self.context))
        with patch('container_job.docker',side_effect=[SimpleNamespace(stdout=json.dumps([True,proxy,launch,'provider-gateway'])),SimpleNamespace(stdout='b'*64)]) as docker:
            result=create_job(**args)
        command=docker.call_args.args
        self.assertIn(f'type=bind,src={self.auth},dst=/home/runner/.claude,readonly',command)
        self.assertNotIn('--env',command);self.assertIn('none',command);self.assertIn('--read-only',command)
        self.assertIn('--subscription-auth',command)
        self.assertNotIn(str(self.auth),json.dumps(result))
        for change in ({'provider':None},{'permission_policy':'review'},{'workspace_id':'other'},{'auth_directory_identity':(0,0)}):
            with patch('container_job.docker') as docker:
                with self.assertRaises(ValueError):create_job(**{**args,**change})
                docker.assert_not_called()


if __name__=='__main__':unittest.main()
