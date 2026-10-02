# Exact state — Codex ACP candidate

Not built. Not qualified. No container run against this Dockerfile.

## Why

`PERMISSION_BASE` (`oria-openhands-qualification:permissions1`), the already-
qualified Claude candidate's own build/qualification images
(`oria-openhands-claude:qualification1`), and their proof artifacts do not
exist in this session's Docker Desktop (`docker images` has no `oria-*`
entries here - confirmed before writing any file, per the mandate's
"compare before reconstructing" instruction). Those images were produced in
whatever environment actually ran `../openhands-claude-runtime/qualify.sh`
previously; this session cannot chain `FROM ${PERMISSION_BASE}` without
rebuilding that base first, which is out of this mandate's scope (it belongs
to `../openhands-permission-extension/`, already qualified separately).

What *is* available in this session and was used, read-only, with no model
call and no login:
- Docker Desktop itself (`docker --version` → 29.4.0), network access to
  `registry.npmjs.org` and `raw.githubusercontent.com` for provenance, and
  the stopped `ghcr.io/openhands/agent-canvas:1.0.0-rc.11` image - see the
  comparison table in `README.md`.
- `npm install --package-lock-only --ignore-scripts` against the pinned
  `package.json` here, to produce a real, verifiable `package-lock.json`
  (sha256 of the lock file itself: run `sha256sum package-lock.json` to
  reproduce - it is checked into this directory, not asserted from memory).

What was deliberately not attempted:
- `docker build` against this Dockerfile (would fail immediately on the
  missing `PERMISSION_BASE`, and building the base is out of scope here).
- Any `codex-acp login`, `codex login`, `--authenticate` request, or network
  call to OpenAI/ChatGPT endpoints.
- Any read, list, or mount of `C:/Users/micha/Dev/openhands-credentials/` or
  `C:/Users/micha/.openhands`.
- Rebuilding or modifying `ghcr.io/openhands/agent-canvas:1.0.0-rc.11` in
  any way (it was only inspected: `docker image inspect`, `docker history
  --no-trunc`, and one bounded `--network none --read-only --cap-drop ALL`
  container run executing only `command -v`/`--version` checks against
  binaries already present in that image, nothing installed or logged in).

## To actually qualify this candidate (next prerequisites)

1. Rebuild or locate the `oria-openhands-qualification:permissions1` and
   `oria-openhands-claude:qualification1` images (or an equivalent
   `oria-openhands-codex:qualification1` built the same way) on a host that
   already has them, or rerun `../openhands-permission-extension/`'s own
   qualification to produce `PERMISSION_BASE` fresh.
2. `docker build -t oria-openhands-codex:qualification1 integrations/openhands-codex-runtime`
   from the Orchestrator repo root, with `PERMISSION_BASE` resolved.
3. `qualify.sh qualify_initialize.py` then `qualify.sh qualify_tools.py`,
   exactly as for the Claude candidate, still with no login and no model
   call - this only proves the ACP stdio handshake and that the bundled
   `codex` App Server subprocess starts locally.
4. Only after that: the official `codex-acp login` sequence documented in
   README.md, on a dedicated private home volume, never touching Hermes'
   `~/.codex/auth.json`.
5. Only after that: widen `integrations/openhands-runner/provider_policy.py`'s
   deployed `/etc/oria-hq/provider-policies/<id>/` registry with a real
   `codex-*` policy folder (squid.conf/entrypoint.sh/relay.mjs authored for
   Codex's actual env/network surface, not copied from Claude's), get it
   approved via `validate_authorization`, and extend
   `model-emission-launch-gate.ts`'s `PROVIDER_PROFILE_TO_REGISTRY_PROVIDER_ID`
   - both explicitly out of this mandate's scope.

## Reproducible commands used in this session

```sh
# Pin and resolve the dependency graph (no scripts run, no network beyond npm registry)
cd integrations/openhands-codex-runtime
npm install --package-lock-only --ignore-scripts --no-audit --no-fund

# Confirm no oria-* qualification images exist locally
docker images --format '{{.Repository}}:{{.Tag}} {{.ID}}' | grep -i oria   # (no output)

# Read-only comparison against the stopped local image (no mounts, no network)
docker image inspect ghcr.io/openhands/agent-canvas:1.0.0-rc.11
docker history --no-trunc ghcr.io/openhands/agent-canvas:1.0.0-rc.11

docker run --rm --network none --read-only --cap-drop ALL \
  --security-opt no-new-privileges --pids-limit 64 --memory 256m \
  --tmpfs /tmp:rw,nosuid,nodev,size=64m --entrypoint sh \
  ghcr.io/openhands/agent-canvas:1.0.0-rc.11 -c \
  'for b in claude-agent-acp codex-acp gemini; do command -v "$b" && "$b" --version; done'
```
