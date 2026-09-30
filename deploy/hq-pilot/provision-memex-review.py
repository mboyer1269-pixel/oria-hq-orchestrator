"""Provision the initial scoped HQ operator secret, outside repositories/images.

Run on Linux as root. Refuses existing targets; does not enable either service.
The same random token has two differently owned files. Neither file is logged.
Rotation is a separate coordinated operation: this script never overwrites keys.
"""
import json
import os
from pathlib import Path
import re
import secrets
import sys


def provision(memex_dir, hq_dir, namespace, *, owners=((1000, 1000), (100, 101))):
    if not re.fullmatch(r"org:workspace:[a-zA-Z0-9][a-zA-Z0-9:_.-]{0,113}", namespace):
        raise ValueError("Expected an exact workspace namespace")
    targets = [Path(memex_dir), Path(hq_dir)]
    for target in targets:
        if not target.is_absolute() or target.exists() or target.is_symlink():
            raise ValueError("Target must be a new absolute directory")
        if not target.parent.is_dir() or target.parent.resolve() != target.parent:
            raise ValueError("Parent must exist and contain no symbolic links")
    if targets[0] == targets[1]:
        raise ValueError("Separate target directories required")
    token = "opr1." + secrets.token_urlsafe(32)
    payloads = [json.dumps({"token": token, "principal": "hq-owner-review", "namespace": namespace}) + "\n", token + "\n"]
    names = ["credential.json", "token"]
    for target, owner, payload, name in zip(targets, owners, payloads, names):
        target.mkdir(mode=0o700)
        # Root owns the directory; only the intended container group traverses it.
        os.chown(target, 0, owner[1])
        os.chmod(target, 0o750)
        fd = os.open(target / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o400)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
            os.fchown(handle.fileno(), *owner)
        directory_fd = os.open(target, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)


if __name__ == "__main__":
    if os.name != "posix" or os.geteuid() != 0 or len(sys.argv) != 4:
        raise SystemExit("Usage as Linux root: provision-memex-review.py MEMEX_DIRECTORY HQ_DIRECTORY NAMESPACE")
    provision(*sys.argv[1:])
    print("Dedicated review credential provisioned; services remain unchanged.")
