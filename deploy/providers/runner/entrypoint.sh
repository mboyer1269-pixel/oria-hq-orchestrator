#!/bin/sh
set -eu
umask 077
test "$(id -u)" = 1000 || { echo 'Runner requires uid 1000' >&2; exit 1; }
test -s /etc/oria-runner/authorized_keys || { echo 'Missing provider-specific authorized public key' >&2; exit 1; }
for directory in /paperclip /workspace /var/lib/oria-ssh; do
  test -w "$directory" || { echo "Runner volume is not writable: $directory" >&2; exit 1; }
done
key=/var/lib/oria-ssh/ssh_host_ed25519_key
if [ ! -f "$key" ]; then
  ssh-keygen -q -t ed25519 -N '' -f "$key"
fi
chmod 600 "$key"
/usr/sbin/sshd -t -f /etc/oria-runner/sshd_config
exec /usr/sbin/sshd -D -e -f /etc/oria-runner/sshd_config
