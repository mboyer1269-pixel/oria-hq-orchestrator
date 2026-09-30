#!/bin/sh
# Operator-only action. Not invoked by Compose, build, or application startup.
set -eu
umask 077
if [ "$#" -ne 1 ]; then echo 'Usage: provision-certificates.sh /absolute/new-private-directory' >&2; exit 2; fi
case "$1" in /*) ;; *) echo 'Absolute path required' >&2; exit 2;; esac
if [ -e "$1" ]; then echo 'Refusing existing destination' >&2; exit 2; fi
command -v openssl >/dev/null
mkdir -m 700 -- "$1"
cd -- "$1"
openssl req -x509 -newkey rsa:3072 -nodes -sha256 -days 365 \
  -keyout ca.key -out ca.crt -subj '/CN=Oria Memex Private CA' \
  -addext 'basicConstraints=critical,CA:TRUE,pathlen:0' -addext 'keyUsage=critical,keyCertSign,cRLSign' 2>/dev/null
openssl req -new -newkey rsa:3072 -nodes -keyout server.key -out server.csr -subj '/CN=memex-tls' 2>/dev/null
printf '%s\n' 'subjectAltName=DNS:memex-tls' 'basicConstraints=critical,CA:FALSE' 'keyUsage=critical,digitalSignature,keyEncipherment' 'extendedKeyUsage=serverAuth' > server.ext
openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out server.crt -days 90 -sha256 -extfile server.ext 2>/dev/null
openssl verify -CAfile ca.crt -verify_hostname memex-tls server.crt
chmod 400 ca.key server.key
chmod 444 ca.crt server.crt
# Linux Docker bind secrets preserve host ownership. Only leaf key is assigned
# to the runtime UID. The CA signing key remains operator-owned and unmounted.
chown 1000:1000 server.key
printf '%s\n' 'Certificates prepared. Deploy separately after review; keep ca.key offline.'
