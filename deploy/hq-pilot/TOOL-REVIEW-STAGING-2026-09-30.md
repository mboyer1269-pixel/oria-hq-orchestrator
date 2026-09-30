# Tool review candidate — 2026-09-30

Canonical HQ source exported using development-snapshot.mjs: 1128 files, 302 test files. Every source file's size and SHA256 verified inside the development image. No runtime environment files exported.

- Manifest SHA256: `f33e8bdd0bd8e4c5354a7e06b0b536a39ea94722a66a5e123961523d19ce7d28`.
- Development image: `sha256:6736c006d5aa69899d830d5b3c4c0c61ca2c2bfb52efb02cca2f7a9aaea54946`.
- Standalone runtime: `sha256:0c7f7a4df9b62f7a2ff35589f6005a18ad9842d1d4bd89346959bff780826f1c`.
- Dependency manifests matched the existing qualified image byte-for-byte; no npm installation. Build network disabled. Only existing public browser Supabase settings passed at build time.

Validation: local typecheck, lint and smoke:joris exited 0; lint retains five preexisting warnings. Production build on VPS exited 0. Build log `/opt/oria-openhands-qualification/staging-build/build-review.log`. Docker emitted the existing ARG-without-default warning, not a failed build.

`start-openhands-staging.py --tool-review-candidate --image <digest>` starts a separate named candidate and refuses replacement. Container `oria-hq-tool-review-staging`, VPS loopback `127.0.0.1:3334`, UID1000, read-only root filesystem, zero operational mounts, capped CPU/RAM/pids/logs. Active HQ and older staging container were not replaced. No local SSH tunnel for 3334 created yet.

Uses existing HQ owner/Supabase configuration and database; all verification so far is read-only. Tool-review flag explicitly 0, no provider credentials or Memex handles copied, no agent execution. Health returned HTTP200; anonymous request to new tool-review route returned HTTP401.

Not yet verified: owner browser access to this candidate, enabled tool review backed by a protected control mount, real provider mission. These require further qualification; this candidate is not the completed product. Claude login handle 76315 was polled and remained live with no new output; OAuth consent still pending, not automatically granted.

## Owner browser follow-up

The existing owner session successfully opened `http://localhost:3334/hq/missions` in IAB tab17 through SSH tunnel handle97403. The page rendered its persisted Supabase mission and OpenHands preparation controls. No form submitted and no data mutation performed. A direct browser navigation to the tool API was blocked by the browser with `ERR_BLOCKED_BY_CLIENT`, leaving a blank tab, so authenticated API behavior is not claimed. That blank tab was closed; missions tab retained for continuing qualification.

Source inspection then found two configuration/governance omissions: the tool-review flag was absent from the central environment schema/template, and its decision-store writes were absent from the runtime capability inventory. Local canonical HQ source now declares the 0/1 flag, documents default0, and classifies the decision/consumption writes under an owner-confirmed internal-write capability, explicitly separate from tool execution. No runtime .env changed. These follow-up source edits are NOT included in the candidate image above. Configuration/inventory tests now pass70/70; updated global gates tracked in HQ output/playwright/review-config-*.log.
