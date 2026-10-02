"""Verify a protected provider manifest. Verification is never execution permission."""
import hashlib
import json
import os
from pathlib import Path,PurePosixPath
import re
import stat

ROOT=Path('/etc/oria-hq/provider-policies')
PROFILE_FIELDS={'id','policySha256','provider','authentication','network','accountConnectors'}
# Each supported provider has its own explicit, fully-spelled policy template.
# Supporting a new provider means adding a new entry here, never widening a
# shared field's type (e.g. provider from a literal to an open string). A
# profile is checked only against the single template named by its own
# declared `provider`, so a Codex profile can never be satisfied by Claude's
# template (or vice versa): no policy, relay or proxy qualified for one
# provider can be presented as another's.
PROVIDER_POLICIES={
    'claude':{'provider':'claude','authentication':'subscription','network':'restricted-proxy','accountConnectors':'disabled'},
    'codex':{'provider':'codex','authentication':'subscription','network':'restricted-proxy','accountConnectors':'disabled'},
}
# Backward-compatible alias to the Claude template: kept so the already
# qualified Claude profile/digest and existing callers (qualify_hq_postgrest.py)
# are unaffected. Never read as "the" expected policy for any other provider.
EXPECTED=PROVIDER_POLICIES['claude']
FILES={'squid.conf','entrypoint.sh','relay.mjs'}
AUTHORIZATION={'profileId','policySha256','policyRoot','gatewayRoot'}


def unique(pairs):
    value={}
    for key,item in pairs:
        if key in value:raise ValueError('Duplicate policy key')
        value[key]=item
    return value


def provider_policy_template(provider):
    """The one policy a profile for this provider must match exactly. Raises for
    any provider not explicitly enumerated in PROVIDER_POLICIES - never falls
    back to a default template or to another provider's template."""
    template=PROVIDER_POLICIES.get(provider)
    if template is None:raise ValueError('Unsupported provider')
    return template


def validate_profile(profile):
    if not isinstance(profile,dict) or set(profile)!=PROFILE_FIELDS:
        raise ValueError('Invalid provider profile')
    if not isinstance(profile['id'],str) or not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,79}',profile['id']):
        raise ValueError('Invalid profile identity')
    if not isinstance(profile['policySha256'],str) or not re.fullmatch(r'[a-f0-9]{64}',profile['policySha256']):
        raise ValueError('Invalid policy digest')
    template=provider_policy_template(profile.get('provider'))
    if any(profile[key]!=value for key,value in template.items()):raise ValueError('Unsupported policy')


def validate_manifest(raw,profile,runtime_image):
    validate_profile(profile)
    if len(raw)>16384 or hashlib.sha256(raw).hexdigest()!=profile['policySha256']:
        raise ValueError('Policy digest mismatch')
    manifest=json.loads(raw,object_pairs_hook=unique,
                        parse_constant=lambda _:(_ for _ in ()).throw(ValueError('Nonfinite policy')))
    # The profile already proved its own provider matches one explicit
    # template; the manifest must match that same template exactly, so a
    # manifest that declares (or silently defaults to) a different provider
    # than the profile can never pass - no cross-provider reuse by digest.
    template=provider_policy_template(profile['provider'])
    keys=set(template)|{'version','agentNetwork','runtimeImage','proxyImage','relayPort','socketPath','files'}
    if not isinstance(manifest,dict) or set(manifest)!=keys:raise ValueError('Unexpected policy fields')
    if type(manifest['version']) is not int or manifest['version']!=1:raise ValueError('Unsupported policy version')
    if any(manifest[key]!=value for key,value in template.items()):raise ValueError('Profile policy mismatch')
    if manifest['agentNetwork']!='none' or manifest['socketPath']!='/provider/provider.sock':raise ValueError('Unsupported transport')
    if type(manifest['relayPort']) is not int or manifest['relayPort']!=3129:raise ValueError('Unsupported relay port')
    for name in ('runtimeImage','proxyImage'):
        if not isinstance(manifest[name],str) or not re.fullmatch(r'sha256:[a-f0-9]{64}',manifest[name]):raise ValueError('Pinned image required')
    if manifest['runtimeImage']!=runtime_image:raise ValueError('Runtime image mismatch')
    files=manifest['files']
    if not isinstance(files,dict) or set(files)!=FILES or any(
            not isinstance(value,str) or not re.fullmatch(r'[a-f0-9]{64}',value) for value in files.values()):
        raise ValueError('Invalid policy artifacts')
    if json.dumps(manifest,sort_keys=True,separators=(',',':')).encode()!=raw:raise ValueError('Canonical policy required')
    return manifest


def protected_bytes(path,limit):
    if os.name!='posix':raise ValueError('Linux host required')
    path=Path(path)
    if not path.is_absolute() or path.resolve(strict=True)!=path:raise ValueError('Real absolute policy path required')
    for parent in path.parents:
        info=parent.stat()
        if info.st_uid!=0 or info.st_mode & 0o022:raise ValueError('Unprotected policy directory')
    descriptor=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    with os.fdopen(descriptor,'rb') as stream:
        info=os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_uid!=0 or info.st_mode & 0o022:
            raise ValueError('Unprotected policy file')
        raw=stream.read(limit+1)
        if len(raw)>limit:raise ValueError('Oversized policy file')
        return raw


def load_provider_policy(config,root=ROOT):
    profile=config['providerProfile'];validate_profile(profile)
    folder=Path(root)/profile['id']
    manifest=validate_manifest(protected_bytes(folder/'policy.json',16384),profile,config['imageDigest'])
    for name,expected in manifest['files'].items():
        if hashlib.sha256(protected_bytes(folder/name,65536)).hexdigest()!=expected:
            raise ValueError('Policy artifact mismatch')
    return manifest


def validate_authorization(authorization):
    """Operator-declared approval of one profile. Never read from HQ or a dossier."""
    if not isinstance(authorization,dict) or set(authorization)!=AUTHORIZATION:
        raise ValueError('Invalid provider authorization')
    if not isinstance(authorization['profileId'],str) or not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,79}',authorization['profileId']):
        raise ValueError('Invalid authorized profile identity')
    if not isinstance(authorization['policySha256'],str) or not re.fullmatch(r'[a-f0-9]{64}',authorization['policySha256']):
        raise ValueError('Invalid authorized policy digest')
    for field in ('policyRoot','gatewayRoot'):
        root=authorization[field]
        if (not isinstance(root,str) or not 1<len(root)<=4096 or chr(0) in root or not root.startswith('/')
                or str(PurePosixPath(root))!=root or '..' in PurePosixPath(root).parts):
            raise ValueError('Absolute host path required for '+field)
    if authorization['policyRoot']==authorization['gatewayRoot']:
        raise ValueError('Separate policy registry and gateway roots required')
    return authorization


def separate_gateway_root(gateway,others):
    """One rule for every caller: the gateway shares no subtree with these paths."""
    for other in others:
        if gateway==other or gateway in other.parents or other in gateway.parents:
            raise ValueError('Separate protected gateway root required')
    return gateway


def authorized_profile(config,authorization):
    """Refuse any canonical profile the operator did not approve by identity and digest."""
    validate_authorization(authorization)
    profile=config.get('providerProfile')
    validate_profile(profile)
    if (profile['id'],profile['policySha256'])!=(authorization['profileId'],authorization['policySha256']):
        raise ValueError('Canonical profile is not the authorized profile')
    return profile


def provider_preflight(config,authorization=None):
    if 'providerProfile' not in config:return None
    try:
        if authorization is None:load_provider_policy(config)
        else:
            authorized_profile(config,authorization)
            # The approved registry is named by the authorization, never guessed.
            load_provider_policy(config,authorization['policyRoot'])
    except (ValueError,TypeError,KeyError,OSError):
        return {'state':'invalid_provider_policy','started':False}
    # Policy integrity does not prove credentials, relay lifecycle or tool review.
    if authorization is None:return {'state':'unsupported_provider_profile','started':False}
    # The operator approved this exact policy here. Nothing is started yet: the
    # worker repeats both checks against the canonical reread before any effect.
    return None
