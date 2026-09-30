import asyncio
import os
from pathlib import Path
import tempfile
import unittest
from permission_transport import serve_permissions, request_permission, encode, request_shape, LIMIT


class Model:
    def __init__(self,**fields):self.__dict__.update(fields)
    def model_dump(self,**kwargs):return dict(self.__dict__)


class FrameTests(unittest.TestCase):
    def test_agent_cannot_supply_host_identity(self):
        with self.assertRaises(ValueError):
            request_shape(dict(session_id='s',tool_call={},options=[{}],workspaceId='other'))
    def test_bounded_finite_frames(self):
        for value in ({'x':'x'*LIMIT},{'x':float('nan')}):
            with self.assertRaises(ValueError):encode(value)


@unittest.skipUnless(hasattr(os,'chown'),'Linux host transport')
class SocketTests(unittest.IsolatedAsyncioTestCase):
    async def test_real_socket_success_rejects_broad_option_and_missing_endpoint(self):
        with tempfile.TemporaryDirectory() as directory:
            socket=str(Path(directory)/'p.sock')
            choice='once';seen=[]
            async def handler(**request):
                seen.append(request)
                return {'outcome':{'outcome':'selected','optionId':choice}}
            server=await serve_permissions(socket,handler,uid=os.getuid())
            args=dict(session_id='session',tool_call=Model(toolCallId='call',rawInput={'command':'npm test'}),
                      options=[Model(option_id='once',kind='allow_once'),Model(option_id='broad',kind='allow_always')])
            try:
                self.assertEqual((await request_permission(socket,**args))['outcome']['optionId'],'once')
                self.assertEqual(seen[0]['session_id'],'session')
                self.assertEqual(os.stat(socket).st_mode & 0o777,0o600)
                choice='broad'
                self.assertEqual((await request_permission(socket,**args))['outcome']['outcome'],'cancelled')
                with self.assertRaises(ValueError):await serve_permissions(socket,handler,uid=os.getuid())
            finally:
                server.close();await server.wait_closed()
            self.assertEqual((await request_permission(socket,**args))['outcome']['outcome'],'cancelled')

    async def test_handler_error_denies(self):
        with tempfile.TemporaryDirectory() as directory:
            socket=str(Path(directory)/'p.sock')
            async def handler(**request):raise RuntimeError('synthetic')
            server=await serve_permissions(socket,handler,uid=os.getuid())
            try:
                result=await request_permission(socket,session_id='s',tool_call=Model(),options=[Model(option_id='once',kind='allow_once')])
                self.assertEqual(result['outcome']['outcome'],'cancelled')
            finally:server.close();await server.wait_closed()

if __name__=='__main__':unittest.main()
