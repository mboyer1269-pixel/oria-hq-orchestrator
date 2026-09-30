"""Disposable host pending registry for the real HQ inbox qualification.

The input file is synthetic harness data, not an agent or production API.
"""
import asyncio
import json
import sys
from pathlib import Path
from pending_permissions import PendingPermissions
from permission_control import serve_control
from permission_host import host_handler
from permission_transport import serve_permissions,encode,read_frame
from hq_transition import lifecycle_transition,consume_tool_decision
from functools import partial
from datetime import datetime,timedelta


async def main(root,node_name):
    async with asyncio.timeout(90):
        source = root / 'fixture.json'
        while not source.exists():
            await asyncio.sleep(.05)
        fixture = json.loads(source.read_text())
        request = fixture['request']
        pending = PendingPermissions(actor_id=fixture['actorId'],
                                     workspace_id=request['workspaceId'], config=fixture['config'])
        directory = root / request['launchId']
        directory.mkdir(mode=0o755)
        server = await serve_control(str(directory / 'review.sock'), pending, uid=1000)
        agent_server=None
        try:
            if fixture.get('hostFlow'):
                command=['docker','exec','-i','-e','NEXT_PUBLIC_SUPABASE_URL='+fixture['url'],
                         '-e','SUPABASE_SERVICE_ROLE_KEY=synthetic-local-qualification','-e','NODE_ENV=test',
                         node_name,'node','/workspace/hq/src/scripts/openhands-lifecycle.mjs','/tmp/lifecycle-job.json']
                handler=host_handler(job=request,transition=lifecycle_transition(command),
                                     consume=partial(consume_tool_decision,command),pending=pending,
                                     deadline=datetime.fromisoformat(fixture['startRequestedAt'].replace('Z','+00:00'))+timedelta(seconds=fixture['config']['timeoutSeconds']))
                agent_server=await serve_permissions(str(root/'agent.sock'),handler,uid=0)
                reader,writer=await asyncio.open_unix_connection(str(root/'agent.sock'))
                try:
                    writer.write(encode({'session_id':request['sessionId'],
                        'tool_call':{'toolCallId':request['toolCallId'],'rawInput':json.loads(request['inputJson'])},
                        'options':request['options']}));await writer.drain()
                    while not pending.list_ids(actor_id=fixture['actorId'],workspace_id=request['workspaceId']):
                        await asyncio.sleep(.05)
                    (root/'ready').touch()
                    response=await read_frame(reader)
                    assert response=={'outcome':{'outcome':'selected','optionId':'allow'}},response
                    (root/'notified').touch()
                    (root/'consumed').write_text(json.dumps(response))
                    while not (root/'done').exists():await asyncio.sleep(.05)
                finally:
                    writer.close();await writer.wait_closed()
                return
            async with pending.publish(request):
                (root / 'ready').touch()
                # The registry's event is only a wake-up signal. HQ's database
                # separately decides whether consumption is authorized.
                request_id = pending.list_ids(actor_id=fixture['actorId'], workspace_id=request['workspaceId'])[0]
                assert await pending.wait(request_id), 'Notification missing or expired'
                (root / 'notified').touch()
                while not (root / 'done').exists():
                    await asyncio.sleep(.05)
        finally:
            if agent_server:
                agent_server.close();await agent_server.wait_closed()
            server.close()
            await server.wait_closed()


if __name__ == '__main__':
    asyncio.run(main(Path(sys.argv[1]),sys.argv[2]))
