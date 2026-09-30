"""Actual Docker deadline qualification; no provider, account or model."""
import json
from pathlib import Path
import time
import uuid
from supervisor import docker,supervise,state

IMAGE='sha256:3d8c97af6b8f1e6979596709f659124ca8f0319d5949e0f6f06f9c0287a7e11e'


def main():
    container=docker('create','--name','hq-deadline-probe-'+uuid.uuid4().hex,
        '--label','oria.purpose=openhands-supervised-job','--network','none',
        '--read-only','--user','10001:10001','--cap-drop','ALL','--security-opt','no-new-privileges:true',
        '--memory','128m','--pids-limit','32','--cpus','0.5','--entrypoint','python',IMAGE,
        '-c','import time; time.sleep(60)').stdout.strip()
    try:
        try:supervise(container_id=container,timeout_seconds=10,deadline_monotonic=time.monotonic()-1)
        except TimeoutError:pass
        else:raise AssertionError('Expired execution accepted')
        assert state(container)['Status']=='created'
        result=supervise(container_id=container,timeout_seconds=10,deadline_monotonic=time.monotonic()+1,grace_seconds=0)
        assert result['deadlineExceeded'] and result['containerStopped'] and result['elapsedSeconds']<8
        evidence={'expiredDeadlinePreventedStart':True,'nominalBudgetSeconds':10,
                  'remainingBudgetSeconds':1,'process':result,'modelRequests':0}
        (Path(__file__).parent/'shared-deadline-evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
        print(json.dumps(evidence))
    finally:docker('rm','-f',container)


if __name__=='__main__':main()
