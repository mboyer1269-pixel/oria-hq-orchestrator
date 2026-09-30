# Native Claude pilot — ready-to-configure contract

Read from the deployed Paperclip source and installed CLI; no native agent has been registered yet. Board authorization is required. A connection to Claude alone does not authorize administrative Paperclip API calls.

## Environment

Create through the official `/api/companies/{companyId}/environments` endpoint, not by database mutation. Payload fields:

```json
{
  "name": "HQ Claude pilot",
  "driver": "ssh",
  "status": "active",
  "config": {
    "host": "claude-runner",
    "port": 2222,
    "username": "node",
    "remoteWorkspacePath": "/workspace/hq-development",
    "privateKeySecretRef": {
      "type": "secret_ref",
      "secretId": "REPLACE_WITH_EXISTING_DEDICATED_SECRET_UUID",
      "version": "latest"
    },
    "knownHosts": "REPLACE_WITH_VERIFIED_PUBLIC_HOST_KEY_LINE",
    "strictHostKeyChecking": true
  },
  "envVars": {}
}
```

These placeholders intentionally are not directly executable. Register the dedicated SSH secret through the native secret API without printing the private key. The controller's existing private key and verified public known-hosts file remain on the VPS. Probe `/api/environments/{id}/probe` before registering the developer.

## Agent

Use adapterType `claude_local`, top-level `defaultEnvironmentId`, and explicit adapterConfig:

- `cwd`: `/workspace/hq-development`.
- `dangerouslySkipPermissions`: **false**, overriding the deployed adapter's true default.
- `timeoutSec`:120, `graceSec`:10, `maxTurnsPerRun`:4 for the initial bounded qualification. Reassess based on measured duration before the larger mission.
- Initial qualification `extraArgs`: `--permission-mode dontAsk --permission-prompts none --tools Read,Edit,Write --allowedTools Read Edit Write`. No shell needed to prove a bounded file edit. Validate those arguments as an array, not an interpolated shell command.
- `runtimeConfig.aiConnection`: provider `anthropic`, method `subscription`, mode `responsible_user`. Verify the operator's connection is available. Shared mode instead requires both connectionId and grantId.
- `runtimeConfig.heartbeat`: enabled false, intervalSec0, wakeOnDemand false, maxConcurrentRuns1 at creation. Enable demand execution only for the intended explicit run; the periodic scheduler remains disabled.
- `permissions`: canCreateAgents false, canCreateSkills false.

The initial task must read a named project source and produce a bounded candidate change or artifact. The principal validates the result independently; this is runner qualification, not completion of the HQ development mission. No repeated model probes or automatic retries.

For later agent-triggered tests, a fixed wrapper can be authorized explicitly. A root-owned wrapper is not a sandbox: scripts/tests inside the candidate may execute arbitrary code. Prefer a separate validation container with the candidate sources and **no provider home, operational secrets, host socket or application volumes**. Node22 is required for HQ while the existing provider runner uses Node24. Do not silently switch Claude's runtime to solve the application-test requirement.

## Cancellation

The development checkout is initialized on `codex/hq-self-development` at baseline `529f7a2d52a2d13635442653a0db9b003a9f2413`. Its 1,072 exported files were verified byte-for-byte against development-v2's manifest. The working tree is clean. The older `/workspace/hq-pilot` deployment-source checkout remains untouched and must not be selected for development. The baseline is a local snapshot, not an upstream commit or a pushed branch. Git normalizes line endings in the index according to the repository attributes; the source manifest identifies the exact validated working bytes.

Run application validation through the separate Node22 image and operator validation pipeline; dependencies are intentionally absent from this source checkout. No native Paperclip environment has been registered by this preparation.

Paperclip's cancellation signals its local SSH process group. The deployed implementation explicitly does not guarantee that all remote descendants terminate. Keep the pilot runner exclusive and verify remote process state. If native cancellation leaves work alive, stop the dedicated runner container, verify Running=false/Pid=0, then start only after checking the retained diff. A remote watchdog can additionally bound execution but is not yet integrated in the native adapter.

Do not mark a mission stopped because the HTTP cancellation request succeeded. Do not publish provider tokens or command logs containing credentials. Monthly budget configuration is not a guaranteed subscription token ceiling.

## Source evidence

Deployed `/app/server/src/services/environment-config.ts`, `/app/packages/shared/src/ai-connections.ts`, `/app/packages/shared/src/validators/agent.ts`, `/app/packages/adapters/claude-local/src/server/execute.ts`, `/app/packages/adapter-utils/src/server-utils.ts`, and `/app/packages/adapter-utils/src/execution-target.ts`. CLI help inspected in the existing container. Revalidate paths and schema before applying to a different Paperclip version.
