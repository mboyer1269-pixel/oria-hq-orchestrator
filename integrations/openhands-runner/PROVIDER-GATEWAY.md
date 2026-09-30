# Per-launch provider gateway lifecycle

Local host helper `provider_gateway.py`, explicitly included in the host release package. The live worker still refuses provider profiles; this helper is exercised by the isolated qualification harness, not automatically by production missions.

Before creating resources it validates the protected policy, runtime image, all artifact hashes, root ownership, mount syntax and the Linux Unix-socket path limit. It snapshots the exact verified configuration and relay into a new exclusive launch directory. The proxy explicitly mounts those snapshots, so the running config does not silently come from unrelated image defaults. Only a pinned proxy image is used.

Each canonical launch UUID gets a deterministic name, new egress network, non-root proxy container, private socket and local lifecycle journal. The helper returns the socket and relay paths only after a real denied-request readiness check. It publishes no port and accesses no account credentials. The caller must separately hold canonical launch authorization; invoking this helper is not proof of that authorization.

Normal completion, body exceptions and startup errors clean up only full resource IDs obtained by this invocation. Uncertain creates retain a reconciliation state with deterministic names; cleanup failure cannot be reported as closed. Existing launch directories are never automatically reused. Journals and policy snapshots remain for inspection. Journal replacement is atomic and fsynced to preserve the preceding record if a write is interrupted.

The container now runs GNU `timeout` independently of the host helper: the validated canonical mission timeout (1–1800 integer seconds) plus 15 seconds startup allowance, followed by a maximum five-second termination grace. Docker restart policy is explicitly `no`. This bounds proxy availability after host-helper loss without relying on Python `finally`. It does not automatically remove the stopped container/network or reconcile HQ mission state. A future shared mission deadline must account for time spent starting the gateway and job; do not treat the allowance as permission to extend the mission budget. SIGKILL recovery still requires live Docker inspection because the journal can remain `ready` after expiry.

## Evidence — 2026-09-30

Six Linux tests passed: success cleanup, deliberate body failure, ambiguous create without automatic start/deletion, cleanup failure, policy rejection before resources, oversized socket path rejection before resources. Full host suite before the sixth added case: 85 passed, 14 Windows-platform skips; the added case passed in the six-test Linux run.

Actual Docker qualification is in `../openhands-provider-proxy/qualify_gateway.py` and `gateway-evidence.json`. Launch `a4c3d210-bd34-462d-8f4a-fea0287efc77` passed the four-host TLS/deny/direct-connection/loopback-relay probe through this helper. Launch `eba0d1cb-1c34-4b20-8c09-241c40b9394b` deliberately failed after gateway startup. Both journals ended `closed`; successful full Docker inventories confirmed their container and network IDs absent. A separate label inventory confirmed no remaining gateway resources, including the first failed long-path attempt.

The long-path defect was observed in an actual initial run and fixed with a pre-effect length check plus a shorter qualification root. No active application or account was changed. No model was called, and no commit/push or active runtime update was made.

Next integrate an enforced lifetime/recovery strategy, actual mission-container relay startup/environment and credential lifecycle. Keep the existing unsupported-provider refusal until these are proven with the canonical mission authority, tool review and provider connection.

## Container-enforced lifetime qualification

`../openhands-provider-proxy/gateway-crash-evidence.json` records launch `9372c4cf-329e-4d00-96f2-b649417ffb17`. The test killed the live Python owner with SIGKILL (exit -9). With a one-second synthetic mission deadline and 15-second allowance, the proxy independently exited 124; total observation from setup was 17.562 seconds. The socket no longer accepted connections while the journal remained `ready`. The harness subsequently removed retained Docker resources; this cleanup was not automatic production recovery. No account or model request was involved.

The unchanged full network probe and deliberate-exception cleanup were rerun with the deadline wrapper; both passed (`gateway-deadline-lifecycle-evidence.json`). Seven Linux gateway tests passed. Full current Windows host suite: 85 passed, 16 platform-dependent skips, no failures. GNU timeout9.1 availability was verified in the exact pinned proxy image. No active host installation or production service was updated.
