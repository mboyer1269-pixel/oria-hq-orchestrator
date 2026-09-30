#!/usr/bin/env python3
"""Operator-only coordinated pilot recovery drill; never deletes volumes/backups.
Controller MUST stop source first and restart it in its own finally block.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time

IMAGE = 'sha256:23805a5b18f4dd3379eaf4f43c6f36c9aaf9deade53a74346fcff214270561d7'
SOURCE_HASH = '67b097bf05a54668ab804ec984d493d8b8ad1f1eebf1a6f3225ebf9ed79dc7d3'
VOLUMES = {f'oria-memex-{part}-pilot': f'/runtime/{part}' for part in ['graph', 'intake', 'vault']}
ENV = {'AGENTMEMORY_DB_PATH': '/runtime/graph/graph.db', 'AGENTMEMORY_INTAKE_DB_PATH': '/runtime/intake/intake.db',
       'AGENTMEMORY_VAULT_PATH': '/runtime/vault', 'GATEWAY_HOST': '0.0.0.0', 'GATEWAY_PORT': '3000',
       'GATEWAY_DEFAULT_ACCESS': 'read_write', 'NODE_OPTIONS': '--max-old-space-size=256'}

def docker(*args, **kwargs):
    result = subprocess.run(['docker', *args], stdout=kwargs.pop('stdout', subprocess.PIPE),
                            stderr=subprocess.PIPE, **kwargs)
    if result.returncode:
        raise RuntimeError('Docker operation failed (details intentionally not printed)')
    return result.stdout

def inspect(kind, name):
    return json.loads(docker(kind, 'inspect', name))[0]

def absent(kind, name):
    # Inspect failure alone is not proof of absence: list must itself succeed.
    if name in docker(kind, 'ls', '--format', '{{.Name}}').decode().splitlines():
        raise RuntimeError('Recovery resource already exists')

def source_stopped(container):
    state = inspect('container', container)['State']
    if state.get('Running') or state.get('Restarting') or state.get('Paused'):
        raise RuntimeError('Source must remain stopped throughout coordinated capture')

def isolated_args():
    return ['--network', 'none', '--read-only', '--user', '1000:1000', '--cap-drop', 'ALL',
            '--security-opt', 'no-new-privileges', '--cpus', '1', '--memory', '512m', '--pids-limit', '96',
            '--tmpfs', '/tmp:rw,nosuid,nodev,size=64m,mode=1777']

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--backup-root', required=True, help='Existing private absolute directory outside repository')
    parser.add_argument('--run-id', required=True, help='Unique lowercase letters/digits/hyphens; no reuse')
    parser.add_argument('--source-manifest', required=True)
    parser.add_argument('--probe', required=True, help='Reviewed runtime-probe.mjs')
    args = parser.parse_args()
    os.umask(0o077)
    if os.geteuid() != 0:
        raise RuntimeError('Run as trusted VPS root operator')
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{2,39}', args.run_id):
        raise RuntimeError('Invalid unique run-id')
    backup_root = Path(args.backup_root)
    if not backup_root.is_absolute() or not backup_root.is_dir() or backup_root.is_symlink():
        raise RuntimeError('Backup root must be an existing private absolute directory')
    if backup_root.stat().st_mode & 0o077:
        raise RuntimeError('Backup root must deny group/other access')
    source_manifest = Path(args.source_manifest).read_bytes()
    if hashlib.sha256(source_manifest).hexdigest() != SOURCE_HASH:
        raise RuntimeError('Source manifest differs from validated image input')
    probe = Path(args.probe).read_bytes()
    sources = docker('ps', '-aq', '--filter', 'label=com.docker.compose.project=oria-memex-pilot',
                     '--filter', 'label=com.docker.compose.service=memex').decode().split()
    if len(sources) != 1:
        raise RuntimeError('Expected exactly one fixed pilot source container')
    source = sources[0]
    data = inspect('container', source)
    source_stopped(source)
    if data['Image'] != IMAGE:
        raise RuntimeError('Source image differs from validated image')
    mounts = data['Mounts']
    for volume, target in VOLUMES.items():
        matches = [m for m in mounts if m.get('Type') == 'volume' and m.get('Name') == volume and m['Destination'] == target]
        if len(matches) != 1:
            raise RuntimeError('Source volume identity mismatch')
    mounted_volumes = {m['Name'] for m in mounts if m['Type'] == 'volume'}
    if mounted_volumes != set(VOLUMES):
        raise RuntimeError('Unexpected source volume set')
    for volume in VOLUMES:
        if docker('ps', '-q', '--filter', f'volume={volume}').strip():
            raise RuntimeError('A running container still mounts a source volume')
    secrets = [m for m in mounts if m['Destination'] == '/run/secrets/handle-signing-key' and m['Type'] == 'bind' and not m['RW']]
    if len(secrets) != 1:
        raise RuntimeError('Expected a single read-only signing key bind mount')
    actual_env = dict(item.split('=', 1) for item in data['Config']['Env'])
    if any(actual_env.get(k) != v for k, v in ENV.items()):
        raise RuntimeError('Source runtime configuration mismatch')
    name = f'oria-memex-restore-{args.run_id}'
    # docker container ls uses .Names rather than .Name.
    if name in docker('ps', '-a', '--format', '{{.Names}}').decode().splitlines():
        raise RuntimeError('Recovery container already exists')
    restored = {v: f'{v}-restore-{args.run_id}' for v in VOLUMES}
    for volume in restored.values():
        absent('volume', volume)
    backup = backup_root / args.run_id
    backup.mkdir(mode=0o700)  # existing path fails; never overwrite.
    records = {'image': IMAGE, 'sourceManifestSha256': SOURCE_HASH, 'sourceContainer': source,
               'runtimeEnvironment': ENV, 'restoredContainer': name, 'volumes': {}, 'status': 'capturing'}
    def record():
        (backup / 'recovery-evidence.json').write_text(json.dumps(records, indent=2) + '\n')
    record()
    clone_created = False
    try:
        shutil.copyfile(args.source_manifest, backup / 'source-manifest.json')
        key_bytes = Path(secrets[0]['Source']).read_bytes()
        if len(key_bytes.strip()) < 32:
            raise RuntimeError('Invalid signing key file')
        backup_key = backup / 'handle-signing-key'
        backup_key.write_bytes(key_bytes)
        os.chmod(backup_key, 0o600)
        key = backup / 'restore-handle-signing-key'
        key.write_bytes(key_bytes)
        os.chown(key, 1000, 1000)
        os.chmod(key, 0o400)
        for volume, target in VOLUMES.items():
            source_stopped(source)
            archive = backup / f'{volume}.tar'
            with archive.open('xb') as output:
                docker('run', '--rm', *isolated_args(), '--mount', f'type=volume,source={volume},target={target},readonly',
                       '--entrypoint', 'tar', IMAGE, '-C', target, '-cf', '-', '.', stdout=output)
            with archive.open('rb') as captured:
                archive_hash = hashlib.file_digest(captured, 'sha256').hexdigest()
            records['volumes'][volume] = {'archive': archive.name, 'sha256': archive_hash,
                                           'restoreVolume': restored[volume], 'target': target}
            record()
        source_stopped(source)
        records['status'] = 'captured'
        record()
        for volume, target in VOLUMES.items():
            docker('volume', 'create', '--label', f'oria.recovery.run={args.run_id}', restored[volume])
            with (backup / f'{volume}.tar').open('rb') as archive:
                docker('run', '--rm', '-i', *isolated_args(), '--mount', f'type=volume,source={restored[volume]},target={target}',
                       '--entrypoint', 'tar', IMAGE, '-C', target, '-xf', '-', stdin=archive)
            with (backup / f'{volume}.tar').open('rb') as archive:
                docker('run', '--rm', '-i', *isolated_args(), '--mount', f'type=volume,source={restored[volume]},target={target},readonly',
                       '--entrypoint', 'tar', IMAGE, '-C', target, '--compare', '-f', '-', stdin=archive)
            records['volumes'][volume]['archiveCompare'] = 'pass'
            record()
        run = ['run', '-d', '--name', name, '--label', f'oria.recovery.run={args.run_id}', '--init', *isolated_args()]
        for volume, target in VOLUMES.items():
            run += ['--mount', f'type=volume,source={restored[volume]},target={target}']
        run += ['--mount', f'type=bind,source={key},target=/run/secrets/handle-signing-key,readonly']
        for k, v in ENV.items():
            run += ['--env', f'{k}={v}']
        docker(*run, IMAGE)
        clone_created = True
        for attempt in range(30):
            result = subprocess.run(['docker', 'exec', name, 'node', '-e',
                "fetch('http://127.0.0.1:3000/health').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"], capture_output=True)
            if result.returncode == 0:
                break
            time.sleep(1)
        else:
            raise RuntimeError('Restored gateway did not become healthy')
        evidence = docker('exec', '-i', '--env', 'MODE=verify', name, 'node', '--experimental-strip-types', '--input-type=module', input=probe)
        verdict = json.loads(evidence)
        if verdict.get('mode') != 'verify' or verdict.get('exactCanaries') != 'pass' or verdict.get('signedHttpRead') != 'pass':
            raise RuntimeError('Restored synthetic verification failed')
        records['probe'] = verdict
        records['status'] = 'restore-verified'
        record()
    except BaseException:
        records['status'] = 'failed'
        record()
        raise
    finally:
        if clone_created:
            docker('stop', '--time', '10', name)
            records['restoredContainerStopped'] = not inspect('container', name)['State']['Running']
            record()
        # Intentionally retain stopped clone, volumes, archives, key and evidence.
        # Controller must restart the ORIGINAL source even on any failure above.
    print(json.dumps({'status': 'restore-verified', 'runId': args.run_id, 'volumes': 3, 'network': 'none', 'cloneStopped': True}))

if __name__ == '__main__':
    try:
        main()
    except BaseException:
        print(json.dumps({'status': 'failed', 'action': 'inspect private evidence; controller must restart source'}))
        raise SystemExit(1)
