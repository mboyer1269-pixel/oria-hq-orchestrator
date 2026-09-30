# Experimental instance-scoped ACP permission extension

Upstream SDK 1.50.0 / commit dcf401af7a9a302ef92cb7d092e1df9bb659daa5.
This directory is a candidate integration, not deployed or production-qualified.

In a NEW disposable image built from the qualified SDK image, copy this directory
and run `python apply_patch.py` during build. The patch refuses unexpected version,
source SHA256 or anchors. It adds one virtual factory method to ACPAgent and
changes one bridge construction call to `self.create_acp_bridge()`. No global
runtime monkeypatch. The original SDK file is recoverable by discarding the image.
Running the patch twice intentionally fails rather than claiming a clean base.

Run `python qualify_instance_policies.py` with network disabled, no credentials,
read-only root, temporary writable /tmp and an external 60-second container
watchdog. Two real SDK conversations use different per-instance policies
concurrently; a third deny run checks no allow-policy leakage. The synthetic
peer makes an actual ACP permission request and reports the received answer.

The custom PermissionAgent defaults to deny and requests session mode `default`.
`upstream-auto-allow` is an explicit test control, not a recommended deployment.
The policy field is serializable, but custom-agent server registration and cold
deserialization remain unqualified. Existing providers may execute operations
without requesting permission; this extension is not a sandbox. No durable HQ
approval, path authorization, real provider, restart, or remote lifecycle is
claimed. A future production callback requires a correlated canonical request,
bounded wait, durable decision, revocation handling and fail-closed errors.

Parent must execute the image and retain output; syntax checks alone do not prove
the runtime contract. No installation or deployment is performed by this folder.

Runtime callback candidate: `agent.set_permission_callback(async_callback,
timeout_seconds=1)` attaches an instance-only async policy. It receives copied
`session_id`, `tool_call`, and `options`; response must validate as an ACP
RequestPermissionResponse and select an offered option or cancel. Exceptions,
expired deadlines, unknown options and policy replacement fail closed. Caller
async cancellation propagates. Timeout cancels the callback task without waiting
indefinitely; trusted callbacks must cooperate with cancellation and never block
the event loop. This is not a process-level isolation boundary.

PrivateAttrs hold callback and deadline: serialization drops both, so default
deny applies after reconstruction until explicitly reattached. The explicit
upstream-auto-allow test control cannot accept a callback. No HTTP, secrets,
durable approval ledger or human interface is introduced. Execute
`python qualify_callbacks.py` plus the existing concurrent-instance test. Callback
unit qualification uses real ACP schemas/factory but does not launch a provider.

## Candidate Claude session budget metadata

In another disposable image derived from the qualified permissions image, run
`python apply_budget_patch.py`. It requires the exact permissions-patched source
SHA256 `7a496b59265b8139e3dd965e9ef95e28133db5cfa4b48ee20da12c328e152455`.
It adds `build_acp_session_meta` and redirects only the fresh-session metadata
construction through that per-instance factory. Existing patch files are unchanged.

`BudgetPermissionAgent` requires strict bounded `hq_max_iterations` and
`hq_max_cost_cents`, supplies Claude `maxTurns` and `maxBudgetUsd`, and explicitly
disables dangerous bypass in session options. Permissions still default to deny.
No taskBudget alpha feature and no hard token cap are claimed. Use this subclass
only for a fresh Claude session; it does not update budgets of loaded sessions.
Existing model-selection metadata is preserved by copying/merging options.

Run `qualify_session_budgets.py` in the patched image, network disabled, no
credentials, with external timeout60. Two concurrent synthetic peers report
the metadata actually received on new_session. This qualifies transport and
instance isolation only, not Claude's enforcement. Claude maxBudgetUsd stops
after exceeding estimated consumption; it is not a hard prepaid ceiling.
Wall-clock supervision remains a separate responsibility. No model calls.
