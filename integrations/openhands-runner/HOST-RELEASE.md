# Host release candidate, 2026-09-30

Historical candidate below: current source documentation and consumer example now explicitly select root for private bridge CLI execution. Rebuild and verify a new release before installing; the recorded archive remains immutable and does not contain that correction.

Release ID: `97805964c62f17a53ce9d367c9bbceaf819ae71728c1b49c847a6af2b951268f`.

Archive SHA256: `1c933aaede0d3f540179d449571fff78076a53c6d141f97a1249507fda1a8ea6`.

The package contains 20 explicitly selected host runtime/documentation/service files plus a hash manifest. It excludes accounts, credentials, local environments, tests, agent images and HQ server source. The build uses fixed archive metadata and refuses unpublished local Python dependencies. Reproducibility and exclusion of an extra `.env` sentinel are tested. No dependency installation is performed by this package.

The archive was transferred and its archive/member/manifest hashes verified before files were materialized read-only under `/opt/oria-openhands-qualification/releases/<release-id>`. Its Python entry point imports successfully and prints help with bytecode writes disabled. This is a staged candidate, not the activated production installation.

The unit now declares RuntimeDirectory=oria-hq-control, mode0755 and Preserve=yes. systemd creates the control directory when starting; service stop retains it for reconciliation. `/run` remains volatile across reboot: durable per-launch host configurations and canonical HQ claims remain authoritative. This declaration does not claim reboot recovery is implemented.

The real transient systemd qualification verified creation/mode and retention after stop of an isolated equivalent runtime directory. It again passed failed-job visibility, restart without replay, duplicate-consumer refusal and graceful idle stop; six ledger records survived PostgreSQL restart. The agent still stops at missing Claude authentication. No successful model mission, production deployment or account connection is implied.

Installation dependencies still unresolved: current coherent HQ/bridge artifact containing the discovery and lifecycle scripts, protected database environment, actual owner/runner profile and project source mappings, enabled authenticated UI path, project memory publication/read handle, and provider network/authentication profile. Prepare those concrete bindings before copying the unit into systemd or starting a durable production consumer.
