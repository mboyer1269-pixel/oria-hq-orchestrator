import unittest
from datetime import datetime,timezone,timedelta
from pending_permissions import PendingPermissions
from permission_control import query_pending


class ControlTests(unittest.IsolatedAsyncioTestCase):
    async def test_scope_and_no_approval_operation(self):
        pending=PendingPermissions(actor_id='owner',workspace_id='w',config={})
        request={'workspaceId':'w','runnerId':'r','expiresAt':(datetime.now(timezone.utc)+timedelta(seconds=20)).isoformat()}
        scope={'actorId':'owner','workspaceId':'w'}
        async with pending.publish(request) as request_id:
            self.assertEqual(query_pending(pending,{'operation':'list',**scope})['requestIds'],[request_id])
            read={'operation':'read',**scope,'requestId':request_id}
            self.assertEqual(query_pending(pending,read)['pending']['request'],request)
            self.assertIsNone(query_pending(pending,{**read,'actorId':'other'})['pending'])
            self.assertFalse(query_pending(pending,{**read,'operation':'notify','workspaceId':'other'})['notified'])
            for value in ({**read,'operation':'approve'},{**read,'request':request}):
                with self.assertRaises(ValueError):query_pending(pending,value)
        self.assertIsNone(query_pending(pending,read)['pending'])

if __name__=='__main__':unittest.main()
