# Review service and Memex integration qualification

Verified on the isolated VPS qualification infrastructure, 2026-09-30.

## Reproduce

```sh
python3 /opt/oria-openhands-qualification/openhands-runner/qualify_hq_postgrest.py --review-service
python3 /opt/oria-openhands-qualification/openhands-runner/qualify_hq_postgrest.py --review-service --live-memex
```

Both commands exited 0. The harness uses disposable PostgreSQL/PostgREST and actual HQ modules mounted read-only. It removes its containers and volume in `finally`; no qualification containers remained after these runs.

## Evidence

- Launch progresses through canonical lifecycle transitions to a running synthetic session.
- Actual review service rejects foreign owner, altered request hash and browser-supplied raw request. No decision exists before the valid selection.
- Valid selection passes canonical launch/session admission and persists through the real decision store.
- Two concurrent lifecycle CLI processes attempt consumption: exactly one gets `selected/allow`, the other gets `cancelled`.
- After execution completion, consumption is denied; subsequent storage consumption cannot reuse the grant.
- PostgreSQL restart preserves all six expected mission ledger events.
- Tool argument marker is absent from persisted decision/consumption rows.
- With live Memex enabled, two HTTP reads capture the signed, project-scoped context. Foreign content is excluded. A later source correction does not silently modify the authorized mission snapshot, including after database restart. Verification uses the stored capture and makes zero additional memory reads.

## Boundaries

The runtime container identity/session and pending-request source are synthetic. Owner context is supplied by the qualification harness; no browser authentication, RLS, private control socket, worker notification or ACP-origin request is qualified by this scenario. Database service role bypasses RLS by design in this disposable fixture. No provider/model, public ports, production database, production memory or deployment involved.

This is evidence for assembled HQ review/admission/durable-consumption and Memex snapshot behavior, not a completed autonomous development mission. Next qualification must assemble authenticated HTTP review with the host pending registry/control channel and ACP callback.

## Real private control channel extension

`python3 /opt/oria-openhands-qualification/openhands-runner/qualify_hq_postgrest.py --review-control --live-memex` exited 0.

This variant publishes the synthetic request through the actual Python `PendingPermissions` registry and `serve_control` Unix socket. Actual HQ `createOpenHandsToolInbox` lists and reloads it, verifies admission, persists the exact decision, and notifies the Python registry. The host observes that notification. The same two concurrent lifecycle consumers then yield exactly one grant; Memex snapshot and database restart checks still pass.

The Node process runs as UID 1000, matching the mode-0600 socket owner. The first run with root and dropped capabilities failed to access the socket, correctly respecting filesystem permissions. Switching to UID 1000 exposed inaccessible qualification sources; the harness now creates an explicit read-only copy of just its script and synthetic JSON fixture. Socket permissions were not widened. Host helper processes and temporary directories are cleaned even on failure.

Remaining boundaries: authenticated HTTP route and ACP callback are still outside this run. Caller identity and runtime identity remain synthetic. The writable control mount includes test-only readiness files; this is a qualification arrangement, not a production deployment manifest. A notification is only a hint, never a durable grant.

## Host permission handler extension

`python3 /opt/oria-openhands-qualification/openhands-runner/qualify_hq_postgrest.py --review-host --live-memex` exited 0.

This extension sends an ACP-shaped synthetic request over the actual agent Unix socket to `host_handler`. The actual handler registers the session through the HQ lifecycle CLI, derives the host-bound request and expiry, publishes it in the pending registry, waits for inbox notification, and consumes the durable decision through `consume_tool_decision`. The socket client receives exactly `selected/allow`. Two later concurrent CLI consumers both receive `cancelled`. The canonical launch is then completed and all six ledger rows survive database restart. Signed Memex snapshot checks pass in the same run.

The first run exposed a fixture-file publication race; publishing by write-to-temporary-file then rename fixed it. This is a harness correction, not a production defect claim.

Still unqualified: actual provider-origin ACP callback, authenticated HTTP/session path, complete `run_permission_job` with human review and a real autonomous coding mission. The socket client is synthetic; this does not establish model execution or browser authentication. No production deployment occurred.
