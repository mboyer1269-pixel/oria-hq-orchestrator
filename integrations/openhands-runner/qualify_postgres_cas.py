"""Actual PostgreSQL CAS semantics in an isolated disposable database, no HQ data."""
import concurrent.futures
import json
import subprocess
import time

IMAGE = "sha256:b0f9560a2de083e2cc7382e75f808c7381a32852a7ec49117deedb300e552b24"


def command(*args, input=None, check=True):
    return subprocess.run(["docker", *args], input=input, capture_output=True,
                          text=True, check=check, timeout=20)


def main():
    cid = command("create", "--network", "none", "--read-only", "--user", "postgres",
                  "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
                  "--memory", "256m", "--cpus", "0.5", "--pids-limit", "128",
                  "--tmpfs", "/tmp:rw,nosuid,nodev,size=192m,mode=1777",
                  "--tmpfs", "/var/run/postgresql:rw,nosuid,nodev,size=8m,mode=1777",
                  "--env", "PGDATA=/tmp/pgdata", "--env", "POSTGRES_HOST_AUTH_METHOD=trust",
                  "--label", "oria.purpose=postgres-cas-qualification", IMAGE).stdout.strip()
    try:
        command("start", cid)
        deadline = time.monotonic() + 15
        # TCP readiness excludes the entrypoint's temporary socket-only init server.
        while command("exec", cid, "pg_isready", "-h", "127.0.0.1", "-U", "postgres", check=False).returncode:
            if time.monotonic() >= deadline:
                raise RuntimeError("Disposable PostgreSQL did not become ready")
            time.sleep(.25)

        def sql(statement):
            return command("exec", "-i", cid, "psql", "-h", "127.0.0.1", "-U", "postgres", "-X", "-qAt",
                           "-v", "ON_ERROR_STOP=1", input=statement).stdout.strip()

        sql("""CREATE TABLE missions(id text PRIMARY KEY, workspace_id text,
          status text, updated_at timestamptz, input jsonb);
          INSERT INTO missions VALUES('m','w','draft','2026-09-30T00:00:00Z','{"objective":"fixture"}');""")
        def claim(value):
            # Fixed synthetic constants, no external input interpolated into SQL.
            return sql("""UPDATE missions SET input=jsonb_set(input,'{launch}',to_jsonb('%s'::text)),
              updated_at=clock_timestamp() WHERE id='m' AND workspace_id='w' AND status='draft'
              AND updated_at='2026-09-30T00:00:00Z'::timestamptz
              AND input='{"objective":"fixture"}'::jsonb RETURNING id;""" % value)
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(claim, ("first", "second")))
        if outcomes.count("m") != 1 or outcomes.count("") != 1:
            raise RuntimeError("CAS did not yield exactly one winner")
        if claim("repeat"):
            raise RuntimeError("Old version allowed another claim")
        if sql("UPDATE missions SET status='running' WHERE id='m' AND workspace_id='foreign' RETURNING id;"):
            raise RuntimeError("Foreign workspace predicate matched")
        print(json.dumps({"postgresVersion": sql("SHOW server_version;"),
                          "concurrentCasWinners": 1, "staleRetryRejected": True,
                          "foreignWorkspaceRejected": True, "postgrestQualified": False,
                          "productionDatabaseUsed": False, "modelCalled": False}))
    finally:
        command("rm", "-f", cid)


if __name__ == "__main__":
    main()
