#!/usr/bin/env python3
"""Host-only credential renewal. Never prints credentials or provider stderr."""
import base64
import json
import os
import re
import subprocess
import tempfile
import time
from pathlib import Path

DIRECTORY = Path("/opt/oria-hq-pilot/memex-read")
NAMESPACE = "org:workspace:michael-hq"

def validate_handle(raw, now):
    token = raw.strip()
    if len(token) > 8192 or not re.fullmatch(r"amh1\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]{43}", token):
        raise ValueError("invalid handle")
    encoded = token.split(".")[1]
    payload = json.loads(base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4)))
    if (payload.get("sub") != "hq-runtime" or payload.get("access") != "read_only"
        or payload.get("namespaces") != [NAMESPACE]
        or not isinstance(payload.get("exp"), (int, float))
        or not now + 300 < payload["exp"] <= now + 3660):
        raise ValueError("invalid scope or expiry")
    return token

def rotate():
    import fcntl
    if os.geteuid() != 0 or DIRECTORY.is_symlink() or not DIRECTORY.is_dir():
        raise RuntimeError("protected directory required")
    if DIRECTORY.resolve() != DIRECTORY:
        raise RuntimeError("unexpected directory")
    with open("/run/oria-hq-memex-read/renew.lock", "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        result = subprocess.run(["docker", "exec", "oria-memex-pilot-memex-1", "node",
            "--experimental-strip-types", "/app/pilot/mint-read-handle.mjs",
            "hq-runtime", NAMESPACE, "3600"], capture_output=True, text=True, timeout=20)
        if result.returncode != 0:
            raise RuntimeError("mint unavailable")
        token = validate_handle(result.stdout, time.time())
        descriptor, temporary = tempfile.mkstemp(prefix=".handle-", dir=DIRECTORY)
        try:
            with os.fdopen(descriptor, "w") as output:
                os.fchmod(output.fileno(), 0o400)
                os.fchown(output.fileno(), 100, 101)
                output.write(token + "\n")
                output.flush()
                os.fsync(output.fileno())
            os.replace(temporary, DIRECTORY / "handle")
            directory_fd = os.open(DIRECTORY, os.O_RDONLY | os.O_DIRECTORY)
            try: os.fsync(directory_fd)
            finally: os.close(directory_fd)
        finally:
            if os.path.exists(temporary): os.unlink(temporary)

if __name__ == "__main__":
    try:
        rotate()
        print("Memex read credential renewed; scope unchanged.")
    except Exception:
        print("Memex read credential renewal failed; existing credential retained.")
        raise SystemExit(1)
