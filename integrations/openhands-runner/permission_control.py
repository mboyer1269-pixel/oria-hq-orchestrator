"""Private HQ-backend channel. Never mount this socket into an agent job.

The backend must authenticate the owner before calling. Socket filesystem
permissions authenticate the local backend process, not an end user's session.
"""
import asyncio
import os
from permission_transport import LIMIT,encode,read_frame


def query_pending(pending,raw):
    if not isinstance(raw,dict):raise ValueError('Invalid control request')
    operation=raw.get('operation')
    fields={'operation','actorId','workspaceId'}
    if operation in ('read','notify'):fields.add('requestId')
    if operation not in ('list','read','notify') or set(raw)!=fields:raise ValueError('Invalid control operation')
    if any(not isinstance(raw[key],str) or not 1<=len(raw[key])<=160 for key in fields):raise ValueError('Invalid identity')
    scope=dict(actor_id=raw['actorId'],workspace_id=raw['workspaceId'])
    if operation=='list':return {'status':'ok','requestIds':pending.list_ids(**scope)}
    scope['request_id']=raw['requestId']
    if operation=='read':return {'status':'ok','pending':pending.load(**scope)}
    return {'status':'ok','notified':pending.notify(**scope)}


async def serve_control(path,pending,*,uid):
    if os.path.lexists(path):raise ValueError('Control socket already exists')
    active=0
    async def accept(reader,writer):
        nonlocal active
        if active>=4:writer.close();return
        active+=1
        try:
            async with asyncio.timeout(2):
                response=query_pending(pending,await read_frame(reader))
                writer.write(encode(response));await writer.drain()
        except Exception:
            try:writer.write(encode({'status':'unavailable'}));await writer.drain()
            except Exception:pass
        finally:active-=1;writer.close()
    server=await asyncio.start_unix_server(accept,path=path,limit=LIMIT,start_serving=False)
    try:
        os.chown(path,uid,-1);os.chmod(path,0o600)
        await server.start_serving();return server
    except BaseException:
        server.close();await server.wait_closed();raise
