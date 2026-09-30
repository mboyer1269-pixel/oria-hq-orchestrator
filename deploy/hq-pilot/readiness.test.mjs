import { test } from 'node:test';
import assert from 'node:assert/strict';
import { checkDependencies } from './readiness.mjs';
const env = { NEXT_PUBLIC_SUPABASE_URL: 'https://test.supabase.co', NEXT_PUBLIC_SUPABASE_ANON_KEY: 'public-test', SUPABASE_SERVICE_ROLE_KEY: 'secret-test' };
test('DNS failure stops downstream probes and never exposes diagnostics or credentials', async () => {
  let calls = 0;
  const result = await checkDependencies(env, async () => { calls++; throw Object.assign(new Error('secret-test private diagnostic'), { cause: { code: 'ENOTFOUND' } }); });
  assert.equal(calls, 1); assert.equal(result.ready, false);
  assert.equal(result.checks[0].status, 'dns_not_found');
  assert.ok(!JSON.stringify(result).includes('secret-test'));
});
test('requests forbid redirects and request no rows without claiming end-to-end readiness', async () => {
  const calls = [];
  const result = await checkDependencies(env, async (url, options) => {
    calls.push({ url, options }); return new Response('[]', { status: 200 });
  });
  assert.equal(result.ready, true); assert.equal(result.ownerLoginVerified, false);
  assert.equal(result.durableWritesVerified, false); assert.equal(result.agentExecutionVerified, false);
  assert.ok(calls.every(call => call.options.redirect === 'error' && call.options.signal));
  assert.ok(calls.slice(1).every(call => call.url.searchParams.get('limit') === '0'));
  assert.equal(calls[0].options.headers.Authorization, undefined);
});
test('invalid destination and HTTP denial fail without a fallback or retry', async () => {
  let calls = 0;
  assert.equal((await checkDependencies({ ...env, NEXT_PUBLIC_SUPABASE_URL: 'http://invalid' }, async () => { calls++; })).ready, false);
  assert.equal(calls, 0);
  const result = await checkDependencies(env, async () => { calls++; return new Response('private', { status: 403 }); });
  assert.equal(calls, 1); assert.equal(result.ready, false); assert.equal(result.checks[0].httpStatus, 403);
});
