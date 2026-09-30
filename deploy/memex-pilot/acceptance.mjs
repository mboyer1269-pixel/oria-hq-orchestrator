// Synthetic, disposable integration check: never opens configured runtime paths.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { randomBytes } from 'node:crypto';
const root = fs.mkdtempSync(path.join(os.tmpdir(), 'memex-pilot-'));
process.env.AGENTMEMORY_VAULT_PATH = path.join(root, 'vault');
process.env.AGENTMEMORY_DB_PATH = path.join(root, 'graph.db');
process.env.AGENTMEMORY_INTAKE_DB_PATH = path.join(root, 'intake.db');
process.env.AGENTMEMORY_HANDLE_SECRET = randomBytes(32).toString('hex');
delete process.env.GATEWAY_TOKEN;
process.env.GATEWAY_DEFAULT_ACCESS = 'read_write';
delete process.env.GATEWAY_NAMESPACES;
const source = process.env.MEMEX_SOURCE_ROOT || '/app';
const load = relative => import(pathToFileURL(path.join(source, 'src', relative)).href);
const graph = await load('graph.ts');
const intake = await load('intake.ts');
const { mintHandle } = await load('mcp/handles.ts');
const { createHttpApp } = await load('mcp/unified-server.ts');
graph.initGraph(process.env.AGENTMEMORY_DB_PATH);
intake.initIntake(process.env.AGENTMEMORY_INTAKE_DB_PATH);
const server = await new Promise(resolve => { const s = createHttpApp().listen(0, '127.0.0.1', () => resolve(s)); });
const token = (access, ns, now = new Date()) => mintHandle('pilot-agent', access, process.env.AGENTMEMORY_HANDLE_SECRET, 60, now, [ns]);
const rw = token('read_write', 'org:pilot-a');
const ro = token('read_only', 'org:pilot-a');
async function call(credential, name, args) {
  const res = await fetch(`http://127.0.0.1:${server.address().port}/mcp`, {
    method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${credential}` },
    body: JSON.stringify({ jsonrpc: '2.0', id: 1, method: 'tools/call', params: { name, arguments: args } })
  });
  return { status: res.status, body: await res.json() };
}
const query = namespace => ({ namespace });
try {
  for (const method of ['tools/list', 'resources/list']) {
    const response = await fetch(`http://127.0.0.1:${server.address().port}/mcp`, {
      method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${ro}` },
      body: JSON.stringify({ jsonrpc: '2.0', id: 1, method })
    });
    const body = await response.json();
    assert.ok(body.result, JSON.stringify(body));
    assert.ok(Array.isArray(body.result[method.split('/')[0]]));
  }
  const proposed = await call(rw, 'agentmemory_submit_proposal', { tenant: 'org:pilot-a', namespace: 'org:pilot-a', content: 'SYNTHETIC_PILOT_CANARY', proposedBy: 'spoofed' });
  assert.equal(proposed.status, 200);
  assert.ok(proposed.body.result, JSON.stringify(proposed.body));
  const id = proposed.body.result.content[0].text;
  assert.equal(intake.readProposal(id).proposedBy, 'pilot-agent');
  assert.ok(!JSON.stringify((await call(ro, 'agentmemory_graph_query', query('org:pilot-a'))).body).includes('SYNTHETIC_PILOT_CANARY'));
  intake.approveProposal(id); // Explicit synthetic operator admission, never remote auto-approval.
  intake.promoteApprovedProposal(id);
  intake.promoteApprovedProposal(id); // Retry must not duplicate projections.
  assert.equal(intake.readProposal(id).status, 'promoted');
  const markdown = fs.readdirSync(process.env.AGENTMEMORY_VAULT_PATH, { recursive: true })
    .filter(p => p.endsWith('.md'))
    .map(p => fs.readFileSync(path.join(process.env.AGENTMEMORY_VAULT_PATH, p), 'utf8'));
  assert.equal(markdown.filter(body => body.includes('SYNTHETIC_PILOT_CANARY')).length, 1);
  const read = await call(ro, 'agentmemory_graph_query', query('org:pilot-a'));
  const rows = JSON.parse(read.body.result.content[0].text);
  assert.equal(rows.filter(r => r.properties?.content === 'SYNTHETIC_PILOT_CANARY').length, 1);
  assert.ok((await call(ro, 'agentmemory_graph_query', query('org:pilot-b'))).body.error);
  assert.ok((await call(token('read_only', 'org:pilot-b'), 'agentmemory_graph_query', query('org:pilot-b'))).body.result);
  assert.ok(!JSON.stringify((await call(token('read_only', 'org:pilot-b'), 'agentmemory_graph_query', query('org:pilot-b'))).body).includes('SYNTHETIC_PILOT_CANARY'));
  assert.ok((await call(ro, 'agentmemory_submit_proposal', { tenant: 'org:pilot-a', namespace: 'org:pilot-a', content: 'denied' })).body.error);
  assert.equal((await call(token('read_only', 'org:pilot-a', new Date(Date.now() - 120000)), 'agentmemory_graph_query', query('org:pilot-a'))).status, 401);
  assert.equal((await call(`${ro}tampered`, 'agentmemory_graph_query', query('org:pilot-a'))).status, 401);
  assert.equal((await call('', 'agentmemory_graph_query', query('org:pilot-a'))).status, 401);
  assert.ok((await call(ro, 'agentmemory_read_vault_file', { filepath: 'Human/private.md' })).body.error);
  console.log(JSON.stringify({ synthetic: true, publication: 'pass', retry: 'pass', signedHttpRead: 'pass', crossProject: 'pass', readOnlyWriteDenied: 'pass', expiredAndTampered: 'pass', rawVaultDenied: 'pass' }));
} finally {
  await new Promise(resolve => server.close(resolve));
  graph.closeGraph();
  intake.getIntakeDb().close();
  fs.rmSync(root, { recursive: true, force: true });
}
