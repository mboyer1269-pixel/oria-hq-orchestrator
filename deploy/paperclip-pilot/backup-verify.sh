#!/usr/bin/env bash
# Source reads only. All restoration is into freshly created dedicated volumes.
# No rm/down/prune, no published port, no provider or Paperclip server execution.
set -euo pipefail
umask 077
cd /opt/oria-paperclip-pilot
for cmd in docker python3 openssl sha256sum cmp; do command -v "$cmd" >/dev/null; done
test -f compose.json
test -f .env
test "$(stat -c %a .env)" = 600 || { echo 'Private source .env must have mode 600.' >&2; exit 1; }

run_id="$(date -u +%Y%m%dT%H%M%SZ)-$(openssl rand -hex 4)"
prefix="oria-paperclip-restore-${run_id}"
backup_dir="/opt/oria-paperclip-pilot/backups/${run_id}"
mkdir -p "$backup_dir"
chmod 700 "$backup_dir"
# Recovery also needs the session secret and deployment config. Copy privately;
# these files are never echoed, sourced or included in stdout diagnostics.
cp -- .env "$backup_dir/pilot.env"
chmod 600 "$backup_dir/pilot.env"
cp -- compose.json paperclip.config.json source-review.json "$backup_dir/"
if test -f compose.providers.json; then cp -- compose.providers.json "$backup_dir/"; fi
if test -f /opt/oria-provider-runners/paperclip.networks.json; then
  cp -- /opt/oria-provider-runners/paperclip.networks.json "$backup_dir/"
fi

source_db=$(docker compose -f compose.json --env-file .env ps -q db)
source_app=$(docker compose -f compose.json --env-file .env ps --all -q paperclip)
[[ "$source_db" =~ ^[a-f0-9]{12,64}$ && "$source_app" =~ ^[a-f0-9]{12,64}$ ]] || { echo 'Source containers missing; no restore created.' >&2; exit 1; }
for container in "$source_db" "$source_app"; do
  test "$(docker inspect --format '{{index .Config.Labels "com.docker.compose.project"}}' "$container")" = oria-paperclip-pilot
done
test "$(docker inspect --format '{{.State.Running}}' "$source_app")" = false || {
  echo 'Refusing: stop the pilot app gracefully before taking the cross-store backup.' >&2
  exit 1
}
source_volume=$(docker inspect --format '{{range .Mounts}}{{if eq .Destination "/paperclip"}}{{if eq .Type "volume"}}{{.Name}}{{end}}{{end}}{{end}}' "$source_app")
test "$source_volume" = oria-paperclip-pilot_pilot-paperclip || { echo 'Unexpected source app volume; refusing.' >&2; exit 1; }
app_image=$(python3 -c 'import json; print(json.load(open("compose.json"))["services"]["paperclip"]["image"])')
db_image=$(python3 -c 'import json; print(json.load(open("compose.json"))["services"]["db"]["image"])')
[[ "$app_image" =~ ^ghcr.io/paperclipai/paperclip@sha256:[a-f0-9]{64}$ && "$db_image" =~ ^postgres@sha256:[a-f0-9]{64}$ ]] || { echo 'Expected reviewed digest pins.' >&2; exit 1; }
# Images must already be present; never pull during a backup verification.
docker image inspect "$app_image" >/dev/null
docker image inspect "$db_image" >/dev/null

verify_db="${prefix}-db"
verify_app="${prefix}-app"
verify_db_volume="${prefix}-db-data"
verify_app_volume="${prefix}-app-data"
archive_container="${prefix}-archive"
created_db=false
finish() {
  result=$?
  trap - EXIT
  # Stop only the verification DB this script successfully created. Keep all
  # containers, volumes, logs and backup files for explicit operator review.
  if [ "$created_db" = true ]; then docker stop --time 15 "$verify_db" >/dev/null 2>&1 || true; fi
  if [ "$result" -ne 0 ]; then echo "FAIL: artifacts retained privately at $backup_dir; source services untouched." >&2; fi
  exit "$result"
}
trap finish EXIT

# The metadata census contains table names/counts only, never row values.
# Compare before/after to detect obvious activity; this is NOT an atomic
# cross-store transaction. The app must remain stopped throughout capture.
cat > "$backup_dir/census.sql" <<'SQL'
BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY;
SELECT format('SELECT %L || '':'' || count(*) FROM %I.%I;', schemaname || '.' || tablename, schemaname, tablename)
FROM pg_tables WHERE schemaname NOT IN ('pg_catalog', 'information_schema') ORDER BY schemaname, tablename
\gexec
COMMIT;
SQL
docker exec -i "$source_db" psql -X -qAt -v ON_ERROR_STOP=1 -U paperclip_pilot -d paperclip_pilot < "$backup_dir/census.sql" > "$backup_dir/source-before.txt" 2> "$backup_dir/census-before.log"
docker exec "$source_db" pg_dump -U paperclip_pilot -d paperclip_pilot --format=custom --no-owner --no-acl > "$backup_dir/database.dump" 2> "$backup_dir/dump.log"
test -s "$backup_dir/database.dump"
docker exec -i "$source_db" psql -X -qAt -v ON_ERROR_STOP=1 -U paperclip_pilot -d paperclip_pilot < "$backup_dir/census.sql" > "$backup_dir/source-after.txt" 2> "$backup_dir/census-after.log"
cmp -s "$backup_dir/source-before.txt" "$backup_dir/source-after.txt" || { echo 'Source table counts changed; snapshot not accepted.' >&2; exit 1; }

docker run --pull=never --name "$archive_container" --network none --read-only --user node \
  --cap-drop ALL --security-opt no-new-privileges:true --memory 128m --cpus 0.25 --pids-limit 32 \
  --mount "type=volume,source=$source_volume,target=/paperclip,readonly" \
  --entrypoint /bin/tar "$app_image" -C /paperclip -cf - . > "$backup_dir/paperclip-volume.tar" 2> "$backup_dir/archive.log"
test -s "$backup_dir/paperclip-volume.tar"
test "$(docker inspect --format '{{.State.Running}}' "$source_app")" = false || {
  echo 'Source app restarted during capture; backup not accepted.' >&2; exit 1;
}
(cd "$backup_dir" && sha256sum database.dump paperclip-volume.tar > SHA256SUMS)

# Collision checks prevent docker volume create from silently reusing data.
for volume in "$verify_db_volume" "$verify_app_volume"; do
  if docker volume inspect "$volume" >/dev/null 2>&1; then echo 'Restore volume already exists; refusing reuse.' >&2; exit 1; fi
  docker volume create --label oria.purpose=paperclip-restore-verification --label "oria.restore-run=$run_id" "$volume" >/dev/null
done
for container in "$verify_db" "$verify_app"; do
  if docker container inspect "$container" >/dev/null 2>&1; then echo 'Restore container already exists; refusing reuse.' >&2; exit 1; fi
done
{
  printf 'POSTGRES_USER=paperclip_pilot\nPOSTGRES_DB=paperclip_pilot\nPOSTGRES_PASSWORD='
  openssl rand -hex 32
} > "$backup_dir/restore-db.env"
chmod 600 "$backup_dir/restore-db.env"
docker run -d --pull=never --name "$verify_db" --network none --read-only --user postgres \
  --cap-drop ALL --security-opt no-new-privileges:true --memory 512m --cpus 0.5 --pids-limit 128 \
  --tmpfs /tmp:rw,nosuid,nodev,size=64m --tmpfs /var/run/postgresql:rw,nosuid,nodev,size=16m,mode=1777 \
  --mount "type=volume,source=$verify_db_volume,target=/var/lib/postgresql/data" \
  --env-file "$backup_dir/restore-db.env" "$db_image" > "$backup_dir/restore-db.id"
created_db=true
ready=false
for attempt in $(seq 1 30); do
  if docker exec "$verify_db" pg_isready -U paperclip_pilot -d paperclip_pilot >/dev/null 2>&1; then ready=true; break; fi
  sleep 2
done
test "$ready" = true || { echo 'Restore database not ready; retained for review.' >&2; exit 1; }
docker exec -i "$verify_db" pg_restore --exit-on-error --single-transaction --no-owner --no-acl -U paperclip_pilot -d paperclip_pilot < "$backup_dir/database.dump" > "$backup_dir/restore.log" 2>&1
docker exec -i "$verify_db" psql -X -qAt -v ON_ERROR_STOP=1 -U paperclip_pilot -d paperclip_pilot < "$backup_dir/census.sql" > "$backup_dir/restored-census.txt" 2> "$backup_dir/restored-census.log"
cmp -s "$backup_dir/source-after.txt" "$backup_dir/restored-census.txt" || { echo 'Restored table counts differ; verification failed.' >&2; exit 1; }

docker run -i --pull=never --name "$verify_app" --network none --read-only --user node \
  --cap-drop ALL --security-opt no-new-privileges:true --memory 128m --cpus 0.25 --pids-limit 32 \
  --mount "type=volume,source=$verify_app_volume,target=/paperclip" \
  --entrypoint /bin/tar "$app_image" -C /paperclip --no-same-owner -xf - < "$backup_dir/paperclip-volume.tar" > "$backup_dir/restore-app.log" 2>&1
# Compare every archived member's contents/metadata against the restored tree,
# using GNU tar's compare mode, without listing names or key material.
docker run -i --pull=never --name "${prefix}-compare" --network none --read-only --user node \
  --cap-drop ALL --security-opt no-new-privileges:true --memory 128m --cpus 0.25 --pids-limit 32 \
  --mount "type=volume,source=$verify_app_volume,target=/paperclip,readonly" \
  --entrypoint /bin/tar "$app_image" -C /paperclip --compare -f - < "$backup_dir/paperclip-volume.tar" > "$backup_dir/compare.log" 2>&1
{
  printf 'run=%s\nsourceComposeProject=oria-paperclip-pilot\n' "$run_id"
  printf 'restoreDatabaseContainer=%s\nrestoreDatabaseVolume=%s\nrestoreAppVolume=%s\n' "$verify_db" "$verify_db_volume" "$verify_app_volume"
  printf 'databaseRestore=pass\ntableCounts=match\nappArchiveCompare=pass\nsourceAppStoppedAtCaptureBoundaries=true\n'
  printf 'applicationLoginAfterRestore=not-tested\nproviderCalls=none\n'
} > "$backup_dir/result.txt"
echo "PASS: isolated DB restore/counts and app-volume archive comparison; artifacts retained at $backup_dir."
echo 'No source service stopped or changed. Restored Paperclip server was not started; owner login/session recovery remains untested.'
