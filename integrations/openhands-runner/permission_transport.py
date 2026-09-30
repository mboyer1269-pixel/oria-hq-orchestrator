"""Per-job Unix IPC. Host supplies the socket and handler, never the dossier.

Deploy only in a private host-owned directory mounted into one job. This
transport conveys requests, not authority; the handler must bind the job,
register its session, and consume an authenticated HQ decision.
"""
import asyncio
import json
import os

LIMIT=32768


def denied():
    return {'outcome':{'outcome':'cancelled'}}


def request_shape(raw):
    if not isinstance(raw,dict) or set(raw)!={'session_id','tool_call','options'}:
        raise ValueError('Invalid request')
    if not isinstance(raw['session_id'],str) or not 1<=len(raw['session_id'])<=160:
        raise ValueError('Invalid session')
    if not isinstance(raw['tool_call'],dict) or not isinstance(raw['options'],list) or not 1<=len(raw['options'])<=8:
        raise ValueError('Invalid tool request')
    return raw


def encode(value):
    frame=json.dumps(value,ensure_ascii=False,allow_nan=False).encode('utf-8')+b'\n'
    if len(frame)>LIMIT:raise ValueError('Oversized frame')
    return frame


async def read_frame(reader):
    frame=await reader.readline()
    if not frame.endswith(b'\n') or len(frame)>LIMIT:raise ValueError('Invalid frame')
    return json.loads(frame,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('Nonfinite JSON')))


async def request_permission(socket_path, *, session_id, tool_call, options):
    writer=None
    try:
        raw=request_shape({'session_id':session_id,'tool_call':tool_call.model_dump(mode='json',by_alias=True),
                           'options':[item.model_dump(mode='json',by_alias=True) for item in options]})
        frame=encode(raw)
        async with asyncio.timeout(205):
            reader,writer=await asyncio.open_unix_connection(socket_path,limit=LIMIT)
            writer.write(frame);await writer.drain()
            response=await read_frame(reader)
            outcome=response.get('outcome',{})
            offered={item.option_id for item in options if item.kind in ('allow_once','reject_once')}
            if outcome.get('outcome')=='selected' and outcome.get('optionId') in offered:
                return {'outcome':{'outcome':'selected','optionId':outcome['optionId']}}
    except (Exception,):
        pass
    finally:
        if writer is not None:writer.close()
    return denied()


async def serve_permissions(socket_path, handler, *, uid):
    """No overwrite/unlink of an existing socket; one in-flight request per job.

    Caller owns server lifetime and private-directory cleanup. UID is the
    configured job UID; no keys, launch IDs or workspace IDs come from the wire.
    """
    if os.path.lexists(socket_path):raise ValueError('Socket already exists')
    busy=False
    async def accept(reader,writer):
        nonlocal busy
        if busy:
            writer.close();return
        busy=True
        response=denied()
        try:
            async with asyncio.timeout(200):
                request=request_shape(await read_frame(reader))
                response=await handler(**request)
            writer.write(encode(response));await writer.drain()
        except Exception:
            try:writer.write(encode(denied()));await writer.drain()
            except Exception:pass
        finally:
            busy=False
            writer.close()
    server=await asyncio.start_unix_server(accept,path=socket_path,limit=LIMIT,start_serving=False)
    try:
        os.chown(socket_path,uid,-1)
        os.chmod(socket_path,0o600)
        await server.start_serving()
        return server
    except BaseException:
        server.close();await server.wait_closed()
        raise
