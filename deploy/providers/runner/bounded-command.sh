#!/bin/sh
# Remote watchdog survives SSH hangup; child processes remaining in its group
# get TERM at the deadline, then KILL five seconds later. No foreground mode.
set -eu
deadline=${1:-}
case "$deadline" in ''|*[!0-9]*) echo 'Invalid remote deadline' >&2; exit 64;; esac
test "$deadline" -ge 1 && test "$deadline" -le 900 || exit 64
shift
test "$#" -gt 0 || exit 64
command -v timeout >/dev/null
# HUP alone must not destroy the watchdog while leaving its child running.
trap '' HUP
exec timeout --signal=TERM --kill-after=5s "${deadline}s" "$@"
