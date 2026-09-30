"""Synthetic stop/restart qualification of the idle, exclusive Claude pilot.

Does not qualify Paperclip's native SSH cancellation. No model invocation.
"""
import json
from pathlib import Path
import subprocess
import time

name = "oria-provider-runners-claude-runner-1"


def run(args):
    return subprocess.check_output(args, text=True).strip()


def top():
    return [line.split()[-1] for line in run(["docker", "top", name, "-eo", "pid,comm"]).splitlines()[1:]]


def fixture_count():
    lines = run(["docker", "top", name, "-eo", "pid,args"]).splitlines()[1:]
    return sum(line.split()[1:] in (["node", "/tmp/cancellation-probe.mjs"], ["node", "/tmp/cancellation-probe.mjs", "child"], ["/usr/local/bin/node", "/tmp/cancellation-probe.mjs", "child"]) for line in lines)


assert sorted(top()) == ["sshd", "tini"], "Runner is not idle; refusing stop test"
assert not run(["docker", "exec", "-w", "/workspace/hq-pilot", name, "git", "status", "--porcelain"])
fixture = Path(__file__).with_name("cancellation-probe.mjs").read_bytes()
subprocess.run(["docker", "exec", "-i", name, "sh", "-c", "cat > /tmp/cancellation-probe.mjs"], input=fixture, check=True)
try:
    subprocess.run(["docker", "exec", "-d", name, "node", "/tmp/cancellation-probe.mjs"], check=True)
    for _ in range(20):
        if fixture_count() == 2:
            break
        time.sleep(.1)
    assert fixture_count() == 2, "Detached child did not start"
    subprocess.run(["docker", "stop", "--time", "3", name], check=True, stdout=subprocess.DEVNULL)
    state = json.loads(run(["docker", "inspect", name]))[0]["State"]
    assert state["Running"] is False and state["Pid"] == 0
finally:
    # Also clean up a partially started fixture if a pre-stop assertion fails.
    if json.loads(run(["docker", "inspect", name]))[0]["State"]["Running"]:
        subprocess.run(["docker", "stop", "--time", "3", name], check=True, stdout=subprocess.DEVNULL)
    subprocess.run(["docker", "start", name], check=True, stdout=subprocess.DEVNULL)
for _ in range(30):
    if sorted(top()) == ["sshd", "tini"]:
        break
    time.sleep(.1)
assert sorted(top()) == ["sshd", "tini"], "Unexpected process after restart"
stat = ["docker", "exec", name, "stat", "-c", "%s", "/workspace/hq-cancellation-probe.marker"]
first = run(stat)
time.sleep(.5)
assert run(stat) == first, "Old child resumed"
assert not run(["docker", "exec", "-w", "/workspace/hq-pilot", name, "git", "status", "--porcelain"])
subprocess.run(["docker", "exec", name, "rm", "--", "/workspace/hq-cancellation-probe.marker"], check=True)
print(json.dumps({"synthetic": True, "detachedChildStarted": True, "containerStop": "Running=false/Pid=0", "restart": "no child resumed", "candidateGit": "clean", "nativePaperclipCancel": "not tested"}))
