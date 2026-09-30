"""Explicit Docker qualification; disposable no-network Python jobs, no model."""
import json
from supervisor import docker, state, supervise


def create(code):
    return docker("create", "--network", "none", "--read-only",
                  "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
                  "--pids-limit", "32", "--memory", "128m", "--cpus", "0.5",
                  "--label", "oria.purpose=openhands-supervised-job",
                  "--label", "oria.qualification=deadline",
                  "--entrypoint", "python",
                  "oria-openhands-claude:qualification1", "-c", code).stdout.strip()


def main():
    successful = create("print('qualification completed')")
    result = supervise(container_id=successful, timeout_seconds=10)
    if result["exitCode"] != 0 or result["deadlineExceeded"]:
        raise RuntimeError("Success verdict failed")
    try:
        supervise(container_id=successful, timeout_seconds=10)
    except ValueError:
        pass
    else:
        raise RuntimeError("Completed container was restarted")
    failed = create("raise SystemExit(7)")
    failure = supervise(container_id=failed, timeout_seconds=10)
    if failure["exitCode"] != 7:
        raise RuntimeError("Workload failure hidden")
    stalled = create("import signal,time; signal.signal(signal.SIGTERM,signal.SIG_IGN); time.sleep(120)")
    deadline = supervise(container_id=stalled, timeout_seconds=2, grace_seconds=1)
    if not deadline["deadlineExceeded"] or state(stalled)["Running"]:
        raise RuntimeError("Deadline failed")
    print(json.dumps({"success": result, "failure": failure, "deadline": deadline,
                      "restartRefused": True, "retainedContainers": [successful, failed, stalled],
                      "modelCalled": False}))


if __name__ == "__main__":
    main()
