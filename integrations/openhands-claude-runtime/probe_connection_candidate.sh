#!/bin/sh
# Temporary, isolated diagnostic probe against the locally built candidate
# image (oria-openhands-claude-runtime:candidate1). Mandate:
# docs/CLAUDE-BUILD-CANDIDAT-CONNEXION.md.
#
# Safety, by construction, not by promise:
#   - --network none: no model/API call is even reachable, billed or not.
#   - --read-only root fs, --cap-drop ALL, --security-opt no-new-privileges,
#     bounded --pids-limit/--memory/--cpus.
#   - The ONLY real-data mount is the existing Claude credentials directory,
#     read-only. Never .openhands (session/automation state), never the
#     projects dir, never the Docker socket - so no service that could
#     resume a job ever starts, and this process could not reach one even
#     if it tried.
#   - Entrypoint is explicitly python running ONLY the redacted classifier
#     script below (bind-mounted read-only from this repo), never the
#     image's own default command with other arguments.
#   - --rm: nothing persists after this single run.
set -eu

CREDENTIALS_SRC="${1:-/c/Users/micha/Dev/openhands-credentials/claude}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ ! -f "$SCRIPT_DIR/qualify_connection_account.py" ]; then
  echo "qualify_connection_account.py not found next to this script" >&2
  exit 64
fi
if [ ! -d "$CREDENTIALS_SRC" ]; then
  echo "credentials directory not found: $CREDENTIALS_SRC" >&2
  exit 64
fi

container_id=$(docker create --network none --read-only --cap-drop ALL \
  --security-opt no-new-privileges --pids-limit 128 --memory 512m --cpus 1 \
  --tmpfs /tmp:rw,nosuid,nodev,size=64m \
  --tmpfs /home/runner:rw,nosuid,nodev,size=32m,uid=10001,gid=10001 \
  --mount "type=bind,src=$CREDENTIALS_SRC,dst=/home/runner/.claude,readonly" \
  --mount "type=bind,src=$SCRIPT_DIR/qualify_connection_account.py,dst=/workspace/qualify_connection_account.py,readonly" \
  --label oria.purpose=openhands-claude-runtime-candidate-connection-probe \
  --entrypoint python \
  oria-openhands-claude-runtime:candidate1 /workspace/qualify_connection_account.py)

cleanup() { docker rm -f "$container_id" >/dev/null 2>&1 || true; }
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

set +e
timeout --signal=TERM --kill-after=5s 30s docker start -a "$container_id"
probe_exit=$?
set -e

echo "probe_exit_code=$probe_exit" >&2
exit "$probe_exit"
