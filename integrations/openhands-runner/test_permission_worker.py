import asyncio
import unittest
from datetime import datetime,timezone,timedelta
from contextlib import contextmanager
from unittest.mock import AsyncMock,Mock,patch
from permission_worker import run_permission_job


class WorkerTests(unittest.IsolatedAsyncioTestCase):
    async def test_gateway_only_after_acquisition_shares_deadline_and_closes(self):
        for mode in ('success','lost_claim','run_failure','cleanup_failure'):
            state='claimed';events=[];deadlines=[]
            job=dict(launchId='fixture',missionId='fixture',workspaceId='fixture',runnerId='fixture',imageDigest='fixture',timeoutSeconds=10)
            config={**job,'providerProfile':{'id':'fixture'}}
            def transition(before,after,data):
                nonlocal state
                if mode=='lost_claim':return False
                self.assertEqual(state,before);state=after;events.append(after);return True
            def reader(command,include_config=False):
                if include_config:return lambda:dict(claim={**job,'state':state},config=config)
                return lambda:dict(state=state,containerId='a'*64,startRequestedAt=datetime.now(timezone.utc).isoformat(),
                    authorizationExpiresAt=(datetime.now(timezone.utc)+timedelta(seconds=60)).isoformat())
            @contextmanager
            def gateway(**parameters):
                self.assertEqual(state,'creation_requested');events.append('gateway_open')
                deadlines.append(parameters['deadline_monotonic'])
                try:yield {'fixture':True}
                finally:
                    events.append('gateway_closed')
                    if mode=='cleanup_failure':raise RuntimeError('cleanup unknown')
            def create(**parameters):
                self.assertEqual(parameters['provider'],{'fixture':True});deadlines.append(parameters['deadline_monotonic'])
                return {'containerId':'a'*64,'containerName':'fixture'}
            def run(**parameters):
                deadlines.append(parameters['deadline_monotonic'])
                if mode=='run_failure':raise RuntimeError('run unknown')
                return {'exitCode':0,'containerStopped':True,'deadlineExceeded':False}
            server=Mock(wait_closed=AsyncMock())
            with patch('permission_worker.load_provider_policy'),patch('permission_worker.provider_gateway',side_effect=gateway) as factory,patch(
                    'permission_worker.lifecycle_transition',return_value=transition),patch('permission_worker.lifecycle_reader',side_effect=reader):
                result=await run_permission_job(command=['trusted'],job=job,job_root='/fixture',create=create,run=run,
                    serve=AsyncMock(return_value=server),gateway_root='/protected',policy_root='/policies')
            if mode=='lost_claim':
                self.assertEqual(result['state'],'not_acquired');factory.assert_not_called()
            else:
                self.assertEqual(events[-1],'gateway_closed');self.assertEqual(len(set(deadlines)),1)
                self.assertEqual(result['state'],'execution_finished' if mode=='success' else 'reconciliation_required')

    async def test_provider_profile_refused_before_socket_transition_or_container(self):
        for profile in ({'id':'claude-subscription-v1'},None,{}):
            create=Mock();run=Mock();serve=AsyncMock()
            with patch('permission_worker.lifecycle_reader',return_value=lambda:dict(
                    claim={},config={'providerProfile':profile})),patch(
                    'permission_worker.lifecycle_transition') as transition,patch(
                    'permission_worker.serve_control',new_callable=AsyncMock) as control:
                result=await run_permission_job(command=['trusted'],job={},job_root='/must-not-exist',
                    review_socket='/must-not-exist/review.sock',create=create,run=run,serve=serve)
            self.assertEqual(result,{'state':'invalid_provider_policy','started':False})
            create.assert_not_called();run.assert_not_called();serve.assert_not_called()
            transition.assert_not_called();control.assert_not_called()

    async def test_listens_after_recording_start_and_closes_after_completion(self):
        events=[];state='claimed'
        def transition(before,after,data):
            nonlocal state
            self.assertEqual(state,before);state=after;events.append(after);return True
        server=Mock(wait_closed=AsyncMock())
        async def serve(path,handler,uid):
            self.assertEqual(state,'start_requested');self.assertEqual(uid,10001)
            events.append('listening');return server
        def create(**kwargs):
            self.assertTrue(kwargs['permission_channel'])
            return {'containerId':'a'*64,'containerName':'fixture'}
        def run(**kwargs):
            self.assertEqual(events[-1],'listening');events.append('process')
            return {'exitCode':0,'containerStopped':True,'deadlineExceeded':False}
        job=dict(launchId='fixture',missionId='fixture',workspaceId='fixture',runnerId='fixture',
                 imageDigest='fixture',timeoutSeconds=10)
        def reader(command,include_config=False):
            return (lambda:dict(claim={**job,'state':state},config=job)) if include_config else lambda:dict(state=state,containerId='a'*64,
                startRequestedAt=datetime.now(timezone.utc).isoformat(),authorizationExpiresAt=(datetime.now(timezone.utc)+timedelta(seconds=60)).isoformat())
        with patch('permission_worker.lifecycle_transition',return_value=transition),patch(
                'permission_worker.lifecycle_reader',side_effect=reader):
            result=await run_permission_job(command=['trusted'],job=job,job_root='/fixture',create=create,run=run,serve=serve)
        self.assertEqual(result['state'],'execution_finished')
        self.assertFalse(result['independentValidationPassed'])
        server.close.assert_called_once();server.wait_closed.assert_awaited_once()

    async def test_channel_failure_never_starts_container(self):
        run=Mock()
        job=dict(launchId='fixture',missionId='fixture',workspaceId='fixture',runnerId='fixture',imageDigest='fixture',timeoutSeconds=10)
        def reader(command,include_config=False):
            return (lambda:dict(claim={**job,'state':'claimed'},config=job)) if include_config else lambda:dict(state='start_requested',containerId='a'*64,
                startRequestedAt=datetime.now(timezone.utc).isoformat(),authorizationExpiresAt=(datetime.now(timezone.utc)+timedelta(seconds=60)).isoformat())
        serve=AsyncMock(side_effect=OSError('unavailable'))
        with patch('permission_worker.lifecycle_transition',return_value=lambda *args:True),patch(
                'permission_worker.lifecycle_reader',side_effect=reader):
            result=await run_permission_job(command=['trusted'],job=job,job_root='/fixture',
                create=Mock(return_value={'containerId':'a'*64,'containerName':'fixture'}),run=run,
                serve=serve)
        self.assertEqual(result['state'],'reconciliation_required');run.assert_not_called()
        serve.assert_awaited_once()

    async def test_revoked_or_expired_after_channel_setup_never_starts(self):
        for change in ('cancel','expire'):
            state='claimed';expired=False;run=Mock()
            job=dict(launchId='fixture',missionId='fixture',workspaceId='fixture',runnerId='fixture',imageDigest='fixture',timeoutSeconds=10)
            def transition(before,after,data):
                nonlocal state
                state=after;return True
            def reader(command,include_config=False):
                if include_config:return lambda:dict(claim={**job,'state':state},config=job)
                return lambda:dict(state=state,containerId='a'*64,startRequestedAt=datetime.now(timezone.utc).isoformat(),
                    authorizationExpiresAt=(datetime.now(timezone.utc)+timedelta(seconds=-1 if expired else 60)).isoformat())
            server=Mock(wait_closed=AsyncMock())
            async def serve(*args,**kwargs):
                nonlocal state,expired
                if change=='cancel':state='cancelled'
                else:expired=True
                return server
            with patch('permission_worker.lifecycle_transition',return_value=transition),patch('permission_worker.lifecycle_reader',side_effect=reader):
                result=await run_permission_job(command=['trusted'],job=job,job_root='/fixture',
                    create=Mock(return_value={'containerId':'a'*64,'containerName':'fixture'}),run=run,serve=serve)
            self.assertEqual(result['state'],'reconciliation_required');run.assert_not_called();server.close.assert_called_once()

    async def test_changed_image_or_deadline_cannot_create_container(self):
        canonical=dict(launchId='fixture',missionId='fixture',workspaceId='fixture',runnerId='fixture',imageDigest='approved',timeoutSeconds=10)
        for changed in ({'imageDigest':'other'},{'timeoutSeconds':100}):
            create=Mock()
            with patch('permission_worker.lifecycle_reader',return_value=lambda:dict(claim={**canonical,'state':'claimed'},config=canonical)):
                result=await run_permission_job(command=['trusted'],job={**canonical,**changed},job_root='/fixture',create=create)
            self.assertEqual(result['state'],'not_acquired');create.assert_not_called()

if __name__=='__main__':unittest.main()
