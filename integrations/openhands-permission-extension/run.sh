#!/bin/sh
set -eu
case "${1:-qualify_instance_policies.py}" in
  qualify_instance_policies.py|qualify_callbacks.py) script=${1:-qualify_instance_policies.py} ;;
  *) exit 64 ;;
esac
container_id=$(docker create --network none --read-only --cap-drop ALL \
  --security-opt no-new-privileges --pids-limit 128 --memory 1g --cpus 1 \
  --tmpfs /tmp:rw,nosuid,nodev,size=128m \
  --label oria.purpose=openhands-permission-extension \
  --entrypoint python oria-openhands-qualification:permissions1 "/extension/$script")
cleanup() { docker rm -f "$container_id" >/dev/null 2>&1 || true; }
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
timeout --signal=TERM --kill-after=5s 60s docker start -a "$container_id"
