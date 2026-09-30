# Protected provider policy verification

Current status clarification (2026-09-30): the default operational entry point
still refuses provider execution, but the worker now has an explicit trusted
`gateway_root` integration used by the connected qualification harness. See
`PROVIDER-INTEGRATION-GAPS.md` for the current critical path and
`PROVIDER-STORAGE-QUALIFICATION.md` for bounded evidence. Statements below about
the gateway lifecycle being unimplemented describe the earlier verifier-only
checkpoint. Neither successful policy validation nor the synthetic gateway test
proves authenticated Claude execution.

Implemented locally 2026-09-30; not installed into the active host runtime.

`provider_policy.py` is called by the serial consumer before job allocation and by the permission worker after canonical configuration reread. Legacy profiles without `providerProfile` remain unchanged. Explicit profiles are validated against `/etc/oria-hq/provider-policies/<id>/policy.json` and its three sibling artifacts: `squid.conf`, `entrypoint.sh`, `relay.mjs`.

The loader requires Linux, real absolute paths, root ownership and no group/world write permissions throughout the ancestor chain. It refuses symlinks, non-regular files and oversized reads. The manifest must be strict canonical JSON with no duplicate or additional keys. Its exact bytes must hash to the approved `policySha256`; runtime image must equal the canonical mission configuration; proxy image is pinned. Transport, provider, authentication and connector settings must match the supported candidate contract. Each artifact must hash to its manifest entry. Paths, credentials and arbitrary configuration extensions are never accepted through the public profile.

A malformed, missing or mismatched policy returns `invalid_provider_policy` before effects. An intact policy still returns `unsupported_provider_profile`: verification alone does not implement proxy lifecycle, authenticate the CLI, enforce actual account connector settings or qualify tool review. The checked proxy image is an identity to use in the future executor, not proof that a running container currently uses it. Do not replace this refusal with success until the actual execution settings are bound and tested.

Full host regression suite: 85 passed, 9 platform-dependent tests skipped on Windows, no failures. No HQ source was changed in this step, so the preceding HQ typecheck/lint/build/smoke results were not rerun or represented as new results.

`build_host_release.py` now explicitly includes the verifier; dependency coverage tests protect that inclusion. No active service, installed host package, HQ deployment or credential was changed.

Verification: targeted local suite 11 passed, one Linux test skipped. All five policy tests passed on the actual VPS, including filesystem tampering, writable permissions and symlink cases. The loader also verified the real previously qualified proxy artifacts against manifest digest `0e89f8c258736ce30e465244f56c99cf2a7afc7e455b0887bddef634584c29ba` in an isolated root-owned directory under `/opt/oria-openhands-qualification/provider-policy-check/qualified`. This is not the production registry. The real manifest result was `executionEnabled: false`.
