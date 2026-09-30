# Protected provider policy verification

Current status clarification (2026-09-30): the default operational entry point
still refuses provider execution, and the worker has an explicit trusted
`gateway_root` integration used by the connected qualification harness. A later
change on the same day added the missing operator binding: an optional
`providerExecution` object in the root-owned operator/consumer configuration
supplies that `gateway_root` together with the approved `profileId` and
`policySha256`, and the worker refuses any canonical profile that is not the
approved one. Default configurations omit the key and are unaffected. See
`PROVIDER-INTEGRATION-GAPS.md` for the current critical path and
`PROVIDER-STORAGE-QUALIFICATION.md` for bounded evidence. Statements below about
the gateway lifecycle being unimplemented describe the earlier verifier-only
checkpoint. Neither successful policy validation nor the synthetic gateway test
proves authenticated Claude execution.

Implemented locally 2026-09-30; not installed into the active host runtime.

`provider_policy.py` is called by the serial consumer before job allocation, by canonical preparation before any launch directory exists, and by the permission worker after canonical configuration reread. Legacy profiles without `providerProfile` remain unchanged. Explicit profiles are validated against `<policyRoot>/<id>/policy.json` and its three sibling artifacts: `squid.conf`, `entrypoint.sh`, `relay.mjs`. Without an operator authorization the registry is the compiled-in `/etc/oria-hq/provider-policies`; with one it is the `policyRoot` that authorization names, held to the same protected-path rules, and the worker refuses a policy root or gateway root that is not the authorized one.

The loader requires Linux, real absolute paths, root ownership and no group/world write permissions throughout the ancestor chain. It refuses symlinks, non-regular files and oversized reads. The manifest must be strict canonical JSON with no duplicate or additional keys. Its exact bytes must hash to the approved `policySha256`; runtime image must equal the canonical mission configuration; proxy image is pinned. Transport, provider, authentication and connector settings must match the supported candidate contract. Each artifact must hash to its manifest entry. Paths, credentials and arbitrary configuration extensions are never accepted through the public profile.

A malformed, missing or mismatched policy returns `invalid_provider_policy` before effects, and so does a canonical profile whose identity or digest differs from the operator-approved `providerExecution`. Without that explicit approval an intact policy still returns `unsupported_provider_profile`: verification alone does not implement proxy lifecycle, authenticate the CLI, enforce actual account connector settings or qualify tool review. With it, the already-qualified gateway lifecycle runs under the shared mission deadline; that is a wiring change, not evidence of authenticated Claude execution. The checked proxy image is an identity to use in the future executor, not proof that a running container currently uses it. Do not replace this refusal with success until the actual execution settings are bound and tested.

Full host regression suite: 85 passed, 9 platform-dependent tests skipped on Windows, no failures. No HQ source was changed in this step, so the preceding HQ typecheck/lint/build/smoke results were not rerun or represented as new results.

`build_host_release.py` now explicitly includes the verifier; dependency coverage tests protect that inclusion. No active service, installed host package, HQ deployment or credential was changed.

Verification: targeted local suite 11 passed, one Linux test skipped. All five policy tests passed on the actual VPS, including filesystem tampering, writable permissions and symlink cases. The loader also verified the real previously qualified proxy artifacts against manifest digest `0e89f8c258736ce30e465244f56c99cf2a7afc7e455b0887bddef634584c29ba` in an isolated root-owned directory under `/opt/oria-openhands-qualification/provider-policy-check/qualified`. This is not the production registry. The real manifest result was `executionEnabled: false`.

## Connected operator-path evidence (2026-09-30)

`qualify_hq_postgrest.py --operator-provider` runs the provider path through the
actual consumer, canonical preparation, operator entry and worker, with a
protected explicit authorization. Two harness-only faults extend it:
`--interrupted-start` kills the operator as soon as the container exists, and
`--lost-completed-response` discards the response of a completed execution. The
three invocations ran on the VPS from a disposable qualification root. See
`../../docs/CLAUDE-PREUVE-OPERATEUR-RESULTAT.md` for the exact observations. The
synthetic ACP adapter and disposable policy registry mean this proves the
raccordement and its refusals, not authenticated Claude execution.
