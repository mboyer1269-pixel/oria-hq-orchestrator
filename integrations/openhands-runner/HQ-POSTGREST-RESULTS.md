# HQ durable store qualification — 2026-09-30

`qualify_hq_postgrest.py` and `qualify_hq_postgrest.mjs` passed on the VPS.
The test uses the actual HQ TypeScript development, snapshot, attachment,
authorization, reservation and audit stores through the Supabase JS client,
PostgREST v13.0.0 and isolated PostgreSQL.

Verified:

- Concurrent snapshot insertion returns one canonical capture.
- Concurrent mission attachment has one successful CAS update.
- Preparation and confirmation persist a memory-bearing dossier and audited receipt.
- Three ledger rows exist: snapshot, authorization, reservation.
- After a PostgreSQL restart and a new Node process, repeating confirmation returns
  `already_reserved`; the same three rows remain and the capture is unchanged.
- Foreign-workspace mission lookup returns no result.
- Temporary containers and the dedicated database volume are removed; a subsequent
  label-filtered inventory found none remaining.

Environment: PostgreSQL image ID
`sha256:b0f9560a2de083e2cc7382e75f808c7381a32852a7ec49117deedb300e552b24`;
PostgREST digest
`sha256:c53043d2c9bdb29c28e7e6d02175320af11495cdea5439f44009c06efe6625fa`.
The Node validation image supplies dependencies; current HQ `src` is mounted read-only.
Containers share an isolated network namespace, with no published ports. The Node
test process uses UID 0 with all capabilities dropped and read-only mounts because
the qualification source directory is owner-only. This does not qualify the agent
runtime's user isolation.

Scope limitations: selected real schema definitions/migrations are applied (base
action ledger, 0001, 0002, 0020), not the full production migration history. A tiny
local proxy reproduces `/rest/v1` routing and removes synthetic credentials;
PostgREST executes under a test service role with BYPASSRLS, matching the stores'
privileged access pattern. This does **not** validate Supabase Auth, production RLS,
ledger hash-chain migrations, browser behavior, deployed configuration, real Memex
access or a provider mission. Memex signed HTTP was qualified separately in HQ's
`openhands-memory-http-lifecycle.test.mjs`.

No production database, model, production credentials or application deployment was used.

Configuration reference: [PostgREST v13 configuration](https://docs.postgrest.org/en/v13/references/configuration.html).
# Combined real Memex HTTP and durable HQ lifecycle — 2026-09-30

`python3 qualify_hq_postgrest.py --live-memex` exits0 on the VPS. It now uses the
current, file-verified HQ candidate image by immutable ID. A separate disposable
Memex container starts the real graph, signed handles and HTTP MCP server from
image `sha256:04c47d5b4572fed80ea1a04a93bf6a525f8dcfa2567897e80bc0eae108ffd367`.
No production volumes or credentials are mounted. Fixture and control endpoints
are loopback-only in the disposable network-none namespace; never expose or deploy
`qualify_memex_service.mjs` as an application service.

Observed complete service chain: real Memex signed context capture -> actual HQ
attachment/snapshot stores -> actual Supabase JS/PostgREST/PostgreSQL -> actual
HQ preparation/confirmation -> database restart -> fresh-process confirmation
replay. The approved context excludes the foreign project and remains unchanged
after the live Memex graph is demonstrably modified. The persisted ledger payload
equals the mission snapshot. Exactly three ledger rows remain after restart and
replay returns already_reserved. Foreign workspace mission lookup returns null.

HQ memory transport calls: two during capture; zero during confirmation/restart
replay. The independent direct probe proving the graph changed is separate and
not included in the HQ transport count. These are call counts, not latency or
token savings benchmarks.

Synthetic identities/data only. This does not qualify Supabase owner login/RLS,
the browser UI, production migrations, autonomous coding or provider cancellation.
The live-Memex mode uses a sequential capture to measure calls; concurrent CAS
behavior is covered by the existing non-live mode, not newly asserted here.
Test containers use UID0/cap-drop for read-only harness mounts; this does not
qualify the actual agent sandbox. Cleanup label inventories are empty after run.

# Local lifecycle bridge qualification — 2026-09-30

Valid-input follow-up: `--valid-dossier --live-memex` passed. HQ reread the
canonical submission from its ledger; the host delivered it without modifying
its payload hash, using an independently cloned synthetic Git checkout at the
exact authorized commit. The actual runner wrote started.json with that same
hash/commit and outcome.json with execution_error. The actual process exited 1
after 8.366 seconds, and HQ retained the result through database restart.
No provider credentials or network were mounted. This proves valid dossier
delivery plus failure reporting, not successful inference, coding or review.
Follow-up diagnostic run identified the exception as SDK ConversationRunError
with `Authentication required`, after dossier and commit checks. It exited 1
after 8.574 seconds. No conversation logs were uploaded or sent to a provider.
The qualifier prints only a bounded error tail from this credential-free,
synthetic fixture; do not apply that diagnostic output to production logs.

Follow-up: `--docker-job --live-memex` now passed with the actual host dispatcher,
Python-to-HQ CLI transport, Docker creation and supervisor in one chain.
The container ID and exit code 1 persisted through PostgreSQL restart; replay
was rejected by the canonical lifecycle service. Supervision took 0.438 seconds
for this deliberately invalid-dossier rejection, not a coding task benchmark.
No model or provider credentials; no production database; no public ports.
The test injects `{}` as the runner dossier intentionally, so it proves failure
recording and process lifecycle, NOT approved dossier delivery or autonomous work.
The temporary container, database, and volume were removed by the harness.
Owner authentication, RLS, valid mission execution, live worker provisioning and
independent review still require qualification.

`qualify_hq_postgrest.py --lifecycle --live-memex` passed on the VPS.
Actual HQ stores, PostgreSQL/PostgREST, signed disposable Memex HTTP capture,
and four separate executions of the new local lifecycle CLI were used.
Canonical launch authorization and claim preceded transitions. Replay was
rejected; after database restart, execution_finished and the same container ID
remained durable, with mission status still draft (no false validation).
Four ledger rows persisted. Memex capture used two HTTP calls; verification
needed no additional memory lookup. No production data, published ports or model.

The container identity/process result in THIS combined test are synthetic.
Docker creation/supervision was qualified separately; an actual combined Docker
job, authenticated owner admission, RLS and a real model mission remain unproven.
Latest launch/lifecycle/CLI files were mounted read-only over the pinned test HQ
image; this is not a new deployment image. All temporary containers/volume were
cleaned by the harness. The first run incorrectly expected preparation replay
after launch; the service correctly returned ineligible_mission, and the test
now checks this plus the persisted execution state explicitly.
