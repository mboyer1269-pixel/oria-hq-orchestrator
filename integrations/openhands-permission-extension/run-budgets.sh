#!/bin/sh
set -eu
container_id=$(docker create --network none --read-only --cap-drop ALL \
  --security-opt no-new-privileges --pids-limit 128 --memory 1g --cpus 1 \
  --tmpfs /tmp:rw,nosuid,nodev,size=128m \
  --tmpfs /home/runner:rw,nosuid,nodev,size=32m,uid=10001,gid=10001 \
  --label oria.purpose=openhands-budget-qualification \
  oria-openhands-claude:budgets1)
cleanup() { docker rm -f "$container_id" >/dev/null 2>&1 || true; }
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
timeout --signal=TERM --kill-after=5s 60s docker start -a "$container_id"
