"""Per-launch interprocess lease held across every effect of one launch.

Why `flock` and not something new: the host already serialises its consumer with
`flock` on a root-owned file, so this reuses a primitive the deployment has. The
kernel drops an `flock` when the holding process dies, so a crash leaves no
indefinitely blocking lock; and because the next holder still has to reread
canonical authority and reobserve Docker, a released lease grants no blind
resume. Descriptors opened here are not inherited by the `docker` subprocesses we
spawn, so a child can never keep the launch held after its parent is gone.

It is advisory between our own cooperating host paths. It does not fence a
foreign process that drives Docker by hand, and it is not a distributed lock:
one launch belongs to one host, the same host that owns its job directories.
"""
from contextlib import contextmanager
import os
import stat
from pathlib import Path

NAME='launch.lock'


class LaunchBusy(Exception):
    """Another host path already holds this launch; nothing may be decided."""


def lease_path(*,control_directory=None,job_root=None):
    """Root-owned host path, never inside the agent's mounted job paths."""
    if control_directory is None and job_root is None:
        raise ValueError('A control directory or job root is required')
    base=Path(control_directory) if control_directory is not None else Path(job_root)
    return base/NAME


def open_lease(path):
    path=Path(path)
    if os.name!='posix':raise ValueError('Linux host required for the launch lease')
    if path.name!=NAME:raise ValueError('Unexpected lease filename')
    if not path.is_absolute() or path.parent.resolve(strict=True)!=path.parent:
        raise ValueError('Real absolute lease directory required')
    info=path.parent.stat()
    if info.st_uid!=0 or info.st_mode & 0o022:
        raise ValueError('Root-owned non-writable lease directory required')
    descriptor=os.open(path,os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
    held=os.fstat(descriptor)
    if not stat.S_ISREG(held.st_mode) or held.st_uid!=0 or held.st_mode & 0o022 or held.st_nlink!=1:
        os.close(descriptor)
        raise ValueError('Protected regular lease file required')
    return descriptor


def acquire_exclusive(descriptor):
    import fcntl
    try:fcntl.flock(descriptor,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except (BlockingIOError,OSError) as error:
        raise LaunchBusy('Launch already held by another host path') from error


@contextmanager
def hold_launch(path,*,acquire=acquire_exclusive):
    """Exclusive for the whole block; closing the descriptor releases it."""
    descriptor=open_lease(path)
    try:
        acquire(descriptor)
        yield Path(path)
    finally:
        os.close(descriptor)
