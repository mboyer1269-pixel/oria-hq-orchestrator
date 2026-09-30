import asyncio
import unittest
from unittest.mock import AsyncMock
from session_permissions import SessionPermissions


class SessionPermissionTests(unittest.IsolatedAsyncioTestCase):
    async def test_first_session_registers_once_before_decisions(self):
        registered=[]
        async def register(session):registered.append(session);return True
        async def decide(**request):
            self.assertEqual(registered,['s']);return {'outcome':{'outcome':'selected','optionId':'once'}}
        callback=SessionPermissions(register=register,decide=decide)
        calls=[callback.request(session_id='s',tool_call=None,options=()) for _ in range(2)]
        self.assertTrue(all(r['outcome']['outcome']=='selected' for r in await asyncio.gather(*calls)))
        self.assertEqual((await callback.request(session_id='other',tool_call=None,options=()))['outcome']['outcome'],'cancelled')

    async def test_unknown_registration_is_never_retried(self):
        register=AsyncMock(side_effect=TimeoutError('unknown'));decide=AsyncMock()
        callback=SessionPermissions(register=register,decide=decide)
        for _ in range(2):
            self.assertEqual((await callback.request(session_id='s',tool_call=None,options=()))['outcome']['outcome'],'cancelled')
        register.assert_awaited_once();decide.assert_not_awaited()

    async def test_cancelled_registration_stays_closed(self):
        entered=asyncio.Event()
        async def register(session):entered.set();await asyncio.Future()
        decide=AsyncMock();callback=SessionPermissions(register=register,decide=decide)
        task=asyncio.create_task(callback.request(session_id='s',tool_call=None,options=()))
        await entered.wait();task.cancel()
        with self.assertRaises(asyncio.CancelledError):await task
        self.assertEqual((await callback.request(session_id='s',tool_call=None,options=()))['outcome']['outcome'],'cancelled')
        decide.assert_not_awaited()

if __name__=='__main__':unittest.main()
