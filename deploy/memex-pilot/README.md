# Memex isolated runtime pilot

Prepared deployment assets, not deployed by this task. This runtime is distinct from local AgentMemory development memory. Never copy `.agentmemory`, local databases, `data`, vaults, credentials, node_modules or developer home into the snapshot.

## Build inputs and Linux compatibility

Dockerfile pins the official Docker Hub `node:22-bookworm-slim` **linux/amd64** child manifest `sha256:25330af3531fb5e23318554a0aa911125b6e91b1b777edf7655501d207c067a2`, resolved with `docker manifest inspect` on 2026-09-29. Check VPS architecture is amd64. This is a registry digest pin, not an artifact-attestation claim. Debian compiler dependencies are resolved at build time; archive the final built image digest for exact reuse.

Node22 supports the code's experimental type stripping. `better-sqlite3` must be installed on Linux: the dependency stage uses npm ci with the reviewed lockfile and compiler fallback, then tests native load and FTS5 creation. Windows node_modules are never copied. Runtime contains no compiler or npm-installed provider CLI. Code and dependencies remain root-owned and read-only, UID1000 executes them.

Wait for the Memex correctness/security agents to freeze source. Then run from the Orchestrator checkout (new snapshot outside the repositories):

```sh
node deploy/memex-pilot/snapshot.mjs /path/to/memex-core /path/to/new-reviewed-snapshot
export MEMEX_SOURCE_SNAPSHOT=/path/to/new-reviewed-snapshot
export MEMEX_HANDLE_SECRET_FILE=/outside/repo/memex-handle-signing-key
docker compose -f deploy/memex-pilot/compose.json config --quiet
docker compose -f deploy/memex-pilot/compose.json build memex
```

The snapshot includes only package manifests, src and the two exact MCP capability catalogs (`fixtures/mcp-tools-list.expected.json`, `fixtures/mcp-resources-list.expected.json`); its source-manifest.json captures file hashes, including reviewed uncommitted changes. Do not generate the final snapshot while agents edit. BuildKit additional contexts are required (Compose >=2.17). The signing key is a dedicated random value of at least 32 characters, provisioned outside Git, readable by container UID1000, not world-readable. Compose file-backed secrets preserve host permissions; `uid`/`mode` remapping cannot be assumed. Never print the key in logs. Do not reuse an AgentMemory signing key.

## Isolated acceptance before starting the persistent runtime

```sh
docker run --rm --network none --user 1000:1000 --read-only \
  --cap-drop ALL --security-opt no-new-privileges \
  --memory 512m --pids-limit 96 --tmpfs /tmp:rw,nosuid,nodev,size=64m,mode=1777 \
  --entrypoint node oria-memex-pilot:source-reviewed \
  --experimental-strip-types /app/pilot/acceptance.mjs
```

This harness always creates disposable SQLite/vault files under its own temp directory and fresh in-memory signing material; it never uses mounted runtime data or production credentials. It exercises actual HTTP Authorization Bearer handles, proposal attribution, approval/publication, retry idempotency, scoped reads, cross-project denial, read-only write denial, expired/tampered handles and blocked raw vault access. Local Windows run passed; Linux image run still required. This is not a substitute for the source test suite or the partial-publication regression owned by the correctness agent.

## Runtime

```sh
docker compose -f deploy/memex-pilot/compose.json up -d --no-build memex
```

Only the gateway starts; no autonomous worker or automatic approval, distillation or consolidation. Graph, intake journal and vault persist in three separate named pilot volumes. New volumes copy UID1000 ownership from image directories. Existing volume ownership must be checked explicitly. Do not run `down -v` on a pilot with data to preserve. Stop the service before taking a coordinated backup of all three volumes (including SQLite WAL); restoring only graph or only vault can violate publication consistency.

The private internal network `oria-memory-private` publishes no host ports and has no external route. Attach only the HQ backend bridge container to it through a separately reviewed Compose override. Browser code must never hold handles or reach Memex directly. The backend target is `http://memex:3000/mcp`; the health route is liveness only, not an auth/publication check. Resource limits are initial pilot limits, not measured capacity.

The reviewed gateway accepts signed handles without a legacy GATEWAY_TOKEN. The entrypoint removes any inherited legacy token and namespace configuration, and loads only the external signing key. The gateway default read_write permits narrowly scoped proposal handles. Give HQ only a read_only signed handle scoped to its exact `org:` project. Do not give HQ the signing secret. Generate handles using the operator helper below with short expiry; capture output directly into an external backend secret file, never a terminal transcript. Rotation/revocation is currently expiry or signing-key rotation; there is no per-handle revocation store. This image must include the signed-only authentication fix, which the acceptance harness checks with GATEWAY_TOKEN absent.

## Remaining acceptance in intended network

The operator helper only mints read_only handles, maximum one hour. It rejects terminal stdout; still ensure the orchestration shell redirects output so no tool transcript captures it. Run in a shell with tracing disabled, use a new protected output file, and inject that file into the HQ backend secret mechanism without displaying its contents:

```sh
umask 077
docker compose -f deploy/memex-pilot/compose.json exec -T memex \
  node --experimental-strip-types /app/pilot/mint-read-handle.mjs \
  hq-pilot org:pilot-a 900 > /outside/repo/new-hq-memex-read-handle
```

1. Run image native/FTS check and synthetic harness; record image ID and source-manifest hash.
2. Start pilot; confirm UID1000, rootfs read-only, volumes writable and no published ports.
3. Provision an expiring HQ read_only handle for a synthetic project; seed approved canaries only through explicit operator admission.
4. From HQ's backend container call its actual read bridge against Memex. Confirm project A canary is present, project B and expired/tampered handles denied, and read-only proposals denied. No credential output in evidence.
5. Restart Memex and verify published canaries survive; stop and backup the coordinated volumes. Verify unrelated runner networks cannot connect before widening pilot use.

Provider runners need no direct Memex network access for this bridge pilot. Do not install this service into the local development AgentMemory directory.

## Actual Linux image evidence and persistent probe

Root built image `sha256:23805a5b18f4dd3379eaf4f43c6f36c9aaf9deade53a74346fcff214270561d7` from source-manifest SHA256 `67b097bf05a54668ab804ec984d493d8b8ad1f1eebf1a6f3225ebf9ed79dc7d3`; the actual Linux acceptance harness passed on Node22.23.3. The first image lacked capability catalogs; the corrected snapshot and image include both exact fixture files. Root started the private pilot after this pass. These results do not yet prove HQ integration or persistence across restart.

`runtime-probe.mjs` runs as trusted operator code against the real gateway entrypoint at container-local port3000. It reads the mounted signing key in memory and prints only status, never credentials. It is intentionally outside the image: pipe it to Node without copying into the read-only filesystem. Default mode performs HTTP-only verification; explicit seed mode admits only the two exact synthetic canaries after guarded payload/provenance checks. It refuses ambiguous candidates, unrelated ID collisions and unexpected publication states instead of overwriting or repairing data.

```sh
# Explicitly seed synthetic operator-reviewed memories once (or safely verify existing exact rows).
docker compose -f deploy/memex-pilot/compose.json exec -T -e MODE=seed memex \
  node --experimental-strip-types --input-type=module < deploy/memex-pilot/runtime-probe.mjs
# Verify again after a controlled service restart to prove persistence.
docker compose -f deploy/memex-pilot/compose.json exec -T memex \
  node --experimental-strip-types --input-type=module < deploy/memex-pilot/runtime-probe.mjs
```

HQ mapping: workspace `pilot-a` uses namespace `org:workspace:pilot-a`, and `pilot-b` uses `org:workspace:pilot-b`. Canary IDs are `memex-pilot-canary-a-v1` and `memex-pilot-canary-b-v1`; their properties carry `status=verified`, `zone=human` and source `operator-review:synthetic-pilot`. These are synthetic operator-approved evidence, not real human-authored memories. Bind HQ to pilot-a with a handle whose namespace array contains exactly `org:workspace:pilot-a`; do not issue a multitenant HQ handle.

## Coordinated recovery drill

`recover-pilot.py` uses host Python3 and Docker only. It requires the fixed pilot source container to be stopped, checks the exact image/source manifest and three source volume names, and refuses any other running volume consumer. The calling controller must stop the original service and **restart it in a finally block even if the recovery script fails**. Do not use an unconditional shell command chain that skips restart on failure.

```sh
python3 deploy/memex-pilot/recover-pilot.py \
  --backup-root /outside/repo/private-backups \
  --run-id unique-recovery-001 \
  --source-manifest /path/to/frozen-snapshot/source-manifest.json \
  --probe deploy/memex-pilot/runtime-probe.mjs
```

The backup root must already exist with mode700. Each run creates a new directory, three coordinated tar archives with hashes, source manifest, safe runtime configuration, and a root-owned mode600 signing-key backup. A separate restore-key copy is owned by UID1000 mode400 under the private directory. These backups contain credentials and memory; preserve their private access controls. No keys enter logs.

Restore volumes and container names are unique and collision-checked; no existing data is overwritten or deleted. The clone runs the same image with no network or published ports, verifies canaries and access controls through the actual HTTP gateway, then stops. The script retains the stopped clone, restored volumes, private backup and JSON evidence even after failure. Retention/cleanup is a separate explicit operator decision. The source service is never started or stopped by this script; that responsibility stays with the calling controller. Syntax was checked locally; the actual VPS drill remains to be run by root.
