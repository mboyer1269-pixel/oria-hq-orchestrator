# Claude ACP candidate runtime — not connected or deployed

The parent builds this separate image using an immutable `PERMISSION_BASE` image
ID for the already-qualified OpenHands permission extension. It never changes
that image or any existing service. Build context is this directory only.

Pinned direct dependency: `@agentclientprotocol/claude-agent-acp@0.84.0`, Node>=22.
Official Node22 bookworm-slim manifest digest, resolved from Docker Hub registry:
`sha256:43ac6c60b8f89723f746e8a92ce91abd5017e627ce1ddfe4238355d3a30b772c`.
ACP npm gitHead: `bdb50ad984336e62dde1d41339f04071f6617085`.
SDK dependency: `@anthropic-ai/claude-agent-sdk@0.3.284`.
That SDK's optional `@anthropic-ai/claude-agent-sdk-linux-x64@0.3.284`
already ships the Claude native executable. No separate Claude CLI installation
is needed. This Dockerfile deliberately qualifies Linux x64/glibc only.

Build uses npm ci with lifecycle scripts disabled and the checked-in package-lock.json.
The lock and dependencies-observed.json stay in /opt/claude-acp for review.
The Node base and npm dependency graph are pinned. Debian packages are still
resolved at build time rather than from a snapshot; the complete image build
is therefore not claimed to be reproducible.

Nonroot UID10001; no secrets, model call or login in the build. Parent should
first run with network disabled, read-only root, bounded resources and writable
temporary HOME: `claude-agent-acp --cli --version`,
`claude-agent-acp --cli auth --help`, and `claude-agent-acp --cli auth status --json`.
Use `--entrypoint claude-agent-acp` because inherited default remains Python.
Logged-out status is expected and should not trigger an API fallback.

## Official subscription login sequence to qualify separately

Use a dedicated private home volume for this runtime. No Paperclip token copying,
extraction, shared credential mount or API-key fallback. The official ACP source
offers `--cli auth login --claudeai` for subscription login; on remote terminals
it offers `--cli` and interactive `/login` instead because browser redirects may
not work. First inspect the bundled executable's current help; then run the
official interactive flow with the user. Do not choose `--console` (API billing).
Verify `--cli auth status --json` reports the expected subscription source before
any inference. No user account connection has been performed by these files.

OpenHands can later invoke `acp_command=["/usr/local/bin/claude-agent-acp"]` using
the qualified PermissionAgent, default session mode and the scoped policy. This
does not itself enforce provider tool sandboxing, usage budgets or durable HQ
approvals. Real provider execution remains a separate bounded qualification.

Primary evidence:
- https://registry.npmjs.org/@agentclientprotocol/claude-agent-acp/0.84.0
- https://registry.npmjs.org/@anthropic-ai/claude-agent-sdk/0.3.284
- https://github.com/agentclientprotocol/claude-agent-acp/blob/bdb50ad984336e62dde1d41339f04071f6617085/src/acp-agent.ts#L1719
- https://github.com/agentclientprotocol/claude-agent-acp/blob/bdb50ad984336e62dde1d41339f04071f6617085/src/acp-agent.ts#L2399
