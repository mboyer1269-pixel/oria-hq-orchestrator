"""Container guardian for the fixed provider relay and mission child."""
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import time


def stop(process):
    if process is None:return
    # Also stop descendants when the direct child has already exited.
    try:os.killpg(process.pid,signal.SIGTERM)
    except ProcessLookupError:pass
    try:process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        try:os.killpg(process.pid,signal.SIGKILL)
        except ProcessLookupError:pass
        process.wait(timeout=3)


def monitor(relay,worker):
    while True:
        if relay.poll() is not None:return 70
        result=worker.poll()
        if result is not None:return result
        time.sleep(0.05)


def run_relay_job(arguments):
    if os.name!='posix':raise ValueError('Linux runtime required')
    if '--provider-relay' in arguments:raise ValueError('Recursive relay invocation')
    relay=None;worker=None
    environment=dict(os.environ)
    for key in ('ALL_PROXY','all_proxy'):environment.pop(key,None)
    for key in ('HTTP_PROXY','HTTPS_PROXY','http_proxy','https_proxy'):
        environment[key]='http://127.0.0.1:3129'
    environment.update(NO_PROXY='',no_proxy='',ENABLE_CLAUDEAI_MCP_SERVERS='false')
    try:
        relay=subprocess.Popen(['/usr/local/bin/node','/provider-relay.mjs'],stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,start_new_session=True,env=environment)
        readable,_,_=select.select([relay.stdout],[],[],5)
        if not readable or os.read(relay.stdout.fileno(),64)!=b'ready\n' or relay.poll() is not None:
            return 70
        worker=subprocess.Popen([sys.executable,str(Path(__file__).with_name('run_mission.py')),*arguments],
            stdin=subprocess.DEVNULL,start_new_session=True,env=environment)
        return monitor(relay,worker)
    finally:
        try:stop(worker)
        finally:
            try:stop(relay)
            finally:
                if relay is not None and relay.stdout is not None:relay.stdout.close()
