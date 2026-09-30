// Run inside the deployed HQ container. Reads zero application rows and writes nothing.
import { pathToFileURL } from 'node:url';

export async function checkDependencies(env, fetcher = fetch) {
  let origin;
  try {
    origin = new URL(env.NEXT_PUBLIC_SUPABASE_URL);
    if (origin.protocol !== 'https:' || origin.username || origin.password || origin.search || origin.hash) throw Error();
    if (!env.NEXT_PUBLIC_SUPABASE_ANON_KEY || !env.SUPABASE_SERVICE_ROLE_KEY) throw Error();
  } catch { return { ready: false, checks: [{ dependency: 'configuration', status: 'invalid' }] }; }
  const checks = [];
  for (const [dependency, pathname, key, columns] of [
    ['supabase_auth', '/auth/v1/health', env.NEXT_PUBLIC_SUPABASE_ANON_KEY],
    ['missions_schema', '/rest/v1/missions', env.SUPABASE_SERVICE_ROLE_KEY, 'id,workspace_id,mode_id,title,objective,expected_output,status,input,updated_at'],
    ['ledger_schema', '/rest/v1/action_ledger', env.SUPABASE_SERVICE_ROLE_KEY, 'id,user_id,action_type,event_type,summary,autonomy_level,requires_confirmation,model_id,cost_mode,workspace_id,skill_id,agent_id,mission_id,payload,metadata,created_at'],
  ]) {
    const target = new URL(pathname, origin);
    if (columns) { target.searchParams.set('select', columns); target.searchParams.set('limit', '0'); }
    try {
      const response = await fetcher(target, { redirect: 'error', signal: AbortSignal.timeout(5000),
        headers: { apikey: key, ...(columns ? { Authorization: `Bearer ${key}` } : {}) } });
      checks.push({ dependency, status: response.ok ? 'reachable' : 'http_error', httpStatus: response.status });
      // Never retain or print error bodies, keys, URLs or application data.
      if (response.body) await response.body.cancel();
      if (!response.ok) break;
    } catch (error) {
      const cause = error?.cause?.code;
      const status = cause === 'ENOTFOUND' ? 'dns_not_found'
        : error?.name === 'TimeoutError' || error?.name === 'AbortError' ? 'timeout' : 'connection_failed';
      checks.push({ dependency, status });
      break;
    }
  }
  return { ready: checks.length === 3 && checks.every(check => check.status === 'reachable'),
    checks, scope: 'auth_reachability_and_zero_row_schema_reads',
    ownerLoginVerified: false, durableWritesVerified: false, agentExecutionVerified: false };
}

if (process.argv[1] === '-' || (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href)) {
  const result = await checkDependencies(process.env);
  console.log(JSON.stringify(result));
  if (!result.ready) process.exitCode = 2;
}
