# OpenHands candidate: actual browser and image evidence

## Observed deployment gap

The authenticated owner browser at localhost:3321/hq/missions shows the persisted
development mission, Supabase as its source, and disabled Paperclip transfer.
No OpenHands preparation control is visible. The VPS still runs HQ image
039c64a460dc (the documented v13). Local tests of newer code do not prove this
running UI exposes it. Do not announce an integrated OpenHands mission yet.

## Current development image

Source export: 1112 files; 131 inventory entries excluded by the existing
development snapshot exporter. Manifest SHA256:
191F200B5FA0C9C0228ACDC6B4F2D07015589FCA1D2D5D33D1164856E3D1E6F8.

VPS snapshot directory:
`/opt/oria-openhands-qualification/hq-development-openhands-20260930`.

Docker inspect reports candidate image ID:
`sha256:32f6f90cc1ab149069e4436e0ea025cb07f8730be6b1581677dcb76e7a16be85`.
This is a development/validation image, not a production release. Nothing was
deployed to the active application.

`Development.cached.Dockerfile` copies only node_modules from the previously
qualified dependency image. Both package.json and package-lock.json must match
byte for byte before copying. Its sibling dockerignore deliberately includes
tests, documentation and smoke scripts, unlike the production filter.

Dependency image inspected before use:
`sha256:6f12fcb9e41d8e401ec4d934dc15cc75327693c721300c120f6fc8f7cff23a85`.
The build used a local alias containing this full ID; BuildKit resolved the same
ID in its output. Tags themselves are mutable. Pass DEPENDENCY_IMAGE explicitly.
Build RUN network disabled; no npm install/download occurred in the successful
build. This avoids dependency reinstall, not all image-copy/export costs.

Qualification evidence:
- All 1112 source files verified inside image against manifest bytes and SHA256;
  298 .test.mjs files included.
- Targeted server/missions/openhands*.test.mjs: 44 passed, 0 failed, 2 skipped.
  Skips are real Memex-handler and signed-HTTP lifecycle tests requiring the
  separate Memex checkout. Prior separate evidence is not a pass in this image.
- npm run typecheck exits 0 in network-isolated disposable container.
- No provider call, production database write or active application replacement.

Intermediate failures retained honestly: the first standard build would reinstall
dependencies without network and was interrupted; a raw sha256 image ID in FROM
was treated as a registry reference, so the resolved local alias was used instead.
The first qualification script contained CRLF in its shell command, making npm
look for `typecheck\r`; corrected LF script then passed typecheck. Tests had already
passed and were not repeated solely for that shell formatting error.

Logs on VPS: qualify-current-hq.log (tests and shell error),
qualify-current-hq-typecheck.log (successful correction).
This is not a new claim of full lint/build/smoke or browser lifecycle validation.

## Account and next integration gates

Previous Claude code exchange returned HTTP400 and login process exited1. Cause
unproven. Restarted that stopped dedicated login container once, creating a fresh
official flow. New process remains waiting for user consent; no second parallel
login. Do not save authorization codes, OAuth state or token material in this file.

Next: complete official account connection, then use the current candidate in a
separate staging environment with explicit project-scoped Memex binding. Validate
the actual browser prepare/confirm flow against durable stores. The launch bridge
and a real model-driven edit/review/recovery cycle remain incomplete. A prepared
dossier, a passing script or a logged-in account is not an executed mission.
