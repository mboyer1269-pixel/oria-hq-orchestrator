// Offline structural regression + synthetic model; never imports/runs upstream code.
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import assert from 'node:assert/strict';
const root = process.argv[2];
assert(root, 'Pass the reviewed Paperclip source directory');
const read = p => readFileSync(resolve(root, p), 'utf8').replace(/\r\n/g, '\n');
const utils = read('packages/adapter-utils/src/server-utils.ts');
const target = read('packages/adapter-utils/src/execution-target.ts');
const sanitizer = read('packages/adapter-utils/src/remote-execution-env.ts');
const cursor = read('packages/adapters/cursor-local/src/server/execute.ts');
const gemini = read('packages/adapters/gemini-local/src/server/execute.ts');
assert(utils.includes('remoteEnv: opts.remoteExecution ? opts.env : null'));
assert(utils.includes('Object.entries(options.remoteEnv ?? {})'));
assert(utils.includes('if (options.remoteExecution) {\n    const resolvedSsh = await resolveCommandPath("ssh", process.cwd(), env);'));
assert(target.includes('!installCommand || input.target?.kind !== "remote" || input.target.transport !== "sandbox"'));
assert(cursor.includes('Object.entries({ ...process.env, ...env })'));
assert(gemini.includes('Object.entries(ensurePathInEnv({ ...process.env, ...buildGeminiHeadlessEnv(env) }))'));
assert(target.includes('sanitizeRemoteExecutionEnv(Object.fromEntries('));
assert(sanitizer.includes('if (!REMOTE_EXECUTION_ENV_IDENTITY_KEYS.has(normalizedKey)) {\n      sanitized[key] = value;'));
const identityKeys = new Set([...sanitizer.slice(0, sanitizer.indexOf(']);')).matchAll(/"([A-Z_]+)"/g)].map(m => m[1]));
const inherited = { HOME:'/host', PATH:'/host/bin', DATABASE_URL:'synthetic-db', BETTER_AUTH_SECRET:'synthetic-auth', OTHER_SERVER_SECRET:'synthetic-other' };
const explicit = { PAPERCLIP_API_KEY:'synthetic-run-scoped', PAPERCLIP_AGENT_ID:'fixture', HOME:'/home/runner' };
// Model only the reviewed identity filter, using synthetic inputs exclusively.
const sanitize = env => Object.fromEntries(Object.entries(env).filter(([k,v]) => !identityKeys.has(k.toUpperCase()) || inherited[k] !== v));
const sshRemote = sanitize(explicit);
const sandboxProbe = sanitize({...inherited, ...explicit});
for (const key of ['DATABASE_URL','BETTER_AUTH_SECRET','OTHER_SERVER_SECRET']) {
  assert(!(key in sshRemote));
  assert(key in sandboxProbe);
}
assert.equal(sshRemote.PAPERCLIP_API_KEY, explicit.PAPERCLIP_API_KEY);
assert('DATABASE_URL' in sanitize({...explicit, DATABASE_URL:'synthetic-misconfiguration'}));
console.log('PASS: reviewed source seams intact; synthetic SSH explicit env excludes inherited secrets; sandbox merged probe retains canaries; explicit config is not secret-filtered. Not an end-to-end SSH test.');
