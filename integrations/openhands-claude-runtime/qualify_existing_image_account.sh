#!/bin/sh
# Isolated, temporary, read-only-credentials probe against the REAL stopped
# ghcr.io/openhands/agent-canvas:1.0.0-rc.11 image already present on this
# machine. Never starts the real entrypoint (tini -- entrypoint.sh) - that
# entrypoint starts an agent-server AND an automation server that read
# persisted state under ~/.openhands (conversations, automations.db); this
# script overrides the entrypoint with a plain shell probe instead (bind-
# mounted read-only, run via `sh`), so neither process ever starts and
# neither can resume a prior job. Mounts only the Claude credential
# directory, read-only; never .openhands (session/automation state), never
# the projects dir, never the Docker socket, never a write-mode mount of
# anything original. No model call, no billed API, no login prompt (auth
# status is a non-interactive read), no production/VPS touched.
set -eu
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
MSYS_NO_PATHCONV=1 docker run --rm \
  --network bridge --read-only --cap-drop ALL \
  --security-opt no-new-privileges --pids-limit 64 --memory 512m --cpus 1 \
  --tmpfs /tmp:rw,nosuid,nodev,size=64m \
  --tmpfs /tmp2:rw,nosuid,nodev,size=4m \
  --tmpfs /home/openhands:rw,nosuid,nodev,size=32m,uid=10001,gid=10001 \
  -v "C:/Users/micha/Dev/openhands-credentials/claude:/home/openhands/.claude:ro" \
  -v "$SCRIPT_DIR/qualify_existing_image_account_probe.sh:/probe/probe.sh:ro" \
  --label oria.purpose=existing-image-account-probe \
  --entrypoint sh \
  ghcr.io/openhands/agent-canvas:1.0.0-rc.11 \
  /probe/probe.sh
