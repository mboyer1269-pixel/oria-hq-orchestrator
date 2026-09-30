"""Prepare a detached local runtime clone. Never launches agent or project code."""
import os
from pathlib import Path
import re
import subprocess


def git_environment():
    environment = {key:value for key,value in os.environ.items() if not key.upper().startswith("GIT_")}
    environment.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull,
                       GIT_TERMINAL_PROMPT="0", GIT_LFS_SKIP_SMUDGE="1")
    return environment


def prepare_workspace(*, source, commit, server_root, job_name):
    if not isinstance(commit,str) or not re.fullmatch(r"(?:[a-f0-9]{40}|[a-f0-9]{64})",commit):
        raise ValueError("Exact commit hash required")
    if not isinstance(job_name,str) or not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_-]{0,79}",job_name):
        raise ValueError("Simple server-selected job name required")
    root = Path(server_root).resolve(strict=True)
    origin = Path(source).resolve(strict=True)
    if not root.is_dir() or not origin.is_dir():
        raise ValueError("Source and server root must be directories")
    if root == origin or root.is_relative_to(origin):
        raise ValueError("Server root must be outside the source repository")
    target = root/job_name
    if target.exists() or target.is_symlink():
        raise FileExistsError("Destination already exists")
    if target.resolve().parent != root:
        raise ValueError("Destination escapes server root")
    env = git_environment()
    config = ["git","--no-replace-objects","-c","core.hooksPath="+os.devnull,
              "-c","protocol.allow=never","-c","protocol.file.allow=always",
              "-c","submodule.recurse=false","-c","filter.lfs.required=false",
              "-c","filter.lfs.smudge=","-c","filter.lfs.process="]

    def run(args, timeout=30):
        return subprocess.run(config+args,env=env,capture_output=True,text=True,check=True,timeout=timeout).stdout.strip()

    if Path(run(["-C",str(origin),"rev-parse","--show-toplevel"])).resolve()!=origin:
        raise ValueError("Source must be checkout root")
    if run(["-C",str(origin),"cat-file","-t",commit])!="commit":
        raise ValueError("Object is not a commit")
    # Reserve atomically. Any failure retains the new directory for inspection.
    target.mkdir(mode=0o700)
    run(["clone","--no-local","--no-hardlinks","--no-checkout","--no-recurse-submodules",
         "--template=",str(origin),str(target)],timeout=120)
    run(["-C",str(target),"config","core.hooksPath",os.devnull])
    run(["-C",str(target),"config","submodule.recurse","false"])
    run(["-C",str(target),"checkout","--detach",commit,"--"],timeout=120)
    # Agent copies have no configured push/fetch destination. This is an
    # accidental-write guard; container mounts still enforce source isolation.
    run(["-C",str(target),"remote","remove","origin"])
    head=run(["-C",str(target),"rev-parse","HEAD"])
    status=run(["-C",str(target),"status","--porcelain=v1","--untracked-files=all"])
    if head!=commit or status:
        raise ValueError("Prepared checkout does not match requested clean commit")
    return {"status":"prepared","checkout":str(target),"commitSha":head,
            "clean":True,"executionRequested":False}
