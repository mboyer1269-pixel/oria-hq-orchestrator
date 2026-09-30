# Isolated Antigravity SSH executor

Prepared overlay, not remotely deployed by this task. Reuses the existing reviewed SSH runner image. Use with compose.json and select only antigravity-runner; it has no dependency on other runners. The controller override antigravity.paperclip.networks.json adds only the internal control network to Paperclip when merged with its existing network overrides.

Required external paths:

- ANTIGRAVITY_BINARY_PATH: `/opt/oria-provider-staging/antigravity-1.2.13/antigravity`, previously checksum/version verified by root.
- ANTIGRAVITY_MODULE_PATH: reviewed `integrations/antigravity` directory, including remote-entry.mjs and its relative module dependencies.
- ANTIGRAVITY_DEADLINE_WRAPPER: absolute uploaded bounded-command.sh path (LF).
- ANTIGRAVITY_AUTHORIZED_KEYS_FILE: dedicated public authorized_keys, never a private key.

Existing `oria-antigravity-home` remains external; new workspace/hostkey volumes are exclusive to this provider. Container executes as UID1000 with read-only root, dropped capabilities, resource limits and no published ports. Code and binary binds are read-only; no Docker socket, application database environment, shared provider home or app credentials are mounted. Control network is internal; separate egress bridge enables provider HTTPS but is not an outbound allowlist.

```sh
node deploy/providers/runner/validate-antigravity.mjs
docker compose -f deploy/providers/runner/compose.json -f deploy/providers/runner/antigravity.compose.json config --quiet
docker compose -f deploy/providers/runner/compose.json -f deploy/providers/runner/antigravity.compose.json up -d --no-build antigravity-runner
```

Root must check GNU timeout exists in the actual image (`timeout --version`), SSH strict host-key verification, provider version, absence of app secrets, and writable isolated workspace. Authentication success is independent of these infrastructure checks.

## Remote process lifetime contract

Execute through SSH as node in /workspace, HOME=/paperclip:

```sh
/bin/sh /opt/oria-runner/bounded-command.sh 305 node /opt/oria-antigravity/remote-entry.mjs
```

The adapter supplies JSON `{prompt,timeoutMs,runId}` on stdin and consumes a bounded JSON result. Its remote runner deadline must be at most300 seconds. GNU timeout is an independent remote watchdog: TERM to its process group at305 seconds, escalation to KILL after5 seconds. HUP is ignored before launch so an SSH disconnect alone does not remove that watchdog. Exit124 indicates deadline;137 can indicate kill escalation. Neither proves success or immediate cancellation.

The controller timeout must allow this cleanup window (at least315 seconds for the maximum runtime) or invoke its independently verified cancellation hook. A dropped SSH connection or killed local ssh process **does not prove remote stop**. Descendants that deliberately create another session/process group can escape group signals. For definitive containment the host controller stops this dedicated executor container and verifies stopped state; serialize one active run per executor before using that fallback. No Docker socket is exposed to the runner. The transport must refuse activation if its required host-owned cancellation hook is missing. Container restart preserves provider login/workspace volumes.

The wrapper is a last deadline bound, not a job cancellation API or process ownership registry. Runtime cancellation and orphan-process tests remain required before claiming the adapter operational.
