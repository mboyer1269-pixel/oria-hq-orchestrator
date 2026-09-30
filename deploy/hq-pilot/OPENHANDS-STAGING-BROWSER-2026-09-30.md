# Actual authenticated OpenHands preview on HQ staging

## Product correction

HQ production boot formerly required a model API key even for mission control and
CLI-backed work. `src/lib/server-env.ts` in canonical Oria.HQ now keeps owner and
Supabase configuration mandatory, while reporting absent model APIs as the stable
health warning `model_api_keys_missing`. It neither connects CLI accounts nor grants
provider access. No secret or actual runtime .env file was changed.

Configuration tests: 22 pass. Newly exercised inventory tests exposed two previously
undocumented OpenHands variables and an undeclared operator-only performance flag;
the schema and empty/disabled `.env.example` entries now document these. No feature
was enabled by the template. Typecheck, lint, build and smoke:joris all exit0 (existing
lint warnings remain). Logs: `.validation/hq-api-optional-tests.log` and
`.validation/hq-api-optional-gates.log` in Orchestrator. No commit or push.

## Candidate and runtime

File-verified development image:
`sha256:399a7f6f443424d80bf2b07b314e67fd49887323a5d73414ad09bfb68e3446dd`.
1112 manifest files verified, including 298 test files. Manifest hash:
`263E22F710BA2EF5C5E91390DA718D410C93E957BF19C3CFAC64DE0EB52B5FB0`.

Standalone staging image:
`sha256:1499e56946446c52765d7d691a325cf8b9ee90e9f4820aa0a621d8830aba03e3`.
Built from the verified candidate, without npm installation. Only existing public
Supabase URL/anon configuration is passed to build; no service-role/provider key.

Scripts: OpenHands.staging.Dockerfile, build-openhands-staging.py (explicit immutable
source image), start-openhands-staging.py (explicit immutable runtime image).
Existing named container is refused rather than silently replaced.

VPS container `oria-hq-openhands-staging`, UID1000, root filesystem read-only,
capabilities dropped, no operational mounts, bounded CPU/RAM/pids and logs.
Only VPS loopback127.0.0.1:3332 is published. Local SSH tunnel exposes
http://localhost:3332/hq/missions while its process is live. Main HQ3321 remains v13.

This candidate uses the EXISTING HQ Supabase database and owner configuration,
not a disposable database. Qualification was limited to reads and dossier preview.
No reservation/approval/mission creation was submitted. Provider keys, Memex
handles, schedulers and webhook credentials were not copied. Durable draft creation
is disabled; OpenHands preparation/confirmation is enabled, agent execution absent.

## Browser evidence

- Anonymous OpenHands API:401. Health HTTP200 with model_api_keys_missing and
  inngest_keys_missing, accurately degraded.
- Existing owner browser session successfully opened the staged missions page.
- OpenHands form now visible, unlike live v13.
- User-visible project memory list explicitly reports none configured.
- Prepared existing mission using commit2cbea807174ab58de9b5811a6e92898e537e7427
  (independently observed in the isolated provider workspace), SDK1.50.0,
  requested100cents/10000tokens/2iterations/60seconds.
- Actual server preview displays objective/scope/criteria/commit/budgets, unchecked
  confirmation and disabled reserve button. It explicitly states no authorization
  recorded yet and no execution. The route itself still labels commit unverified;
  separate Git observation must not be confused with route enforcement.
- Screenshot `.validation/hq-openhands-staging-preview.png`.

Not proven: actual project Memex binding in this staging instance, reservation via
this UI, model execution, sandbox tool permissions, independent review or recovery
of a running provider. Claude consent still pending in its separate official tab.
