# Provider execution: verified gaps and implementation order

## Current checkpoint — supersedes the historical status below

Source inspection on 2026-09-30 confirms that `container_job.create_job(provider=...)`
accepts a host-selected gateway, validates its live Docker identity and mounts its
Unix socket and verified relay. The job still has network `none`. The opt-in
`permission_worker` creates this gateway when a trusted `gateway_root` is supplied.
The connected synthetic worker/storage/Memex qualification is recorded in
`PROVIDER-STORAGE-QUALIFICATION.md`. Thus the older statements below that the
gateway lifecycle and mission wiring do not exist are historical, not current.

The operational entry point remains deliberately different: `run_host_job.py`
accepts `--gateway-root` only for read-only inspection, not execution. A passing
qualification harness does not activate the installed consumer.

Remaining critical path, in order:

1. Obtain the pending explicit account grant and verify official Claude login.
   Separately approve the prepared project-memory publication.
2. Qualify subscription credential storage and refresh in the actual pinned CLI.
   Current `create_job` has no account mount; login in its dedicated container
   does not authenticate mission containers. Do not copy an entire user home,
   place credentials in a dossier, or describe a read-only credential mount as
   protection against credential reads by agent tools.
3. Implement and review the chosen credential boundary; bind execution to the
   approved provider policy. Keep authentication material outside HQ records,
   repository files, reports and shared development memory.
4. Provision the governed project-scoped Memex read connection, then prepare a
   fresh mission snapshot and confirmation matching the final execution policy.
5. Activate one operator-controlled execution path with owner tool review; run
   one real coding mission and independently test/review its exact changes.
6. Exercise interruption/reconciliation before enabling unattended repetition.

No new account grant, credential transfer, service activation or model request
was performed by this checkpoint. No measured model performance claim follows
from the synthetic runs. The remaining sections preserve earlier decisions and
research; their time-specific deployment statements must not override this list.

Checked 2026-09-30 against current source and official documentation. This is a design checkpoint, not an implemented or activated provider profile.

## Actual current behavior

`container_job.py` always creates jobs with network none, a temporary `/home/runner`, checkout/results/dossier mounts and optionally the permission socket. It provides no Claude account volume or provider credential. `run_mission.py` launches the fixed Claude ACP adapter. Successful official login in the separate `oria-openhands-claude-login` container therefore cannot, by itself, make a dispatched job authenticated or online.

The private HQ bridge is a different component: it reads/writes canonical mission state through Supabase. It must never become the provider credential container or an agent workspace. Its successful discovery says nothing about provider reachability.

The permission worker exposes requests through the existing host callback and owner review path. Current staging tool-review flag0 prevents that UI path. Do not silently replace the callback with automatic approvals to obtain a passing model run. Actual permissions needed by the first coding task remain to be observed and reviewed.

## Decisions for implementation

1. Preserve the existing offline profile as the qualification baseline. Introduce an explicit operator-owned provider profile; do not simply replace network none with a general egress network.
2. Include the provider profile identity and policy fingerprint in the canonical launch binding shown for confirmation. A network/authentication/tool-policy change must invalidate old launch approval. Host-only paths and secrets must remain out of browser payloads and dossiers. The local launch schema now represents this fingerprint; installed VPS services have not yet been rebuilt with it.
3. Qualify the bundled native CLI through a controlled network route before attempting coding. Official Claude Code documentation supports HTTP/HTTPS proxy variables. A proxy setting alone does not enforce network isolation: direct connectivity must be restricted separately. No proxy is currently deployed for this job path.
4. Confirm the supported subscription credential storage and refresh behavior with the actual CLI. Do not claim that API credential injection automatically supports claude.ai subscription/OAuth traffic. Do not transfer Paperclip credentials or all user configuration into agent jobs. Any credential readable by the same user as agent commands remains exposed within that security boundary; a read-only mount prevents changes, not reads.
5. Inventory account-provided tools before enabling them. Official documentation says claude.ai MCP connectors are enabled by default and documents `ENABLE_CLAUDEAI_MCP_SERVERS=false` for disabling their fetch. Our first mission should use explicitly selected tools; the runtime must report which tools are actually available.
6. Qualify provider connectivity/authentication, exact-commit workspace, permission review and non-model tests independently, then execute the owner-confirmed mission. Keep process completion separate from independent validation and delivery.

## Required evidence before a real coding mission

- Exact profile fingerprint agrees between web preview, durable authority and host configuration; changes refuse old authority.
- Intended provider connection works; disallowed destination fails without relying solely on cooperative proxy environment variables.
- Real official account status is connected in the actual execution context; refresh/storage behavior is understood without printing token material.
- Scoped published Memex context is attached to the v2 dossier.
- A real tool request reaches owner review and is consumed once; refusal or unavailable review does not become approval.
- Work stays in isolated checkout; tests/review run on the resulting exact changes; unknown outcomes are reconciled before retry.

No provider network was opened, account credential mounted into a job, approval granted or model invoked by this review. Existing pending Claude consent and Memex publication approval remain necessary, but are not the only unfinished work.

## Local implementation checkpoint — provider binding

HQ now accepts an optional strict public `providerProfile` in its canonical launch configuration and includes it in the existing approval hash. The UI describes the requested policy and refuses confirmation of this currently unsupported profile. The local consumer refuses profile-bearing jobs before filesystem preparation; the worker independently refuses them after canonical reread, before sockets or Docker. Absence preserves the offline baseline. This code is not yet in the installed VPS runtime or staging images.

Protected manifest verification is now implemented locally and exercised against the real network candidate (see `PROVIDER-POLICY.md`). The consumer and worker reject missing or changed policies before effects. A verified policy still cannot execute: proxy lifecycle, account credential lifecycle and real provider execution remain unfinished. These changes are not installed in the active VPS runtime. Do not remove the host guards merely because HQ can parse the profile.

## Primary sources (research)

Subsequent isolated network qualification: `../openhands-provider-proxy/README.md` records real TLS allow/deny checks through a Unix socket while the agent remains network-none. This is not yet wired to the mission launcher, account credentials or host policy registry; the unsupported-profile guards remain.

- [Claude Code network configuration](https://code.claude.com/docs/en/network-config): proxy support, authentication endpoints, connector defaults and environment-setting limitations.
- [Secure deployment of agents](https://code.claude.com/docs/en/agent-sdk/secure-deployment): network/credential boundaries, Unix socket proxy pattern, distinction between sampling endpoint overrides and HTTPS CONNECT tunnels.

These documents establish available mechanisms, not compatibility proof for our pinned ACP/native CLI versions. No market comparison or performance superiority follows from this research.
