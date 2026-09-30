"""Run one deterministic check in a disposable candidate image, without secrets.

Operator-side only. Never mount provider homes, host sockets or application data.
The immutable image must already contain a reviewed development snapshot and deps.
"""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import time
import uuid

parser = argparse.ArgumentParser()
parser.add_argument("--image", required=True)
parser.add_argument("--phase", choices=["test", "typecheck", "lint", "build", "smoke:joris"], required=True)
parser.add_argument("--timeout", type=int, default=600)
args = parser.parse_args()
if not re.fullmatch(r"sha256:[a-f0-9]{64}", args.image) or not 1 <= args.timeout <= 900:
    parser.error("An immutable image ID and timeout from 1 to 900 seconds are required")
name = "oria-hq-validation-" + uuid.uuid4().hex
directory = Path("/opt/oria-hq-pilot/validation")
directory.mkdir(mode=0o700, exist_ok=True)
if directory.is_symlink() or directory.resolve() != directory:
    raise SystemExit("Refuse linked log directory")
log_path = directory / (name + ".log")
started = time.monotonic()
status = "failed"
return_code = None
heap_mb = 512 if args.phase == "test" else 1536
command = ["docker", "run", "--rm", "--name", name, "--network", "none", "--cpus", "2",
           "--memory", "2g", "--memory-swap", "2g", "--pids-limit", "256", "--user", "1000:1000",
           "--cap-drop", "ALL", "--security-opt", "no-new-privileges:true",
           "-e", f"NODE_OPTIONS=--max-old-space-size={heap_mb}", args.image, "npm", "run", args.phase]
try:
    fd = os.open(log_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as log:
        try:
            result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=args.timeout)
            return_code = result.returncode
            status = "passed" if return_code == 0 else "failed"
        except subprocess.TimeoutExpired:
            status = "timed_out"
finally:
    # The random name belongs exclusively to this invocation. No broad prune.
    subprocess.run(["docker", "rm", "-f", name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
    still_exists = subprocess.run(["docker", "inspect", name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10).returncode == 0
print(json.dumps({"phase": args.phase, "status": status, "exitCode": return_code,
                  "durationSeconds": round(time.monotonic() - started, 2), "log": str(log_path),
                  "containerRemoved": not still_exists, "network": "none", "operationalVolumes": False}))
raise SystemExit(0 if status == "passed" and not still_exists else 1)
