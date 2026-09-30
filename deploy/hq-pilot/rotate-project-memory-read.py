"""Renew only ORIA HQ project read access. No key material is logged.

Run after an operator creates the dedicated root-owned directory. Uses the
existing trusted Memex signer; local payload checks do not verify signatures.
"""
import base64
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import time

DIRECTORY=Path('/opt/oria-hq-pilot/memex-project-read')
NAMESPACE='org:project:oria-hq'
SUBJECT='hq-project-oria-hq'

def validate_handle(raw, now):
    token=raw.strip()
    if len(token)>8192 or not re.fullmatch(r'amh1\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]{43}',token):
        raise ValueError('Invalid handle envelope')
    encoded=token.split('.')[1]
    payload=json.loads(base64.urlsafe_b64decode(encoded+'='*(-len(encoded)%4)))
    if (payload.get('sub')!=SUBJECT or payload.get('access')!='read_only'
        or payload.get('namespaces')!=[NAMESPACE]
        or type(payload.get('exp')) not in (int,float)
        or not now+300<payload['exp']<=now+3660):
        raise ValueError('Invalid project scope or expiry')
    return token

def rotate():
    import fcntl
    if os.geteuid()!=0 or not DIRECTORY.is_dir() or DIRECTORY.resolve()!=DIRECTORY:
        raise RuntimeError('Protected real directory required')
    info=DIRECTORY.stat()
    if info.st_uid!=0 or info.st_mode&0o022:
        raise RuntimeError('Directory must be root-owned without group/other writes')
    # Root-owned directory is not writable by the container; no shared temp lock.
    with open(DIRECTORY/'.renew.lock','a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        result=subprocess.run(['docker','exec','oria-memex-pilot-memex-1','node',
            '--experimental-strip-types','/app/pilot/mint-read-handle.mjs',
            SUBJECT,NAMESPACE,'3600'],capture_output=True,text=True,timeout=20)
        if result.returncode: raise RuntimeError('Signer unavailable')
        token=validate_handle(result.stdout,time.time())
        descriptor,temporary=tempfile.mkstemp(prefix='.handle-',dir=DIRECTORY)
        try:
            with os.fdopen(descriptor,'w') as output:
                os.fchmod(output.fileno(),0o400)
                os.fchown(output.fileno(),1000,1000)
                output.write(token+'\n');output.flush();os.fsync(output.fileno())
            os.replace(temporary,DIRECTORY/'handle')
            fd=os.open(DIRECTORY,os.O_RDONLY|os.O_DIRECTORY)
            try: os.fsync(fd)
            finally: os.close(fd)
        finally:
            if os.path.exists(temporary): os.unlink(temporary)

if __name__=='__main__':
    try:
        rotate()
        print('Project read handle renewed; scope unchanged.')
    except Exception:
        print('Project renewal failed; inspect renewal state before retrying.')
        raise SystemExit(1)
