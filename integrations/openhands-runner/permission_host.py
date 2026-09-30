"""Bind ACP wire requests to a host-owned job before consulting HQ."""
import asyncio
from datetime import datetime, timezone, timedelta
import json
from session_permissions import SessionPermissions
from permission_transport import denied


def identifier(value):
    if not isinstance(value,str) or not 1<=len(value)<=160:raise ValueError('Invalid identifier')
    return value


def host_handler(*, job, transition, consume, now=lambda:datetime.now(timezone.utc), pending=None, deadline=None):
    # Snapshot host configuration. The wire cannot override these identities.
    identity={key:job[key] for key in ('workspaceId','missionId','launchId','runnerId','containerId')}
    async def register(session):
        return await asyncio.to_thread(transition,'start_requested','running',
                                      {'containerId':identity['containerId'],'sessionId':session})
    async def decide(*,session_id,tool_call,options):
        started=now()
        raw=tool_call.get('rawInput')
        if not isinstance(raw,dict) or not raw:return denied()
        serialized=json.dumps(raw,ensure_ascii=False,allow_nan=False,separators=(',',':'))
        if len(serialized.encode('utf-8'))>16384:return denied()
        selected=[]
        for option in options:
            if option.get('kind') in ('allow_once','reject_once'):
                selected.append({'optionId':identifier(option.get('optionId')),'kind':option['kind']})
        if not selected or len({x['optionId'] for x in selected})!=len(selected):return denied()
        expires=started+timedelta(seconds=180 if pending is not None else 20)
        if deadline is not None:expires=min(expires,deadline)
        if expires<=started:return denied()
        request={'version':1,**identity,'sessionId':session_id,
                 'toolCallId':identifier(tool_call.get('toolCallId')),'inputJson':serialized,
                 'options':selected,'requestedAt':started.isoformat(),
                 'expiresAt':expires.isoformat()}
        # Consumption cannot manufacture approval. Until an authenticated review
        # exists for this exact request, HQ returns cancelled.
        if pending is None:return await asyncio.to_thread(consume,request)
        async with pending.publish(request) as request_id:
            if not await pending.wait(request_id):return denied()
            return await asyncio.to_thread(consume,request)
    sessions=SessionPermissions(register=register,decide=decide)
    return sessions.request
