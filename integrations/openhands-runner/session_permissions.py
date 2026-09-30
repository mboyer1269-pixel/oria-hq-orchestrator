"""Instance-local ACP callback sequencing; host callbacks own durable authority."""
import asyncio


class SessionPermissions:
    def __init__(self, *, register, decide):
        # These trusted async functions must never be supplied by the dossier.
        self.register=register
        self.decide=decide
        self.session_id=None
        self.failed=False
        self.lock=asyncio.Lock()

    async def request(self, *, session_id, tool_call, options):
        denied={'outcome':{'outcome':'cancelled'}}
        if not isinstance(session_id,str) or not 1<=len(session_id)<=160:
            return denied
        try:
            async with self.lock:
                if self.failed:return denied
                if self.session_id is None:
                    # Mark uncertainty BEFORE awaiting the durable registration.
                    # Cancellation/lost response must not cause implicit retry.
                    self.failed=True
                    if await self.register(session_id) is not True:return denied
                    self.session_id=session_id
                    self.failed=False
                if self.session_id!=session_id:return denied
            return await self.decide(session_id=session_id,tool_call=tool_call,options=options)
        except asyncio.CancelledError:
            raise
        except Exception:
            return denied
