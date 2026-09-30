#!/bin/sh
set -eu
case "${1:-qualify_initialize.py}" in
  qualify_initialize.py|qualify_tools.py) script=${1:-qualify_initialize.py} ;;
  *) exit 64 ;;
esac
container_id=$(docker create --network none --read-only --cap-drop ALL \
  --security-opt no-new-privileges --pids-limit 128 --memory 1g --cpus 1 \
  --tmpfs /tmp:rw,nosuid,nodev,size=128m \
  --tmpfs /home/runner:rw,nosuid,nodev,size=32m,uid=10001,gid=10001 \
  --mount type=bind,src=/opt/oria-openhands-qualification/openhands-claude-runtime,dst=/qualification,readonly \
  --label oria.purpose=claude-acp-initialize \
  oria-openhands-claude:qualification1 "/qualification/$script")
cleanup() { docker rm -f "$container_id" >/dev/null 2>&1 || true; }
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
timeout --signal=TERM --kill-after=5s 30s docker start -a "$container_id"
