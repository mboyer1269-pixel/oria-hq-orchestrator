# One host execution deadline

Implemented locally and qualified on the VPS, 2026-09-30. The installed consumer remains unchanged and provider-profile execution remains disabled.

After the canonical `claimed → creation_requested` compare-and-swap succeeds, dispatch creates one monotonic deadline. Container creation and subsequent startup work consume that same budget. If creation exhausts it, the created container is retained for reconciliation without a start request. Dispatch passes the original absolute deadline to the permission worker and supervisor; no stage refreshes it.

The permission worker verifies canonical `start_requested` state, exact container identity and unexpired launch authority before opening the channel, then rereads them after channel setup. Channel requests receive a wall-clock expiry capped by both remaining monotonic budget and canonical start time. A timed-out channel setup is cancelled. Unknown or changed state refuses execution and retains reconciliation semantics; no automatic retry is introduced. This is a specific pre-start check, not a claim that distributed cancellation can be atomic with Docker startup.

The supervisor validates and caps the absolute deadline against its nominal budget. It deducts time spent inspecting Docker before invoking start. An expired budget never starts a container. Process termination and cleanup still have their explicit grace/observation costs; those are not additional model execution allowance. A still-running provider request's remote cancellation is not proven by a local stop.

The per-launch provider gateway is now wired into the permission worker behind a trusted, explicit `gateway_root` parameter. Creation occurs only after canonical acquisition; gateway creation, container creation and supervision share the same deadline. The installed operator configuration does not supply this parameter, so provider execution remains disabled there; an operator who adds the explicit `providerExecution` object now supplies it without a separate budget, because the gateway keeps receiving the same shared deadline as container creation and supervision. Store acquisition and cleanup ordering are tested with mocks; an actual HQ/PostgREST provider-profile mission remains to be qualified.

A real VPS probe delayed Docker startup by two seconds, then killed the host supervisor with SIGKILL. With a six-second shared budget, the proxy exited 124 and refused socket connections. Total harness observation took 7.618 seconds including setup and observation overhead, not a latency benchmark. The journal still said `ready`: reconciliation must inspect actual resources. The harness removed its resources. No model requests were sent. Evidence: `../openhands-provider-proxy/gateway-shared-deadline-evidence.json`.

## Validation

- Latest Linux follow-up: 30 focused worker/dispatch/supervisor/gateway tests pass on the VPS. Gateway network creation, container creation and startup calls now receive the remaining shared budget. If container creation consumes that budget, cleanup removes the known resources without issuing a start. Two added regression cases exercise these boundaries. Cleanup retains its separate bounded allowance.
- This follow-up ran from `/opt/oria-openhands-qualification/gateway-worker-check`, initially unpacked from release `3013cf07aaa7fe667aa1c7ddc077cdb65fb9c1e84b0c09bdf5431d260261df72` then overlaid with the corrected gateway and its tests. It is a qualification directory, not an installed release.

- Twenty focused tests passed on both Windows and actual Linux, covering slow creation, spent inspection time, absolute-deadline capping, and cancellation/authorization expiry during channel setup.
- Latest full host suite: 92 passed, 19 Windows platform-dependent skips, no failures. The latest focused worker/deadline suite passed 21 tests on Windows; the earlier 20-test version also passed on Linux. The staged release below predates the latest gateway wiring.
- Real Docker probe: an expired deadline left the container `created`; a nominal10-second budget with only1second remaining stopped a sleep workload after1.146seconds, exit137, deadlineExceeded=true, containerStopped=true. The probe container was then removed. See `shared-deadline-evidence.json` and `qualify_shared_deadline.py`.
- No provider/account/model, HQ source modification, active service update, commit or push.

The staged host package contains22files, release `ffad9f3b9639779df88c5d3d85bfa008d3b934c79f3eaa51f8749281d482ebfc`, archive SHA256 `e1ceb7dc5fa1a26ee4dc691ba70d1e039c4b8b3916c61dabb8de2a1268e71c99`. It was used only under `/opt/oria-openhands-qualification/shared-deadline`.
# Pre-start inspection correction — 2026-09-30

Source review found that provider identity inspection in `container_job.py` and
the supervisor's two pre-start inspections still used Docker's independent
10-second timeout. Each now receives the smaller of that timeout and the
remaining absolute mission budget. An exhausted budget refuses the next call;
an inspection timeout propagates without starting or retrying the job.
Post-start cleanup retains its separate existing policy.

Local Windows validation: 124 discovered tests, 102 passed and 22 platform skips.
New supervisor tests cover decreasing inspection budgets and a daemon timeout
with no start or retry. This is deterministic regression evidence, not a VPS
latency benchmark. The source correction has not been installed in the active
host runtime, and does not enable authenticated provider execution.

Linux follow-up: the same source was copied to the separate VPS directory
`/opt/oria-openhands-qualification/hq-linux-deadline-c9f825c1eb3e4a83b4def85a61fec2c1`.
`python3 -m unittest discover -p "test_*.py"` exited 0: 124 tests passed,
zero skipped. These unit tests include mocks; this does not establish a real
Docker-daemon latency guarantee or an authenticated mission result.

The explicit 23-file host release was built there successfully:
release `b6472aaf32257f1355ee4264d7cebbb19bcded1f2e894ad95cc7394115c10ae9`,
archive SHA256 `d825c96266de649410b99065dd81ff3407d24526aa75874b86b47137f31b53c2`.
It remains an inactive qualification artifact; the installed consumer and HQ
services were not replaced or activated.
