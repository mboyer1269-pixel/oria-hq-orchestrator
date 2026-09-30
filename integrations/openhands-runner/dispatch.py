"""Execution ordering for a trusted, already authorized host job.

The supplied transition is a durable compare-and-swap bound to the exact HQ
launch ID, workspace, runner, config and expected version. It must return True
only after confirmed persistence. There is no in-memory production fallback.

When session registration is enabled, read_claim must be a trusted canonical
reader bound to that same launch and workspace. Omitting it is supported only
for runners that never register a session. It does not replace the transition's
version/CAS validation; a concurrent cancellation must still reject completion.
"""
from container_job import create_job
from supervisor import supervise
import time


def dispatch(*, transition, launch_id, image_digest, workspace_id, job_root,
             timeout_seconds, create=create_job, run=supervise, read_claim=None, clock=time.monotonic):
    if type(timeout_seconds) is not int or not 1 <= timeout_seconds <= 1800:
        raise ValueError('Invalid deadline')
    # Two workers may read the same claim; only one may cross this boundary.
    # The adapter must also enforce unexpired canonical launch authorization.
    if transition('claimed','creation_requested',{}) is not True:
        return {'state':'not_acquired','started':False}
    deadline=clock()+timeout_seconds
    container_id=None
    try:
        created=create(launch_id=launch_id,image_digest=image_digest,
                       workspace_id=workspace_id,job_root=job_root,deadline_monotonic=deadline)
        container_id=created['containerId']
        identity={'containerId':container_id,'containerName':created['containerName']}
        if transition('creation_requested','container_created',identity) is not True:
            return {'state':'reconciliation_required','started':False,**identity}
        if clock()>=deadline:
            return {'state':'reconciliation_required','started':False,'deadlineExceeded':True,**identity}
        if transition('container_created','start_requested',identity) is not True:
            return {'state':'reconciliation_required','started':False,**identity}
        outcome=run(container_id=container_id,timeout_seconds=timeout_seconds,deadline_monotonic=deadline)
        # A process exit is never proof that its coding mission passed review.
        result={'state':'execution_finished',**identity,'process':outcome,
                'independentValidationPassed':False}
        expected='start_requested'
        if read_claim is not None:
            # Host-owned canonical read, after the process has stopped. Never
            # infer the lifecycle state from an agent's output or local flag.
            claim=read_claim()
            if (not isinstance(claim,dict)
                    or claim.get('containerId')!=container_id
                    or claim.get('state') not in ('start_requested','running')):
                return {**result,'state':'reconciliation_required'}
            expected=claim['state']
        if transition(expected,'execution_finished',result) is not True:
            return {**result,'state':'reconciliation_required'}
        return result
    except Exception:
        # Do not make a second write or execution attempt after unknown effects.
        # Persisted *_requested state plus deterministic name enables recovery.
        return {'state':'reconciliation_required','containerId':container_id}
