# Operator entry for a prepared, authorized job

`run_host_job.py --config /root/hq-operator/jobs/<launch-id>.json`

This is an explicit one-job Linux operator command, not an HTTP endpoint or queue daemon. It calls the existing `run_permission_job`; there is no second execution state machine.

The root-owned configuration has exactly three fields:

```json
{
  "lifecycleCommand": ["/usr/bin/docker", "exec", "-i", "hq-host-bridge", "node", "/workspace/hq/src/scripts/openhands-lifecycle.mjs", "/protected/job.json"],
  "jobRoot": "/var/lib/oria-hq/jobs/<launch-id>",
  "reviewSocket": "/run/oria-hq-control/<launch-id>/review.sock"
}
```

Names above are placeholders, not installed services. The lifecycle process must already have its authorized HQ environment and protected canonical job configuration. Never put secrets or agent-supplied command arguments in this file. The command executable, configuration and parent directories must be real absolute, root-owned paths without group/world write. Resolve executable symlinks explicitly before provisioning. Only the root operator can run this entry.

Prerequisites: valid HQ launch claim in `claimed` state, exact authorized dossier in `jobRoot/dossier.json`, isolated checkout and results writable by UID10001, host-owned IPC directory, protected control directory outside the job. Job and control directory basenames must equal the canonical launch UUID. Existing socket is an uncertain prior attempt and is refused, never removed automatically.

The command reads image/deadline/identities from the canonical lifecycle response, then the worker rereads them before dispatch. It does not create a claim, prepare a source checkout, approve a tool, provision accounts, select a network profile or perform a deployment. Current container creation remains network-none and credential-free, so this entry cannot yet perform a real Claude coding mission.

Exit 0 means the process reached `execution_finished`, including a nonzero container exit. Inspect the returned `process.exitCode` and independent evidence; it is NOT mission success. Exit3 means no confirmed execution completion; exit2 reports reconciliation required. No automatic retry. Existing resources remain for operator inspection under the worker/supervisor policy.

Validation 2026-09-30: four entry tests pass on VPS, including real POSIX ownership/mode checks. These tests qualify input/dispatch binding, not a live authorized execution through this CLI. Existing assembled worker/control/DB qualification is documented separately in REVIEW-SERVICE-RESULTS.md. Next: exercise this exact entry against the disposable canonical fixture, then provision its protected host bridge and source preparation workflow before enabling real execution.

## Actual entry qualification

Subsequently ran `qualify_hq_postgrest.py --host-entry --live-memex` on VPS, exit0. The harness invokes this exact CLI as a subprocess using a root-protected configuration. Actual canonical HQ reservation, signed Memex capture, PostgreSQL/PostgREST, Docker worker/supervisor and OpenHands Claude adapter participate.

The runner verifies the authorized dossier hash and exact Git commit, then the adapter fails with `Authentication required`. Outcome: `execution_finished`, process exitCode1, stopped=true, deadlineExceeded=false, independentValidationPassed=false. Observed process duration10.07s is a missing-authentication failure-path measurement, not successful task performance.

A second CLI invocation refuses the existing review socket/prior attempt; the canonical container ID remains unchanged. PostgreSQL restart retains six expected ledger events. Qualification cleanup removes its disposable container/database; the operator entry itself does not delete retained work. No provider account, model request, public ports or production database used. The runner image is pinned to sha256:3d8c97af6b8f1e6979596709f659124ca8f0319d5949e0f6f06f9c0287a7e11e.

Next: provision a protected canonical dossier/checkout preparation path and provider profile. Browser launch authorization and genuine provider mission remain unqualified. This command requires an already-prepared job and cannot serve as a complete HQ orchestrator by itself.

## Canonical preparation

`prepare_host_job.prepare_host_job(command=..., source=..., jobs_root=..., control_root=...)` now prepares the exact canonical submission using the lifecycle `next:prepare` operation. This operation requires a still-claimed launch and valid, unexpired launch authority; ordinary observation cannot export a dossier through this new operation after expiry. It returns no new authorization and performs no database mutation.

The host checks protected root-owned source/runtime paths, dossier integrity/workspace/mission/commit binding and local commit availability before creating anything. It reserves launch-specific job/control directories exclusively, creates the detached isolated clone using existing workspace preparation, transfers only checkout/results ownership to UID10001 (without following symlinks), and writes a read-only dossier plus root-only operator configuration. Failures retain partial directories for reconciliation. No automatic retries or agent execution during preparation.

Verified `qualify_hq_postgrest.py --prepare-host --live-memex` on VPS: canonical preparation, repeat refusal, source HEAD unchanged, actual operator entry, exact commit/dossier runner verification, authentication-required process exit1, second invocation refused, six ledger events preserved after database restart. Process duration8.465s again measures the missing-authentication failure path. Twelve HQ launch/lifecycle tests pass, including refusal of expired, foreign and already-started preparation. The source remains a trusted operator-controlled repository; this function is not a hostile-repository sanitizer.

Still missing: a provisioned production host bridge/source registry, UI launch dispatch, provider profile/account consent and a successful independently reviewed coding mission. Preparation is currently a callable host function, not a new public endpoint or automatically running service.

## Project-bound preparation command

The integrated Memex profile now has a Linux root operator entry:

```sh
python3 project_sources.py --config /root/hq-operator/preparation.json
```

Example configuration (paths are placeholders, not provisioned production services):

```json
{
  "lifecycleCommand": ["/usr/bin/docker", "exec", "-i", "hq-host-bridge", "node", "/workspace/hq/src/scripts/openhands-lifecycle.mjs", "/protected/job.json"],
  "registryFile": "/root/hq-operator/project-sources.json",
  "jobsRoot": "/var/lib/oria-hq/jobs",
  "controlRoot": "/run/oria-hq-control"
}
```

The private source registry schema is `{ "version": 1, "entries": [...] }`. Each entry contains exactly `workspaceId`, `projectId`, `runnerId`, and an absolute `sourceRoot`. Bindings are unique by the three identities; missing or ambiguous bindings fail closed. The project comes from the canonical v2 Memex dossier, never from browser path input. Legacy v1 dossiers are deliberately unsupported by this integrated profile. The registry contains no provider credentials or memory handles and does not replace the separate Memex connection registry.

Configuration and all parent paths must be real, root-owned and non-writable by group/others. Validate and resolve the executable path before provisioning. The CLI validates paths and command structure before invoking the lifecycle subprocess. Source selection is followed by another canonical authority read; payload changes invalidate preparation. Existing job/control directories require reconciliation, not automatic reuse.

Exit0 returns `state: prepared`, the protected `operatorConfig` path, launch ID and commit, with `executionRequested: false`. It does not launch Docker or an agent. Pass the returned operator configuration to `run_host_job.py` only through the authorized host workflow. Exit2 returns `preparation_not_confirmed`, with automaticRetry false; partial work may remain. Error output omits configuration contents.

Qualification on 2026-09-30: `qualify_hq_postgrest.py --project-source` invokes the actual preparation CLI followed by the actual execution CLI. The authorized Git commit and dossier reach OpenHands; duplicate preparation/execution are refused and source HEAD is unchanged. Signed disposable Memex supplies two reads; six ledger events survive PostgreSQL restart. The Claude adapter stops with authentication required (process exit1, 8.215s); no model is called. This duration is not successful mission latency. No public ports or production database are used; owner authentication and RLS are not qualified by this fixture. All five source-registry tests pass on Linux, including rejection of writable configuration before lifecycle effects. The prior full local runner run passed 78 tests with four platform skips; the subsequently added Linux test is separately validated on VPS.

This closes the callable-only preparation gap. A provisioned persistent host bridge, actual browser-to-host dispatch, provider profile/consent, and an independently reviewed coding mission remain unfinished.
