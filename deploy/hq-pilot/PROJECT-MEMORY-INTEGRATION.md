# Project-scoped ORIA HQ memory — pending human publication

Read-only VPS inventory showed only two synthetic pilot namespaces with one
entity each. There was no published ORIA HQ project memory to bind.

`propose-project-memory.mjs --submit` submitted the exact text in
PROJECT-MEMORY-FOUNDATION.md through the existing signed MCP proposal path, using
an in-memory 120-second handle limited to org:project:oria-hq. No signing key or
handle was copied to disk or printed. Existing signing material was not changed.
Stable authenticated requestId: oria-hq-project-foundation-v1.

Durable database read confirms proposal8b5d3617-cc14-43ab-b3ca-fcd62161a657,
status proposed, review_required1; project graph entities0. No publication or
human decision was forged. User approval question is pending.

Prepared artifacts, NOT activated:
- openhands-project-binding.json: one explicit workspace/project/namespace/anchor
  binding, TLS endpoint, read-handle file reference only.
- rotate-project-memory-read.py: trusted existing signer, exactly one namespace,
  read_only, fixed subject, bounded one-hour expiry, atomic replacement/fsync,
  root-owned non-writable directory, runtime UID1000 read access. No new signing key.
- test_rotate_project_memory_read.py: exact project accepted; workspace-wide,
  foreign/multi-project, write, wrong subject and bad expiry refused.

Before activation: obtain decision on exact proposal snapshot; use governed
review and common publication path; verify resulting anchor/content. Provision
the dedicated directory root:1000 mode0750 outside repositories and mint the
read handle. Mount its directory read-only in staging, add existing public CA
and private TLS network, pass the explicit project registry. Do not mount the
signing key or workspace-wide/operator credentials into HQ.

Configure supervised renewal before declaring durable availability. Withdrawing
the HQ binding stops new captures there; it does NOT immediately invalidate an
already-issued signed handle. Such a handle expires in at most one hour under
this renewal configuration. Immediate per-handle revocation is not claimed.

Then verify the browser's project selection and captured text, authorization of
the exact snapshot, foreign-project denial, and restart. These are outstanding;
the existing combined synthetic HTTP/database test is not a substitute for them.

## Renewal candidate and current state, 2026-09-30

A fresh read-only database inspection still reports the same proposal as
`proposed`, `review_required=1`, and zero entities in `org:project:oria-hq`.
No approval/publication has occurred.

Prepared `oria-hq-memex-project-read.service` and matching timer. They renew
every20minutes with a30second service timeout; issued handles remain limited
to one project, read_only and one-hour lifetime. The unit/timer remain staged
under qualification storage, not installed or enabled. They do not constitute
approval to publish or provision credentials.

Five tests passed on Linux in isolated temporary directories using synthetic
handles and a mocked signer. They cover exact scope/expiry rejection, atomic
replacement, UID1000 owner-only read permissions, removal of temporary files,
and preserving the previous handle when the signer fails or returns a broader
scope. These tests call no real signer and issue no credentials. systemd unit
syntax is checked separately; neither check proves durable renewal in production.

Activation order remains: human approval of exact proposal; governed publication
and anchor verification; protected directory and initial handle provisioning;
renewal installation; project-scoped staging connection; real capture and
foreign-project rejection. The current staging UI deliberately has no project
binding yet, and its legacy preparation must not be confirmed as an integrated
memory-backed execution.
