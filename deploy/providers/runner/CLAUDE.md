# Claude SSH executor with a dedicated empty home

Assets only: no activation or secret reads performed. Reuses the existing SSH runner image containing Claude CLI. HOME=/paperclip mounts the dedicated new named volume `oria-claude-home`; no application volume, login subpath or provider credential copy is mounted. Separate workspace, SSH host keys, internal control network and outbound bridge belong to Claude. UID1000, read-only root, dropped capabilities, limits and no published ports remain enforced.

The temporary login directory previously considered is removed after successful promotion: pinned Paperclip `server/src/services/local-ai-login.ts` calls aiConnectionService.save then removes loginHome. It is not a durable login source. Do not recreate it or copy application home into this runner.

## Native Paperclip authentication

Use the native claude_local adapter with the existing selected managed AI connection. Paperclip stores connection secrets using its local_encrypted provider (`server/src/services/ai-connections.ts`), resolves the managed connection for execution (`server/src/services/ai-connection-runtime.ts`), and supplies its selected runtime configuration. The Claude adapter uses CLAUDE_CONFIG_DIR for the managed seed and materializes remote authentication/config through `materializeRemoteClaudeConfig` when the execution target requires a managed home (`packages/adapters/claude-local/src/server/execute.ts`). Authentication is provided by this governed run flow, not by a permanently logged-in CLI home mounted by this overlay. No database credentials are supplied to the executor by Compose.

A standalone Claude auth-status check in the initially empty home may report not authenticated; that does not test managed connection injection. Validate one actual native Paperclip run with its AI connection binding. The runtime may materialize sensitive provider configuration inside its own workspace/home: treat those volumes as private and never print their contents. The exact SSH target managed-home branch must be verified during the real run, not assumed from container health.

## Operator preparation

Set CLAUDE_AUTHORIZED_KEYS_FILE to a dedicated external public authorized_keys file. A new oria-claude-home volume inherits image UID1000 ownership; if a volume of that name already exists, stop and review its provenance instead of silently reusing a different provider's home. No auth copy step is required or authorized here.

```sh
node deploy/providers/runner/validate-claude.mjs
docker compose -p oria-provider-runners -f deploy/providers/runner/claude.compose.json config --quiet
# Root performs deployment only after reviewing the empty dedicated home:
docker compose -p oria-provider-runners -f deploy/providers/runner/claude.compose.json up -d --no-build claude-runner
```

Merge claude.paperclip.networks.json into the controller configuration to add the Claude control network while preserving existing networks. Root must verify strict SSH host-key checks, UID1000/HOME, writable isolated workspace, CLI version, no application mounts or database environment, then run a synthetic task through native Paperclip and test cancellation. No direct CLI login persistence is claimed.
