#!/bin/bash
set -euo pipefail
test ! -e /ipc/provider.sock
/usr/sbin/squid -k parse -f /etc/squid/squid.conf
/usr/sbin/squid -N -f /etc/squid/squid.conf &
squid_pid=$!
/usr/bin/socat UNIX-LISTEN:/ipc/provider.sock,fork,mode=0600 TCP:127.0.0.1:3128 &
relay_pid=$!
cleanup() { kill "$squid_pid" "$relay_pid" 2>/dev/null || true; wait "$squid_pid" "$relay_pid" 2>/dev/null || true; }
trap cleanup EXIT
trap 'exit 143' TERM INT
# Losing either process closes the service; no restart hides an uncertain state.
wait -n "$squid_pid" "$relay_pid"
exit 1
