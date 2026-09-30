# Provider policy identity in actual HQ storage

Verified on the isolated VPS harness, 2026-09-30:

```sh
python3 /opt/oria-openhands-qualification/openhands-runner/qualify_hq_postgrest.py --provider-binding
```

The harness uses actual HQ launch, pending-discovery and lifecycle services with disposable PostgreSQL/PostgREST. The provider profile is explicitly synthetic; no policy registry, provider account or model is used. Existing source overlays include the current canonical HQ launch contract. This is not a qualification of a deployed production build.

Observed successful assertions:

- Launch authorization persists the exact provider profile in the action ledger.
- Discovery with the approved profile finds the claimed mission.
- Changing its policy digest or removing the profile yields no eligible mission and one rejected candidate.
- Foreign workspace discovery finds no mission.
- The actual discovery CLI works and rejects a writable host profile.
- Lifecycle transitions and ledger writes complete using a synthetic container identity.
- After PostgreSQL restart, the exact provider profile and terminal lifecycle state remain available.
- Harness exits 0 and removes its disposable resources; no public ports or production database are used.

Limits: this test does not prove owner authentication, RLS, real Memex reads, Docker agent execution, provider policy enforcement or a model response. Those require their own connected-path evidence. The next integration is to run the worker's opt-in provider gateway against these canonical lifecycle services with the existing explicitly synthetic ACP runtime, then qualify the authenticated provider when consent is available.

The `--provider-binding` mode refuses execution-oriented harness flags to prevent accidentally presenting this storage fixture as a real provider mission.

## Connected worker, gateway and storage qualification

Also verified on the VPS on 2026-09-30:

```sh
python3 /opt/oria-openhands-qualification/openhands-runner/qualify_hq_postgrest.py --synthetic-provider
```

This additional mode creates a protected temporary policy for the pinned synthetic ACP image `sha256:ecfafc87bc148d922dd4d43c3c5d3bb80f4a0828e4ff9af22ef80b7bd5c2924d`. The actual host worker acquires the canonical HQ mission, creates the restricted gateway, starts the real isolated Docker runtime and writes completion through the actual HQ lifecycle services.

Successful run: launch `d750a488-cbf4-4f94-a9ff-5a1752d53231`, container `31a641f9a54dd91c6a542a629b16e876f45e7dc8be952a889c981ea467f23493`. Supervisor observed exit 0 after 9.611 seconds, stopped container, no exceeded deadline. This is a single synthetic observation, not a model speed benchmark. The canonical dossier and exact source commit reached the runtime. The synthetic adapter verified TLS through the proxy and rejection of a foreign host. The gateway journal ended `closed`. Canonical completion and the policy survived PostgreSQL restart. The harness exited 0 and removed disposable containers/database volume.

Host modules came from release `13f37664b839a99cffcaa41c02361fbb0043c5e0b5623f87b398c34bfc9847ad`, archive SHA256 `880821bd7aef45b24ac33169a3d9f7c8e116296fcf0c98a46d9a060f818ed3d3`, in the qualification directory only. The first run reached exit 0 but failed a stale test assertion expecting missing-auth exit 1; the mode-specific expectation was corrected before the successful rerun.

Still not qualified: authenticated Claude, real coding output, independent review, owner authentication/RLS and real Memex context in this connected mode. `independentValidationPassed` remains false. No account or model call was used; active HQ and the installed consumer remain unchanged.

## Connected Memex service qualification

The additional `--synthetic-provider --live-memex` run succeeded on 2026-09-30, launch `9410a3f2-35a4-403d-85ec-287d0e2fd8c0`, runtime exit 0, observed 9.816 seconds (not a benchmark). This uses the actual Memex image in a disposable isolated namespace with an in-memory database and short-lived signed, read-only project handle. It does not read the production project memory.

The HQ transport made two instrumented HTTP requests to capture context and zero during the verification phase after PostgreSQL restart. These are request counts, not a token/cost measurement. A separate fixture mutation and verification request intentionally changed the live test graph after capture. HQ retained its confirmed snapshot.

Assertions inspected all seven files in the SDK conversation directory: the original project decision was present, the foreign project's marker was absent, and the new decision introduced after capture was absent. The canonical dossier reached the real runtime, the proxy closed, and persisted memory/profile/lifecycle survived database restart. The synthetic ACP adapter returned without calling a model. This connects Memex HTTP, HQ durable storage, host worker, proxy and OpenHands SDK in one qualification, while actual project provisioning, authenticated Claude and independent coding validation remain unproven.
