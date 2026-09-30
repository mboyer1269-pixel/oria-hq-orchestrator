#!/bin/sh
# Run only the reviewed no-provider qualification scripts. No persistent volumes.
set -eu
case "${1:-}" in
  qualify.py|qualify_conversation.py|qualify_permissions_conversation.py|qualify_cancellation.py) script=$1; deadline=90s ;;
  qualify_timeout.py) script=$1; deadline=3s ;;
  *) echo 'Unknown qualification script' >&2; exit 64 ;;
esac
test -f "/opt/oria-openhands-qualification/$script"
container_id=$(docker create --network none --read-only --cap-drop ALL \
  --env LITELLM_LOCAL_MODEL_COST_MAP=True \
  --security-opt no-new-privileges --pids-limit 128 --memory 1g --cpus 1 \
  --tmpfs /tmp:rw,nosuid,nodev,size=128m \
  --mount type=bind,src=/opt/oria-openhands-qualification,dst=/qualification,readonly \
  --label oria.purpose=openhands-qualification \
  oria-openhands-qualification:sdk1.50.0 "/qualification/$script")
# Stop and remove this exact newly created container, including on timeout.
cleanup() { docker rm -f "$container_id" >/dev/null 2>&1 || true; }
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
timeout --signal=TERM --kill-after=5s "$deadline" docker start -a "$container_id"
