"""Trusted host assembly. No browser endpoint and no automatic tool approvals.

The caller supplies job values from the same protected canonical configuration
used by command. Directory preparation and launch authorization precede this
function. The external supervisor owns process deadlines, including cancellation.
"""
import asyncio
from datetime import datetime,timedelta,timezone
import time
from functools import partial
from pathlib import Path
from contextlib import ExitStack
from container_job import create_job
from dispatch import dispatch
from hq_transition import lifecycle_transition,lifecycle_reader,consume_tool_decision
from permission_host import host_handler
from permission_transport import serve_permissions
from supervisor import supervise
from pending_permissions import PendingPermissions
from permission_control import serve_control
from provider_policy import ROOT,provider_preflight,load_provider_policy
from provider_gateway import provider_gateway


async def run_permission_job(*, command, job, job_root, create=create_job,
                             run=supervise, serve=serve_permissions, review_socket=None,
                             gateway_root=None,policy_root=ROOT):
    loop=asyncio.get_running_loop()
    job=dict(job)
    command=tuple(command)
    observed=await asyncio.to_thread(lifecycle_reader(command,include_config=True))
    claim=observed['claim'];config=observed['config']
    # A declared policy is not an implemented network/authentication boundary.
    # Never silently execute it using the legacy offline container settings.
    use_provider='providerProfile' in config
    if use_provider:
        if gateway_root is None:return provider_preflight(config)
        try:load_provider_policy(config,policy_root)
        except (ValueError,TypeError,KeyError,OSError):return {'state':'invalid_provider_policy','started':False}
    canonical={key:claim[key] for key in ('launchId','missionId','workspaceId','runnerId')}
    canonical.update(imageDigest=config['imageDigest'],timeoutSeconds=config['timeoutSeconds'])
    if job!=canonical or claim['state']!='claimed':
        return {'state':'not_acquired','started':False}
    job=canonical
    transition=lifecycle_transition(command)
    read=lifecycle_reader(command)
    servers=[]
    pending=None
    if review_socket is not None:
        path=Path(review_socket)
        if not path.is_absolute() or path.parent.resolve(strict=True)!=path.parent:
            raise ValueError('Real absolute control directory required')
        if path.parent==Path(job_root)/'ipc' or Path(job_root) in path.parents:
            raise ValueError('Control socket must be outside the agent job')
        info=path.parent.stat()
        if info.st_uid!=0 or info.st_mode & 0o022:raise ValueError('Protected control directory required')
        pending=PendingPermissions(actor_id=claim['actorId'],workspace_id=job['workspaceId'],config=config)
        servers.append(await serve_control(str(path),pending,uid=1000))
    def current_start(container_id):
        current=read()
        expires=datetime.fromisoformat(current['authorizationExpiresAt'].replace('Z','+00:00'))
        if current['state']!='start_requested' or current['containerId']!=container_id or expires<=datetime.now(timezone.utc):
            raise ValueError('Canonical launch no longer startable')
        return current
    async def open_channel(container_id,deadline_monotonic):
        current=await asyncio.to_thread(current_start,container_id)
        remaining=deadline_monotonic-time.monotonic()
        if remaining<=0:raise TimeoutError('Job deadline elapsed before permission channel')
        deadline=min(datetime.now(timezone.utc)+timedelta(seconds=remaining),
                     datetime.fromisoformat(current['startRequestedAt'].replace('Z','+00:00'))+timedelta(seconds=job['timeoutSeconds']))
        handler=host_handler(job={**job,'containerId':container_id},transition=transition,
                             consume=partial(consume_tool_decision,command),pending=pending,deadline=deadline)
        server=await serve(str(Path(job_root)/'ipc'/'permission.sock'),handler,uid=10001)
        servers.append(server)
    def run_with_channel(*,container_id,timeout_seconds,deadline_monotonic):
        # dispatch already recorded start_requested. No container process starts
        # before its bound handler is listening. No retry on setup uncertainty.
        remaining=deadline_monotonic-time.monotonic()
        if remaining<=0:raise TimeoutError('Job deadline elapsed before channel setup')
        future=asyncio.run_coroutine_threadsafe(open_channel(container_id,deadline_monotonic),loop)
        try:future.result(timeout=min(10,remaining))
        except BaseException:
            future.cancel();raise
        current_start(container_id)
        return run(container_id=container_id,timeout_seconds=timeout_seconds,deadline_monotonic=deadline_monotonic)
    def dispatch_job():
        try:
            with ExitStack() as resources:
                def create_bound(**parameters):
                    provider=None
                    if use_provider:
                        # Called only after the durable launch CAS succeeds.
                        provider=resources.enter_context(provider_gateway(config=config,launch_id=job['launchId'],
                            root=gateway_root,policy_root=policy_root,deadline_monotonic=parameters['deadline_monotonic']))
                    return create(**parameters,permission_channel=True,**({'provider':provider} if provider is not None else {}))
                result=dispatch(transition=transition,read_claim=read,launch_id=job['launchId'],
                    workspace_id=job['workspaceId'],image_digest=job['imageDigest'],
                    job_root=job_root,timeout_seconds=job['timeoutSeconds'],create=create_bound,run=run_with_channel)
            return result
        except Exception:return {'state':'reconciliation_required','automaticRetry':False}
    task=asyncio.create_task(asyncio.to_thread(dispatch_job))
    try:
        # Losing this coroutine must not abandon a running container's supervisor.
        return await asyncio.shield(task)
    except asyncio.CancelledError:
        await task
        raise
    finally:
        for server in servers:
            server.close()
            await server.wait_closed()
