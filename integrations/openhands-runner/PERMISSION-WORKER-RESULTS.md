# Permission worker qualification

## Host probe through actual HQ authority

`--probe-permission` subsequently passed on the VPS. While the actual runner
container was running, a synthetic host client sent a request over its Unix
socket. The host handler registered the session through the real HQ lifecycle
CLI and called the real HQ permission consumption service. No decision existed,
so HQ returned cancelled. The persisted session and running state were checked.
The dispatcher then recorded completion from running, retained across database
restart. This also exercised the worker's canonical image/deadline preflight.

The request originated from the test client, not Claude. This proves the denial
path and running-to-finished transition, not authenticated owner approval or
successful provider tool execution. The runner still exited with Authentication
required; no model was called. Disposable cleanup completed.

On 2026-09-30, `qualify_hq_postgrest.py --permission-worker` passed on the VPS.
It combines real HQ lifecycle services, PostgreSQL/PostgREST, the host permission
worker, a private socket and the permission-capable runner image:

`sha256:ef1d19494a2644b80a69cc0d9a4a66fdc8eee8972bc7ba4a69c877242b84c9e6`

The exact canonical dossier and Git commit reached the runner. Its real Claude
adapter failed with `Authentication required`, exit 1 after 10.131 seconds.
The worker recorded execution_finished without declaring independent validation.
After PostgreSQL restart the recorded outcome remained available; six ledger
rows were verified. Temporary resources were cleaned up.

The socket opened before supervised startup. No tool request was made before
the authentication failure, so this does **not** prove real HQ approval through
the socket. Earlier socket tests used synthetic decision handlers. Authenticated
owner review, provider execution, RLS and successful coding remain unqualified.
No production database, public port or provider account was used. Active HQ and
Memex services were not replaced. Runtime duration is a failure-path measurement,
not a coding performance benchmark.
