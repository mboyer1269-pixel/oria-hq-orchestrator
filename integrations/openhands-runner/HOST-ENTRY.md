# Operator entry for a prepared, authorized job

`run_host_job.py --config /root/hq-operator/jobs/<launch-id>.json`

This is an explicit one-job Linux operator command, not an HTTP endpoint or queue daemon. It calls the existing `run_permission_job`; there is no second execution state machine.

The root-owned configuration has exactly three required fields:

```json
{
  "lifecycleCommand": ["/usr/bin/docker", "exec", "-i", "hq-host-bridge", "node", "/workspace/hq/src/scripts/openhands-lifecycle.mjs", "/protected/job.json"],
  "jobRoot": "/var/lib/oria-hq/jobs/<launch-id>",
  "reviewSocket": "/run/oria-hq-control/<launch-id>/review.sock"
}
```

One optional fourth field, `providerExecution`, is the only way this entry can
reach the worker's provider gateway path. Omitting it keeps the offline baseline
unchanged: no gateway root is passed and a profile-bearing mission is refused
exactly as before. When present it has exactly these four keys and no other:

```json
{
  "providerExecution": {
    "profileId": "claude-subscription-v1",
    "policySha256": "<sha256 of the approved <policyRoot>/<profileId>/policy.json>",
    "policyRoot": "/etc/oria-hq/provider-policies",
    "gatewayRoot": "/var/lib/oria-hq/provider-gateways"
  }
}
```

The authorization names the whole approved execution: which profile, which exact
policy bytes, which protected registry those bytes are read from, and which
gateway root. `policyRoot` and `gatewayRoot` must each be a real, root-owned,
non group/world writable directory; they must differ from each other and share no
subtree with `jobRoot` or the control directory. They are host paths: neither
appears in the dossier, the browser payload or the canonical mission record.

The operator entry passes the authorization together with both roots to
`run_permission_job`, which rereads canonical authority and refuses unless the
mission's own `providerProfile` has exactly the approved identity and digest and
the effective roots are the authorized ones. Provider execution requires the
authorization: a gateway root without it, an authorization without a gateway
root, or a disagreeing root is refused as `invalid_provider_policy` before any
socket, Docker effect or canonical transition. `--gateway-root` remains an
inspection-only flag; no gateway path from argv can reach execution.

This field enables the already-qualified gateway lifecycle for an explicitly
approved policy. It does not authenticate the CLI, mount any account credential,
qualify tool review or prove a real provider mission.

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

## Reconciling an interrupted launch

`python3 reconcile_launch.py --config <operator.json> [--gateway-root <root>]`

Root operator command for a launch whose host process died. It never dispatches
and never relaunches. It reads canonical authority and the observed Docker state,
then applies at most one canonical transition per observation, bounded to two
passes:

| Canonical state | Observed container | Recorded |
|---|---|---|
| `execution_finished`, `cancelled`, `succeeded`, `failed` | any | nothing; the retained evidence is read back |
| `claimed` | any | nothing; no effect exists yet |
| `creation_requested` | absent | `cancelled`, `interrupted_before_start` |
| `creation_requested` | created | `container_created`, then closed on the next pass |
| `container_created` | absent, created, dead | `cancelled`, `interrupted_before_start` |
| `start_requested`, `running` | exited | `execution_finished` with the observed exit code |
| `start_requested`, `running` | absent, dead | `cancelled`, `result_unrecoverable` |
| any stage | running, paused, restarting, removing | nothing; reason and next action returned |
| any stage | identity mismatch or unreadable | nothing; reason and next action returned |

A container is only this launch's if its name, `oria.launch-id` and
`oria.purpose` labels and pinned image all match **and its id equals the one the
claim records**. A replacement container carrying the same name, labels and image
is a different container: its state never justifies closing or releasing
anything, and the launch stays open with `container_identity_mismatch`. Past
`creation_requested` a claim always holds an identity, so a container the claim
never bound is refused as well. Retained `results/started.json` must carry this
launch's payload hash and commit; foreign or unreadable evidence blocks every
transition.

Every binding check — operator configuration against the canonical launch, and
observation against the canonical identity — precedes any transition or removal,
so a configuration naming another launch produces no effect at all.

The canonical compare-and-swap orders the records; it does not freeze Docker. The
command therefore re-observes after writing and reports
`observation_changed_after_recording` if the container changed under it, instead
of presenting the record as a clean outcome. `deadlineExceeded` is computed from the recorded start
time and the container's own finish time — never guessed, so a missing timestamp
returns `deadline_unknown` instead of a recorded result.

Exit 0 means the canonical launch is now terminal, exit 3 that it is not and why,
exit 2 that reconciliation itself is unconfirmed. No job file, checkout, result or
dossier is ever deleted. With `--gateway-root` the per-launch provider gateway is
released only once the launch is terminal, the agent container is observed in an
explicitly releasable state (`absent`, `created`, `exited`, `dead`) and its
identity matches the claim. Every other observation, including `unknown` and any
identity mismatch, keeps the resources and states why. The gateway journal is
retained and marked `released`.

This closes a launch or recovers a result. It is never a validation of the work.
