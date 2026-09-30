"""Private execution bindings to HQ/Memex project identities; no memory handles."""
import json
import argparse
import os
import sys
from pathlib import Path
from run_host_job import protected_path,unique_object
from hq_transition import lifecycle_reader
from prepare_host_job import prepare_host_job


def parse_sources(raw):
    if not isinstance(raw,str) or len(raw.encode('utf-8'))>32768:raise ValueError('Bounded source registry required')
    registry=json.loads(raw,object_pairs_hook=unique_object)
    if not isinstance(registry,dict) or set(registry)!={'version','entries'} or type(registry['version']) is not int or registry['version']!=1:
        raise ValueError('Unsupported source registry')
    entries=registry['entries']
    if not isinstance(entries,list) or len(entries)>20:raise ValueError('Invalid source entries')
    seen=set()
    for entry in entries:
        if not isinstance(entry,dict) or set(entry)!={'workspaceId','projectId','runnerId','sourceRoot'}:raise ValueError('Invalid source entry')
        for key in ('workspaceId','projectId','runnerId'):
            value=entry[key]
            if not isinstance(value,str) or not 1<=len(value)<=160 or value.strip()!=value:raise ValueError('Invalid source identity')
        value=entry['sourceRoot']
        if not isinstance(value,str) or not 1<=len(value)<=4096 or '\0' in value or not Path(value).is_absolute():raise ValueError('Absolute host source required')
        key=(entry['workspaceId'],entry['projectId'],entry['runnerId'])
        if key in seen:raise ValueError('Ambiguous source binding')
        seen.add(key)
    return entries


def select_source(entries,observed):
    claim=observed['claim'];dossier=observed['dossier']
    memory=dossier.get('memory')
    if dossier.get('contractVersion')!=2 or not isinstance(memory,dict):raise ValueError('Integrated profile requires canonical project memory')
    if memory.get('workspaceId')!=claim['workspaceId'] or dossier['mission']['workspaceId']!=claim['workspaceId']:
        raise ValueError('Project workspace mismatch')
    matched=[e for e in entries if (e['workspaceId'],e['projectId'],e['runnerId'])==
             (claim['workspaceId'],memory.get('projectId'),claim['runnerId'])]
    if len(matched)!=1:raise ValueError('Project source not uniquely bound')
    return matched[0]['sourceRoot']


def prepare_configured_project(*,command,registry_file,jobs_root,control_root,expected_payload_hash=None):
    registry=protected_path(registry_file)
    if registry.stat().st_size>32768:raise ValueError('Oversized source registry')
    entries=parse_sources(registry.read_text(encoding='utf-8'))
    observed=lifecycle_reader(command,prepare=True)()
    if expected_payload_hash is not None and observed['claim']['payloadHash']!=expected_payload_hash:
        raise ValueError('Discovered payload changed before preparation')
    source=select_source(entries,observed)
    # Recheck canonical binding on the preparation read: an intervening change
    # must not switch projects while retaining the first source selection.
    return prepare_host_job(command=command,source=source,jobs_root=jobs_root,control_root=control_root,
                            expected_payload_hash=observed['claim']['payloadHash'])


def prepare_configuration(filename):
    """Root operator configuration, never arguments supplied by a mission."""
    if os.name!='posix' or os.geteuid()!=0:raise ValueError('Linux root operator required')
    path=protected_path(filename)
    if path.stat().st_size>16384:raise ValueError('Oversized preparation configuration')
    config=json.loads(path.read_text(encoding='utf-8'),object_pairs_hook=unique_object)
    if not isinstance(config,dict) or set(config)!={'lifecycleCommand','registryFile','jobsRoot','controlRoot'}:
        raise ValueError('Invalid preparation configuration fields')
    command=config['lifecycleCommand']
    if not isinstance(command,list) or not 1<=len(command)<=32 or any(
            not isinstance(arg,str) or not arg or len(arg)>4096 or '\0' in arg for arg in command):
        raise ValueError('Explicit host command required')
    protected_path(command[0])
    # Validate all host paths before invoking any lifecycle subprocess.
    registry=protected_path(config['registryFile'])
    jobs=protected_path(config['jobsRoot'],directory=True)
    controls=protected_path(config['controlRoot'],directory=True)
    return prepare_configured_project(command=tuple(command),registry_file=registry,
                                      jobs_root=jobs,control_root=controls)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',required=True)
    args=parser.parse_args()
    try:
        print(json.dumps(prepare_configuration(args.config)))
        return 0
    except Exception:
        # Partial preparation may exist. Never leak configuration or retry.
        print(json.dumps({'state':'preparation_not_confirmed','automaticRetry':False}))
        return 2


if __name__=='__main__':sys.exit(main())
