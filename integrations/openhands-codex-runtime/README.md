# Codex ACP candidate runtime — not built, not connected, not deployed

Mirrors `../openhands-claude-runtime/` exactly: same Node base image digest,
same `PERMISSION_BASE` chaining, same nonroot UID10001, same "no secrets,
model call or login in the build" doctrine. **Unlike the Claude candidate,
this one has not been built or qualified in any session** — see RESULTS.md
for the exact reason and what reproducing that would require.

Pinned direct dependency: `@agentclientprotocol/codex-acp@2.1.1`, Node>=22.
Official Node22 bookworm-slim manifest digest (same image already used by the
Claude candidate, resolved independently from Docker Hub registry):
`sha256:43ac6c60b8f89723f746e8a92ce91abd5017e627ce1ddfe4238355d3a30b772c`.
ACP npm gitHead: `68d7d2d5ddfc0ed5746f9f6130892dda685e65dd`.
Bundled Codex dependency: `@openai/codex@^0.159.1`, resolved and pinned in
`package-lock.json` to `0.159.3` (and its `@openai/codex-linux-x64@0.159.3-linux-x64`
optional platform package, which ships the actual native `codex` executable
under `vendor/x86_64-unknown-linux-musl/bin/codex`). No separate Codex CLI
installation is needed. This Dockerfile deliberately qualifies Linux
x64/musl-binary-on-glibc-base only, same target scope as the Claude candidate.

Build uses `npm ci` with lifecycle scripts disabled and the checked-in
`package-lock.json`. The lock and `dependencies-observed.json` stay in
`/opt/codex-acp` for review. The Node base and npm dependency graph are
pinned; Debian packages are still resolved at build time, so the complete
image build is not claimed to be reproducible (same caveat as the Claude
candidate).

Nonroot UID10001; no secrets, model call or login in the build. Parent
should first run with network disabled, read-only root, bounded resources
and writable temporary HOME: `codex-acp --version`. Use
`--entrypoint codex-acp` because the inherited default remains Python.
A logged-out ACP `initialize` response (no account, `authMethods` only)
is expected and should not trigger an API-key fallback.

## Why this is a *different* adapter from the one already in the locally
## cached `ghcr.io/openhands/agent-canvas:1.0.0-rc.11` image

Michael pointed out a stopped local image (`agent-canvas:1.0.0-rc.11`, built
2026-06-12, OpenHands core `v1.28.1`) that already bundles three ACP
adapters under `/opt/acp-node` with working wrapper scripts at
`/usr/local/bin/{claude-agent-acp,codex-acp,gemini}`. Read-only inspection
(`docker image inspect`, `docker history --no-trunc`, and a single bounded
`--network none --read-only` container run listing installed package
versions — no login, no model call, no credential mount) found:

| Adapter | Baked into `agent-canvas:1.0.0-rc.11` | Current official (this candidate) |
|---|---|---|
| Claude | `@agentclientprotocol/claude-agent-acp@0.30.0` | `0.84.0` (already qualified separately) |
| Codex | `@zed-industries/codex-acp@0.15.0` | `@agentclientprotocol/codex-acp@2.1.1` |
| Gemini | `@google/gemini-cli@0.38.0` | not in scope of this mandate |

The npm registry's own metadata for `@zed-industries/codex-acp` (both
`0.15.0` and its current `0.16.0` tip) carries an explicit deprecation
notice: *"This package has been replaced by `@agentclientprotocol/codex-acp`.
Please migrate to continue receiving updates."* It is also a different
binary lineage: the installed `codex-acp` in that image is a JS shim over a
bundled native CLI with its own `--help`-driven option parser (no bare
`--version` flag - `error: unexpected argument '--version' found`), compiled
before the project moved to the `agentclientprotocol` GitHub org that
OpenHands' own `ACP_AGENTS.md` now documents (`npx -y
@agentclientprotocol/codex-acp`).

**Conclusion, not an assumption:** the Codex adapter already present in that
stopped image is not the officially current one and is not reusable as the
qualified Codex candidate without itself being an unqualified, deprecated
artifact. Reusing the image's *pattern* (a private `/opt/acp-node` Node 22
runtime plus thin PATH-prepending wrapper scripts, so Claude/Codex/Gemini
coexist in one image without colliding) is sound and precedented by
OpenHands' own build; reusing its specific Codex *binary* is not. That
pattern is not what this candidate reuses either, for a narrower reason:
`../openhands-permission-extension/` and the already-qualified Claude
candidate are built as a single-provider, PermissionAgent-patched image per
provider, not an all-in-one agent-canvas image — mixing both patterns in one
step was judged a larger, unrelated change than this mandate's scope.

No file under `C:/Users/micha/Dev/openhands-credentials/` or
`C:/Users/micha/.openhands` was read, listed or mounted while producing this
comparison; only the image's own metadata and installed package versions
were inspected, with no network and no credential volume attached.

## Official subscription login sequence to qualify separately

`@agentclientprotocol/codex-acp` advertises three ACP auth methods at
`initialize`: `api-key` (never this one - it is the paid-API fallback the
mandate excludes), `chat-gpt` (the ChatGPT subscription login - this is the
one to use), and `chat-gpt-device-code` (same subscription login, remote-
terminal variant, only offered if the client negotiates URL elicitation).
Verified directly from the adapter's own source
(`src/CodexAuthMethod.ts`, `src/login.ts` at the pinned gitHead): the
package's own `codex-acp login` subcommand starts the bundled Codex App
Server, calls `account/read`, and if not already logged in calls
`account/login` with `type: "chatgpt"`, which returns a browser `authUrl`
to open and then waits for an `account/login/completed` event. This writes
through to the bundled Codex CLI's own credential store - never Hermes'
`~/.codex/auth.json`, never a copied or extracted token. Use a dedicated
private home volume for this runtime, exactly like the Claude candidate.
Do not set `CODEX_API_KEY` or `OPENAI_API_KEY` in that environment: either
makes the adapter silently able to answer with API-key billing instead of
the subscription method. Verify login succeeded by re-running the ACP
`initialize` handshake and confirming the account is no longer absent,
before any inference about readiness. No user account connection has been
performed by these files.

OpenHands can later invoke `acp_command=["/usr/local/bin/codex-acp"]` using
the qualified PermissionAgent, default session mode and the scoped policy.
This does not itself enforce provider tool sandboxing, usage budgets or
durable HQ approvals. Real provider execution remains a separate bounded
qualification, exactly as for Claude.

Primary evidence:
- https://registry.npmjs.org/@agentclientprotocol/codex-acp/2.1.1
- https://registry.npmjs.org/@openai/codex/0.159.3
- https://registry.npmjs.org/@openai/codex-linux-x64 (alias of `@openai/codex@0.159.3-linux-x64`)
- https://registry.npmjs.org/@zed-industries/codex-acp (deprecation notice, both `0.15.0` and `0.16.0`)
- https://raw.githubusercontent.com/agentclientprotocol/codex-acp/68d7d2d5ddfc0ed5746f9f6130892dda685e65dd/README.md
- https://raw.githubusercontent.com/agentclientprotocol/codex-acp/68d7d2d5ddfc0ed5746f9f6130892dda685e65dd/src/CodexAuthMethod.ts
- https://raw.githubusercontent.com/agentclientprotocol/codex-acp/68d7d2d5ddfc0ed5746f9f6130892dda685e65dd/src/login.ts
- https://raw.githubusercontent.com/agentclientprotocol/codex-acp/68d7d2d5ddfc0ed5746f9f6130892dda685e65dd/src/index.ts
- `docker image inspect ghcr.io/openhands/agent-canvas:1.0.0-rc.11` / `docker history --no-trunc` (local, this session)
