# Serial canonical HQ consumer

The bridge command explicitly uses `docker exec --user 0:0` for the private discovery/lifecycle CLI. These scripts require root to inspect their root-owned, mode0600 configuration. The source image defaults to UID1000, so inheriting the image user would reject discovery. This override applies only to private operator commands; it does not change the web application's user or grant agents access to the bridge. Do not mount the Docker socket inside the bridge.

`python3 consume_pending.py --config /etc/oria-hq/consumer.json` processes one bounded discovery page. Add `--watch` for continuous operation: subsequent pages wait one second, a completed scan waits five seconds before starting again. No model participates in discovery or dispatch bookkeeping.

The command runs on the Linux host as root. Its configuration and ancestors must be protected root-owned paths. `consumer.example.json` illustrates paths only; it is not a provisioned deployment. The bridge container must mount hostConfigRoot read-only at bridgeConfigRoot, carry the current HQ scripts/dependencies, and inherit its separately protected Supabase environment. Agents must never receive this mount or the bridge credentials. The example has no secrets. The profile uses the schema documented by HQ's OPENHANDS_HOST_DISCOVERY.md; it is a direct child of hostConfigRoot. The project source registry is separately protected.

The consumer configuration accepts one optional key, `providerExecution`, with the
same four fields and the same host-path rules as the operator entry (see
`HOST-ENTRY.md`). `consumer.example.json` deliberately omits it: without it the
consumer refuses every profile-bearing launch before allocating anything, which is
the installed behavior. With it, a launch whose canonical `providerProfile` matches
the approved identity and digest and whose protected policy still verifies is
carried into preparation and into the worker, which repeats both checks after its
own canonical reread. Any other profile is refused before a per-launch directory
exists. The authorization is written only into the root-only operator configuration;
it never reaches the mission lifecycle file or the dossier.

For each discovered launch, the consumer exclusively creates a persistent configuration directory named by its canonical UUID. It writes a root-only lifecycle configuration and uses the existing source selector, canonical preparation, operator entry, permission worker and dispatch CAS. The discovered payload hash must still match on preparation. No source path or executable comes from a mission. A partial attempt is retained, never deleted or replayed automatically. A filesystem lock permits one consumer per hostConfigRoot; canonical CAS remains the cross-worker execution boundary.

One job runs at a time. The consumer halts on an unavailable discovery, uncertain attempt or failed process instead of launching the rest of a potentially broken batch. Exit0 means the requested scan completed or a graceful stop was handled, not independent mission validation. Exit3 means a job did not finish with process exit0; exit2 means consumer/configuration/reconciliation failure. Stdout reports bounded identity/outcome data; no configuration arguments or credentials are printed. Inspect canonical HQ state and retained files before recovery; restarting the process is not permission to delete attempt directories.

SIGTERM/SIGINT stop acquisition and let the current worker finish. Existing per-job deadlines remain responsible for stopping containers. This is not proof of recovery from SIGKILL, kernel failure or a forcibly killed service. The systemd unit is a deployment candidate, not installed/enabled. It has no automatic restart and allows time for the bounded in-flight job to stop. Forced shutdown still requires reconciliation of the deterministic container identity. Review the real bridge mounts and write paths before installation.

Qualification uses `qualify_hq_postgrest.py --host-consumer`: actual disposable HQ/PostgREST/Memex discovery, protected mapped per-job config, source preparation and Docker worker. The Claude adapter lacks authentication and exits1; the consumer must stop with exit3, not report a successful coding mission. This fixture does not prove a live provider mission, production owner authentication/RLS, sustained watch operation or recovery after power loss. Linux tests separately exercise one-confirmation preparation, duplicate reference refusal, nonadvancing cursors, failure halting the batch, and graceful stop before the next job.

Pending: provision a real protected bridge/profile/source mapping, qualify watch under real service lifecycle and interruptions, obtain provider consent and implement its network/auth profile, then run a real coding mission with independent review. No production service is enabled by these files.

Observed 2026-09-30: `--host-consumer` qualification completed with exit0 for the harness. The actual consumer returned exit3 as required after the Claude adapter's authentication-required process exit1 (9.464 seconds, not successful-task latency). Exact dossier/commit reached the runner; source HEAD stayed unchanged; repeated preparation/execution were refused; six canonical ledger events survived database restart. A first harness run failed because its repeat-preparation assertion expected a filesystem refusal after the consumer had already completed execution; the assertion now verifies canonical `execution_finished` refusal instead. No product permission was relaxed. Disposable containers/volumes were removed and cleanup listings were empty. Runner suite: 84 tests, seven Windows platform skips; five consumer tests passed on Linux. Continuous real-service operation and power-loss recovery remain unqualified.

## systemd qualification and restrictive umask correction

`qualify_hq_postgrest.py --consumer-service` runs a temporary uniquely named systemd service with the candidate's User=root, UMask=0077, Restart=no, KillMode=mixed, TimeoutStopSec=2100, NoNewPrivileges, PrivateTmp, ProtectSystem=strict and bounded writable paths substituted to disposable directories. It uses actual canonical discovery/preparation/dispatch and removes the transient service afterward; the production unit is not installed.

The first service run exposed a real preparation bug: creation modes were masked by UMask=0077, making the root-owned dossier unreadable to UID10001. `prepare_host_job.py` now explicitly sets only the intended shared permissions: job/control/IPC directories 0755, dossier 0444. Operator config remains 0600, results remain 0700 owned by UID10001, and private per-launch bridge config directories remain 0700. A Linux regression test verifies these exact modes under umask0077.

The repeated real qualification passed: the adapter reached authentication-required (process exit1, 8.416s); systemd exposed failure with ExecMainStatus3 and no automatic restart. Restarting the same service discovered no pending job and produced no second execution report. It stayed active at idle for at least seven seconds, rejected a simultaneous consumer on the same root, and stopped gracefully at idle with exit0. Database restart again retained six ledger rows. This proves that bounded failure/restart/idle-stop scenario, not sustained load, an in-flight hard kill, reboot recovery, provider cancellation or a successful model mission. Timing is failure-path evidence only.
