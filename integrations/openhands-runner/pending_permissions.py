"""Ephemeral exact requests; notifications are hints, never approval grants.

Access only through the trusted HQ control channel, never the agent socket.
One registry belongs to one host job and one asyncio loop. No disk persistence.
"""
import asyncio
from contextlib import asynccontextmanager
import copy
from datetime import datetime,timezone
import uuid


class PendingPermissions:
    def __init__(self, *, actor_id, workspace_id, config, now=lambda:datetime.now(timezone.utc)):
        self.actor_id=actor_id
        self.workspace_id=workspace_id
        self.config=copy.deepcopy(config)
        self.now=now
        self.entry=None

    def _live(self):
        return self.entry is not None and self.now()<self.entry['expires']

    def _matches(self,actor_id,workspace_id,request_id):
        return (self._live() and actor_id==self.actor_id and workspace_id==self.workspace_id
                and request_id==self.entry['id'])

    @asynccontextmanager
    async def publish(self,request):
        if self.entry is not None:raise ValueError('Pending request already exists')
        expires=datetime.fromisoformat(request['expiresAt'].replace('Z','+00:00'))
        if request['workspaceId']!=self.workspace_id or not 0<(expires-self.now()).total_seconds()<=180:
            raise ValueError('Invalid pending scope or expiry')
        request_id=str(uuid.uuid4())
        self.entry={'id':request_id,'request':copy.deepcopy(request),'expires':expires,'event':asyncio.Event()}
        try:yield request_id
        finally:self.entry=None

    def list_ids(self, *, actor_id, workspace_id):
        if actor_id!=self.actor_id or workspace_id!=self.workspace_id or not self._live():return []
        return [self.entry['id']]

    def load(self, *, actor_id, workspace_id, request_id):
        if not self._matches(actor_id,workspace_id,request_id):return None
        return {'request':copy.deepcopy(self.entry['request']),'config':copy.deepcopy(self.config),
                'actorId':self.actor_id,'runnerId':self.entry['request']['runnerId']}

    def notify(self, *, actor_id, workspace_id, request_id):
        if not self._matches(actor_id,workspace_id,request_id):return False
        self.entry['event'].set()
        return True

    async def wait(self,request_id):
        if not self._live() or self.entry['id']!=request_id:return False
        # Leave time before request expiry for HQ's durable
        # decision consumption. UI must show expiry; late clicks cannot extend it.
        seconds=max(0,min(170,(self.entry['expires']-self.now()).total_seconds()-10))
        try:
            await asyncio.wait_for(self.entry['event'].wait(),seconds)
            return self._live()
        except TimeoutError:return False
