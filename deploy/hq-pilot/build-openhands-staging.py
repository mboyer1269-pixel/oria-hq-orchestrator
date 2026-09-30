"""Operator-only candidate build; reads only public browser config from existing HQ.

No service-role key or provider credential goes to the build. Does not deploy.
"""
import json
import argparse
import re
import os
from pathlib import Path
import subprocess

ROOT=Path('/opt/oria-openhands-qualification')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-image',required=True)
    parser.add_argument('--tag',default='oria-hq-staging:openhands')
    args=parser.parse_args()
    if not re.fullmatch(r'sha256:[a-f0-9]{64}',args.source_image): parser.error('Immutable image ID required')
    if not re.fullmatch(r'oria-hq-staging:[a-z0-9][a-z0-9_.-]{0,127}',args.tag):parser.error('Local staging tag required')
    source=args.source_image
    alias='oria-hq-staging-source:'+source.removeprefix('sha256:')
    inspected=json.loads(subprocess.check_output(['docker','inspect','oria-hq-pilot-hq-1'],text=True))[0]
    values=dict(entry.split('=',1) for entry in inspected['Config']['Env'] if '=' in entry)
    env=os.environ.copy()
    for name in ('NEXT_PUBLIC_SUPABASE_URL','NEXT_PUBLIC_SUPABASE_ANON_KEY'):
        if not values.get(name): raise RuntimeError('Required public build configuration missing')
        env[name]=values[name]
    subprocess.run(['docker','tag',source,alias],check=True)
    # Build context contains only this Dockerfile; source is the verified image.
    subprocess.run(['docker','build','--pull=false','--network=none',
        '--build-arg','SOURCE_IMAGE='+alias,
        '--build-arg','NEXT_PUBLIC_SUPABASE_URL','--build-arg','NEXT_PUBLIC_SUPABASE_ANON_KEY',
        '-f',str(ROOT/'staging-build/OpenHands.staging.Dockerfile'),
        '-t',args.tag,str(ROOT/'staging-build')],env=env,check=True,timeout=600)
    print(subprocess.check_output(['docker','image','inspect',args.tag,'--format','{{.Id}}'],text=True).strip())

if __name__=='__main__': main()
