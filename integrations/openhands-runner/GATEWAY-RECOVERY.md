# Read-only gateway recovery inspection

`provider_gateway.inspect_gateway(root=..., launch_id=...)` reads the protected lifecycle journal and independently queries Docker for the exact deterministic container and network names. It verifies resource IDs and purpose/launch labels before accepting their identity. Only selected metadata is inspected; credentials and environment variables are not returned.

The result separates `journalState`, `containerState` and `networkState`. Errors remain unknown with `inspectionIncomplete`; a journal saying `ready` does not establish that a proxy is running. Stopped or mismatched resources still require reconciliation. No cleanup, restart, retry or canonical HQ state mutation is performed. `reconciliationRequired` concerns gateway resources only, not the mission's result or readiness for retry. Absence is a point-in-time observation, not a lock against concurrent creation.

Validation on 2026-09-30: four focused tests passed locally; all thirteen gateway/inspection tests passed on VPS Linux. Read-only inspection of actual crash-test launch `ed982190-2c13-4223-bb4f-1fb78f09128a` returned journal `ready`, container `absent`, network `absent`, no resources modified and no automatic retry. This confirms stale-journal detection against actual Docker; other branches currently have unit-test coverage.

The inspection helper is available in source and the qualification directory. It is not yet displayed in HQ or used to reconcile mission state automatically. Active services remain unchanged.

## Canonical operator report

`run_host_job.py --config <protected-operator.json> --inspect --gateway-root <protected-directory>` now reads the canonical HQ mission and gateway observations without executing work. Inspection permits an existing review socket; normal execution continues to refuse it. Host directory names must match the canonical launch. The report contains only selected mission identity/state and resource metadata, not the trusted command or credentials.

`recovery_report.py` reads canonical state before and after resource inspection. An observed change yields `changed_during_inspection`; two equal reads are a bounded observation, not an atomic lock. Missing journals remain unknown. Offline configurations do not inspect a provider. Neither stopped nor absent gateway resources authorize a retry or establish independent validation.

Validation: full Windows suite 121 tests, 100 passed and 21 platform skips; eight targeted operator/report tests passed on VPS Linux. The actual Memex/HQ/PostgREST/worker/synthetic-ACP harness also passed with the report, launch `65ee8c17-ae2e-41e7-a283-0abcd319c712`: canonical `execution_finished`, stable observation, gateway journal `closed`, container/network absent, resumeAuthorized false. No model or production data used. CLI configuration and error branches have unit coverage; the connected harness calls the report function directly.

The reproducible host package now includes 23 files, release `cc33754de5d5e5f1494ba208836c75ac15f7e5ae9b0ece3cdeba7cd506b6215b`, archive SHA256 `80a1e066594a60878f9df2bf60681825e0a94c0b3301dd291dab59dc83f6bf3e`. Built locally; not installed as the active consumer. HQ UI integration remains outstanding.

## Host file to actual HQ reader

On 2026-09-30 the disposable harness passed with `--synthetic-provider --live-memex --recovery-report --hq-image sha256:501aee05ffaf05ef94927cc5cf5b100c938b709b5adad9d6f4f0a398ecfac59b`. Python published the real observed report atomically into a protected directory, mounted read-only at the exact HQ report path. The actual HQ recovery reader loaded it against the actual disposable canonical store, returned recent/execution_finished/absent resources, denied foreign actor/workspace and confirmed an attempted fixture write failed with EROFS. After database restart the same checks passed as UID1000, matching the non-root web application user.

Successful launch: `7ad5faf0-ed0b-47a4-8025-9848872c7932`, runtime9.46seconds, synthetic ACP/no model. First non-root attempt exposed a qualification-script directory permission problem; fixed by copying only the fixture script and dossier into a dedicated traversable read-only mount, without relaxing operational directories. Positive browser panel rendering and real authenticated model work remain unqualified. Existing database and report directory for staging were not populated with synthetic results.
