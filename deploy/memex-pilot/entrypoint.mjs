import { readFileSync } from 'node:fs';
const secret = readFileSync('/run/secrets/handle-signing-key', 'utf8').trim();
if (secret.length < 32) throw new Error('Handle signing key must have at least 32 characters');
process.env.AGENTMEMORY_HANDLE_SECRET = secret;
// Pilot is signed-only, including if the launcher inherited a legacy token.
delete process.env.GATEWAY_TOKEN;
delete process.env.GATEWAY_NAMESPACES;
const { runHttp } = await import('../src/mcp/unified-server.ts');
await runHttp();
