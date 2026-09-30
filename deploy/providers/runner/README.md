# Isolated provider SSH runners

One shared derived image reuses the exact official Paperclip pilot base digest. Root verified its official build attestation against source `29c8fb0b66cb01167f71e7107a89628e36b5e032`. Only OpenSSH server is added. No provider credentials, client private keys, homes or workspaces enter the build context. OS packages come from Debian at build time; record the resulting image digest before promoting it.

Gemini CLI 0.61.0 is already in this base. Cursor is mounted read-only from the reviewed standalone distribution; it is not downloaded or installed by this Dockerfile. The reviewed staging directory is `/opt/oria-provider-staging/cursor-2026.09.28-64d2043/dist-package`. Parent verified its version in the base image; archive SHA256 was locally recorded, not vendor-published.

## Storage and networking

- Gemini uses existing external volume `oria-gemini-home` at `/paperclip`. Google rejected the Gemini CLI login as an unsupported client; provider authentication is blocked. Do not recreate or erase it.
- Cursor uses existing external volume `oria-cursor-home` at `/paperclip`.
- Each provider has its own workspace and SSH host-key volumes. Neither gets Paperclip's server home, database environment or Docker socket.
- Each runner listens privately on port 2222. No host ports are published. A dedicated internal control network connects each provider to Paperclip; each provider also has its own outbound bridge for provider HTTPS access. Egress is **not** an allowlist.
- Runtime is uid/gid 1000, root filesystem read-only, all capabilities dropped, privilege escalation disabled, with CPU/RAM/PID limits. Writable mounts are the provider's home/workspace/host keys and bounded `/tmp`.
- SSH permits only node public-key authentication; passwords, root, forwarding, agent forwarding, user rc, PTY and tunnels are disabled. Interactive provider login can use an operator's separate Docker exec; Paperclip's command/tar transport does not require PTY or forwarding.

## Operator preparation (reference commands)

Provision a different SSH client keypair for each provider, outside this repository. Mount only its public authorized_keys file into the corresponding runner. Keep private keys solely in Paperclip's environment secret store. Set these variables on the Docker host:

- `GEMINI_AUTHORIZED_KEYS_FILE`: absolute path to Gemini's public authorized_keys file.
- `CURSOR_AUTHORIZED_KEYS_FILE`: absolute path to Cursor's public authorized_keys file.
- `CURSOR_DIST_PATH`: absolute path to the verified Cursor dist-package directory above.

The key files must be readable by uid1000 through Docker configs and not writable by that user. Existing home volumes must be writable by uid1000. New named volumes inherit owner from image mountpoints. No automatic chmod/chown of an existing login volume is performed.

From repository root, after those variables are set:

```sh
node deploy/providers/runner/validate.mjs
docker compose -f deploy/providers/runner/compose.json config --quiet
docker compose -f deploy/providers/runner/compose.json build gemini-runner
docker compose -f deploy/providers/runner/compose.json up -d --no-build gemini-runner cursor-runner
```

Both services use the same locally built image tag. These build/start commands are prepared instructions, not a claim that the image has been built or run. Nonroot sshd follows the upstream fixture approach but must pass actual authentication under these capability restrictions before enabling an agent.

After start, obtain each host public key through the trusted Docker operator channel (not an unauthenticated network scan):

```sh
docker compose -f deploy/providers/runner/compose.json exec -T gemini-runner cat /var/lib/oria-ssh/ssh_host_ed25519_key.pub
docker compose -f deploy/providers/runner/compose.json exec -T cursor-runner cat /var/lib/oria-ssh/ssh_host_ed25519_key.pub
```

Create known_hosts content `[gemini-runner]:2222 <returned public key>` and `[cursor-runner]:2222 <returned public key>` respectively; retain exact host keys across recreation. Replacing a host-key volume requires an intentional new trust check.

Merge `paperclip.networks.json` with the pilot compose when ready to attach Paperclip to the control networks. It changes only Paperclip networks; the database stays on pilot-internal. First validate the combined config with the pilot's existing environment. The runner networks must already exist. Do not mount provider homes into the Paperclip server.

## Verified Paperclip contract

The pinned `server/src/services/environment-config.ts` SSH schema uses `host`, `port`, `username`, `remoteWorkspacePath`, `privateKeySecretRef`, `knownHosts`, and `strictHostKeyChecking`. Use host `gemini-runner` or `cursor-runner`, port2222, username`node`, workspace`/workspace`, strict checking`true`, and the matching Paperclip secret reference. The private key is **content**, not a filesystem path, after server secret resolution. The adapter-facing spec additionally carries `remoteCwd`; do not invent this as a different authentication mechanism.

`packages/adapter-utils/src/ssh.ts` writes private key and known_hosts content to temporary mode0600 files; it uses BatchMode and strict host checking. Remote execution needs sh, env, git, tar, mkdir and the provider command on PATH. The helper sources /etc/profile and user login profiles. `/etc/profile.d/oria-runner-path.sh` and sshd SetEnv expose `/opt/cursor`, `/paperclip/.local/bin` and the globally installed CLIs. No SSH forwarding is used by this helper.

Source references at the attested revision:
- https://github.com/paperclipai/paperclip/blob/29c8fb0b66cb01167f71e7107a89628e36b5e032/packages/adapter-utils/src/ssh.ts
- https://github.com/paperclipai/paperclip/blob/29c8fb0b66cb01167f71e7107a89628e36b5e032/server/src/services/environment-config.ts

## Required runtime acceptance

Before dispatching jobs, verify nonroot public-key auth and strict host-key rejection, `id -u`=1000, HOME=/paperclip, `gemini --version`, `/opt/cursor/cursor-agent --version`, provider login, write to /workspace, read-only root, no access to the other provider home or database network, and a synthetic tar/workspace round-trip. SSH login success alone does not validate subscription billing, quotas, remote API callbacks or app-building workflows. Each provider can access its own credentials: this is provider isolation, not sandboxing untrusted work from its own login.

## Verified pilot status (2026-09-29)

The root operator built and deployed both runners; both are healthy. Actual strict SSH checks passed for uid1000, HOME=/paperclip, absence of DATABASE_URL and BETTER_AUTH_SECRET, and a non-writable /usr. Unknown host keys were rejected with StrictHostKeyChecking=yes and an empty known-hosts file. A tar-stream workspace canary roundtrip passed on both runners. These are transport tests, not yet a Paperclip-native helper run or a negative database-network connectivity test.

Cursor login succeeded; a provider task smoke test remains pending. Gemini login was rejected by Google as an unsupported client. Neither health nor SSH transport proves provider task execution.
