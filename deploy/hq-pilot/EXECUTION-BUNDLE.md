# Single execution configuration source

`execution-bundle.mjs` produces an **inactive candidate** for the private HQ bridge, host consumer and web launch configuration. It never installs files, copies credentials, contacts a model or starts a service.

Run with Node and the actual HQ source/dependencies:

```powershell
node deploy/hq-pilot/execution-bundle.mjs C:/Users/micha/Dev/Oria.HQ operator-input.json new-output-directory
```

Input has exactly `bridgeImage`, `webImage`, `projectId`, `sourceRoot`, and `profile`. Images must be immutable sha256 identities. `sourceRoot` is a canonical absolute Linux directory for the operator-owned Git source. `profile` has `{context:{workspaceId,actorId,runnerId},config}` and is validated by the actual HQ `pendingLaunchProfileSchema`, including the launch schema, budget limits and matching runner identities. Use the same qualified HQ source as the deployed images. The generator does not prove image provenance, source existence or profile ownership; those are deployment checks.

Outputs:

- `profile.json`: intended for `/var/lib/oria-hq/host-config/profile.json`.
- `consumer.json`: intended for `/etc/oria-hq/consumer.json`.
- `project-sources.json`: intended for `/etc/oria-hq/project-sources.json`.
- `hq.execution.overlay.json`: HQ image and the exact same serialized launch config; launch, confirmation and tool review remain disabled.
- `bridge.compose.json`: opt-in `execution-bridge` service with no published port, Docker socket, source workspace or provider credential mounts. Its only mount is the protected host configuration directory, read-only. Main process UID1000; private operator CLI executes explicitly as root.
- `manifest.json`: generated-file hashes and `activated:false`.

The output directory is exclusive. Existing output is refused, including after a partial write. POSIX files are created0600 in a0700 directory; Windows modes do not establish Linux protection. Installation must establish root ownership, protected ancestors and correct file modes. Never point an agent at this directory.

The separately provisioned `/etc/oria-hq/bridge-runtime.env` is deliberately not generated. It must contain only required HQ owner/persistence boot configuration; do not copy all provider or application secrets. Bridge egress uses the existing HQ network; this is not a new network allowlist. Memex publication, read-handle provisioning, TLS and web connection mounts remain separate governed prerequisites. Preserve the existing Memex overlay when eventually applying the HQ overlay. No flag should be enabled merely because generation succeeds.

## Evidence, 2026-09-30

Three tests passed against the real local HQ schema: shared config and mount mapping; rejection of mismatched runner/policy/budget/credential fields; rejection of floating image identities, ambiguous source paths and Compose interpolation. A synthetic qualification-only input generated six files. VPS Docker Compose accepted the bridge model using `--no-env-resolution --quiet`; no credentials were read and no services started. The fixture does not name the real owner/project and must never be installed as production configuration.

Remaining: verified real operator/project binding, protected deployment files, authenticated owner flow, pending Claude consent and governed project memory publication, then a successful independently reviewed coding mission. Current production is unchanged.

## Inactive real-source candidate

Prepared on VPS under `/opt/oria-openhands-qualification/operator-bundle-6225d49c/bundle`. Owner identity was read from the active HQ configuration and validated as a UUID; no credentials were copied or displayed. Workspace/project use the existing `michael-hq` / `oria-hq` memory binding. New proposed runner identity: `oria-hq-openhands-claude`. These bindings are not proof of authenticated owner access or an activated runner.

Source `/opt/oria-openhands-qualification/hq-git-source-6225d49c` is a new isolated Git baseline, commit `d4a37f9a3c85615e03cca89b5c47de094581594c`, made from 1137 manifest-verified exported files. It has no remote. No original repository history was modified or pushed. The previous export directory was not a Git repository and could not satisfy exact-commit preparation.

The actual runner `prepare_workspace` successfully created a clean detached copy under `operator-source-checkouts/baseline-6225d49c`. A strict initial raw-byte comparison failed on line endings. All 1137 files were subsequently checked against original export hashes, Git blobs and explicit repository attributes: 76 differ from the export only through CRLF-to-LF normalization; PowerShell files retain their declared CRLF checkout convention. No other difference was accepted. Checkout manifest SHA256: `4e0fee31254b38b3e54957001e6fdac9ec1882495d6694445dae28098f20f559`, stored at `/opt/oria-openhands-qualification/operator-checkout-manifest.json`.

Candidate budgets: 100 cents, 20000 requested tokens, 20 iterations, 600 seconds. Hard token enforcement remains explicitly false. Launch/confirmation/tool review flags remain0; this deny-policy runner does not yet provide a usable authenticated coding mission. The files were generated using the coherent source image's canonical validation and accepted by Docker Compose without environment resolution. They remain in qualification storage, not installed under `/etc` or activated by systemd.

## Protected files installed, service inactive

Subsequent step: verified release `b901ffbafc700003b9054a6908fa0764baffd2bd023276366fa7c59d7ff2f110` (archive SHA256 `666ef36e3d17081b68a14c441f51dc5d867c5d56a1a12b04560f32ae48e04796`) was transferred, checked and installed at `/opt/oria-hq-runner`, files0444. Protected consumer/source-registry files are now at `/etc/oria-hq` and profile at `/var/lib/oria-hq/host-config/profile.json`, files0600. The installer refused existing target roots, validated every source hash before writing and used exclusive file creation. Actual `load_config` and source-registry validation passed. The service unit is only a file in the runtime package: it was not installed into systemd or started. Control directory `/run/oria-hq-control` exists but remains volatile across reboot.

The exact discovery CLI was then run in a disposable read-only container against the existing HQ database using the installed profile. It returned `ready`, zero scanned/queued/rejected launches, exit0. Only the five existing owner/Supabase boot variables were passed privately by environment; no provider credential, environment file or public port was added. The container was removed afterward. This was a read-only service-role query, not user-session authentication or an RLS test. No consumer/model/mission mutation was invoked. Sanitized result: `/opt/oria-openhands-qualification/real-discovery-result.json`.

Persistent bridge startup and its credential provisioning remain undone. Do not enable the consumer until the complete owner-confirmed mission path, memory binding and provider connection have been qualified.

## Private bridge running, consumer still inactive

Subsequent step: `hq-host-bridge` was created from the pinned source image and started with an idle Node process, UID1000, read-only root, capabilities dropped, no new privileges, 512MiB limit, no ports or Docker socket, and only the protected configuration root mounted read-only. Restart policy is `no`; reboot/service recovery is not claimed. Startup refuses an existing container rather than replacing it.

The five existing HQ owner/Supabase settings were passed privately through the subprocess environment, not command-line values. They are retained in the bridge container configuration under normal Docker administrator access. No new environment file or provider credential was created. The Compose candidate still references an unprovisioned runtime environment file; it is not yet the reproducible startup path for this running container. The reviewed startup script is `/opt/oria-openhands-qualification/start_private_bridge.py`.

The installed host module's `load_config` + `discover` succeeded against this exact running bridge: `ready`, zero pending jobs. Calling discovery under the container's defaultUID1000 was refused with exit2 as intended; private operator exec uses root. The mission consumer was not invoked, and its systemd unit remains not-found. Sanitized result: `private-bridge-result.json` in qualification storage.

A single idle resource observation reported CPU0.00%, 7.637MiB memory, seven PIDs. This is an instantaneous footprint, not throughput or a before/after performance result. The dedicated Claude container was separately queried through its bundled native CLI at `/opt/claude-acp/node_modules/@anthropic-ai/claude-agent-sdk-linux-x64/claude`: auth status exit1, loggedInfalse, authMethodnone. No authorization or model request occurred.
