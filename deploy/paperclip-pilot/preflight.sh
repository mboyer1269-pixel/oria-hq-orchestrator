#!/bin/sh
# Authored deployment preparation checks. Never starts/pulls/builds a container.
set -eu
cd "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
command -v docker >/dev/null
command -v node >/dev/null
node check-static.mjs
test -f .env || { echo 'Missing private .env; create it from .env.example without printing secrets.' >&2; exit 1; }
test "$(stat -c %a .env)" = 600 || { echo '.env permissions must be 600.' >&2; exit 1; }
# Validate values without sourcing an executable shell file or displaying values.
node --input-type=module -e '
import {readFileSync} from "node:fs";
const entries = new Map(readFileSync(".env", "utf8").split(/\r?\n/).filter(l => l && !l.startsWith("#")).map(l => {const i=l.indexOf("=");if(i<1)throw Error("Invalid env line");return [l.slice(0,i),l.slice(i+1)];}));
for(const key of ["PILOT_DB_PASSWORD","PILOT_AUTH_SECRET"]) if(!/^[a-f0-9]{64}$/.test(entries.get(key)||""))throw Error(key+" must contain 64 lowercase random hex characters");
if(entries.get("PILOT_DB_PASSWORD")===entries.get("PILOT_AUTH_SECRET"))throw Error("Use independent secrets");
for(const key of ["PILOT_DISABLE_SIGN_UP","PILOT_MIGRATION_AUTO_APPLY"])if(!["true","false"].includes(entries.get(key)))throw Error("Missing boolean "+key);
console.log("PASS: private env shape (values not displayed)");'
docker compose -f compose.json --env-file .env config --quiet
echo 'PASS: preflight only. No host port is published. Review free RAM/disk and owner bootstrap before starting.'
