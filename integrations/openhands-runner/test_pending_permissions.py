import unittest
from datetime import datetime,timezone,timedelta
from pending_permissions import PendingPermissions
from permission_host import host_handler


class PendingTests(unittest.IsolatedAsyncioTestCase):
    async def test_review_never_extends_host_deadline(self):
        now=datetime.now(timezone.utc);captured=[]
        class Ready(PendingPermissions):
            async def wait(self,request_id):return True
        pending=Ready(actor_id='o',workspace_id='w',config={},now=lambda:now)
        def consume(request):captured.append(request);return {'outcome':{'outcome':'cancelled'}}
        handler=host_handler(job=dict(workspaceId='w',missionId='m',launchId='l',runnerId='r',containerId='c'),
            transition=lambda *args:True,consume=consume,pending=pending,now=lambda:now,deadline=now+timedelta(seconds=45))
        await handler(session_id='s',tool_call={'toolCallId':'c','rawInput':{'command':'npm test'}},options=[{'optionId':'once','kind':'allow_once'}])
        self.assertEqual(datetime.fromisoformat(captured[0]['expiresAt']),now+timedelta(seconds=45))

    async def test_notification_does_not_grant_permission(self):
        class Notified(PendingPermissions):
            async def wait(self,request_id):
                self.notify(actor_id='o',workspace_id='w',request_id=request_id)
                return await super().wait(request_id)
        pending=Notified(actor_id='o',workspace_id='w',config={})
        calls=[]
        def consume(request):
            calls.append(request);return {'outcome':{'outcome':'cancelled'}}
        handler=host_handler(job=dict(workspaceId='w',missionId='m',launchId='l',runnerId='r',containerId='c'),
            transition=lambda *args:True,consume=consume,pending=pending)
        response=await handler(session_id='s',tool_call={'toolCallId':'c','rawInput':{'command':'npm test'}},
            options=[{'optionId':'once','kind':'allow_once'}])
        self.assertEqual(response['outcome']['outcome'],'cancelled')
        self.assertEqual(len(calls),1);self.assertIsNone(pending.entry)

    async def test_scoped_snapshot_notification_and_cleanup(self):
        now=datetime.now(timezone.utc)
        pending=PendingPermissions(actor_id='owner',workspace_id='w',config={'image':'fixed'},now=lambda:now)
        request={'workspaceId':'w','runnerId':'r','expiresAt':(now+timedelta(seconds=20)).isoformat(),'inputJson':'original'}
        async with pending.publish(request) as request_id:
            scope=dict(actor_id='owner',workspace_id='w',request_id=request_id)
            request['inputJson']='mutated'
            self.assertEqual(pending.load(**scope)['request']['inputJson'],'original')
            snapshot=pending.load(**scope);snapshot['config']['image']='mutated'
            self.assertEqual(pending.load(**scope)['config']['image'],'fixed')
            self.assertIsNone(pending.load(**{**scope,'actor_id':'other'}))
            self.assertFalse(pending.notify(**{**scope,'workspace_id':'other'}))
            self.assertTrue(pending.notify(**scope))
            self.assertTrue(await pending.wait(request_id))
        self.assertIsNone(pending.load(**scope))

    async def test_expiration_and_exception_clear_request(self):
        now=datetime.now(timezone.utc)
        pending=PendingPermissions(actor_id='o',workspace_id='w',config={},now=lambda:now)
        request={'workspaceId':'w','runnerId':'r','expiresAt':(now+timedelta(seconds=20)).isoformat()}
        with self.assertRaises(RuntimeError):
            async with pending.publish(request) as request_id:
                now+=timedelta(seconds=21)
                self.assertEqual(pending.list_ids(actor_id='o',workspace_id='w'),[])
                self.assertFalse(await pending.wait(request_id))
                raise RuntimeError('cancelled workflow')
        self.assertIsNone(pending.entry)

if __name__=='__main__':unittest.main()
