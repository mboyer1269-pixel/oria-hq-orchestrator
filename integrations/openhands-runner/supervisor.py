"""Operator-owned Docker deadline. Does not authorize or create a mission."""
import json
import re
import subprocess
import time
import math


def docker(*args, timeout=10):
    return subprocess.run(["docker", *args], check=True, capture_output=True,
                          text=True, timeout=timeout)


def state(container_id, *, timeout=10):
    # Inspect only fields needed here: never return container environment/secrets.
    result = docker("inspect", "--format",
                    '{{json .State}}', container_id, timeout=timeout)
    return json.loads(result.stdout)


def supervise(*, container_id, timeout_seconds, grace_seconds=5, deadline_monotonic=None):
    """Start one previously authorized, newly created container; retain on exit.

    Caller must hold the durable launch reservation and select the full ID from
    docker create, not from an untrusted request. Labels are an ownership guard,
    not proof of user authorization. Daemon failure leaves reconciliation needed.
    """
    if not isinstance(container_id, str) or not re.fullmatch(r"[a-f0-9]{64}", container_id):
        raise ValueError("Full server-selected container ID required")
    if type(timeout_seconds) is not int or not 1 <= timeout_seconds <= 1800:
        raise ValueError("Invalid deadline")
    if type(grace_seconds) is not int or not 0 <= grace_seconds <= 10:
        raise ValueError("Invalid grace period")
    started=time.monotonic()
    if deadline_monotonic is not None and (type(deadline_monotonic) not in (int,float) or not math.isfinite(deadline_monotonic)):
        raise ValueError('Invalid absolute deadline')
    deadline=min(started+timeout_seconds,deadline_monotonic) if deadline_monotonic is not None else started+timeout_seconds
    if deadline<=started:raise TimeoutError('Job deadline elapsed before inspection')
    def inspection_budget():
        remaining=deadline-time.monotonic()
        if remaining<=0:raise TimeoutError('Job deadline elapsed before inspection')
        return min(10,remaining)
    purpose = docker("inspect", "--format",
                     '{{index .Config.Labels "oria.purpose"}}', container_id, timeout=inspection_budget()).stdout.strip()
    if purpose != "openhands-supervised-job" or state(container_id,timeout=inspection_budget()).get("Status") != "created":
        raise ValueError("Only a newly created owned job may start")
    remaining=deadline-time.monotonic()
    if remaining<=0:raise TimeoutError('Job deadline elapsed before start')
    expired = False
    interrupted = False
    try:
        # Output stays in Docker logs, avoiding unbounded host capture buffers.
        subprocess.run(["docker", "start", "--attach", container_id],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       check=False, timeout=remaining)
    except subprocess.TimeoutExpired:
        expired = True
    except BaseException:
        interrupted = True
        raise
    finally:
        # A detached CLI is not evidence the workload stopped. Inspect the daemon.
        current = state(container_id)
        if current.get("Running"):
            docker("stop", "--time", str(grace_seconds), container_id,
                   timeout=grace_seconds + 10)
            current = state(container_id)
        if current.get("Running") or current.get("Status") not in ("exited", "dead"):
            raise RuntimeError("Container outcome requires reconciliation")
    return {"status": "deadline_exceeded" if expired else "exited",
            "exitCode": current.get("ExitCode"),
            "elapsedSeconds": round(time.monotonic() - started, 3),
            "containerStopped": True, "containerRetained": True,
            "deadlineExceeded": expired, "interrupted": interrupted,
            "providerCancellationVerified": False, "hardTokenLimitEnforced": False}
