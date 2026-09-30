// Trusted operator probe, pipe via docker exec -i node --experimental-strip-types --input-type=module.
// Default verify is HTTP-only. MODE=seed explicitly publishes ONLY these guarded synthetic canaries.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
const mode = process.env.MODE || 'verify';
if (!['seed', 'verify'].includes(mode)) throw new Error('MODE must be seed or verify');
const source = process.env.MEMEX_SOURCE_ROOT || '/app';
const load = name => import(pathToFileURL(path.join(source, 'src', name)).href);
const { mintHandle } = await load('mcp/handles.ts');
const secret = fs.readFileSync('/run/secrets/handle-signing-key', 'utf8').trim();
const subject = 'operator-synthetic-memex-pilot-v1';
const provenance = 'operator-review:synthetic-pilot';
const canaries = ['a', 'b'].map(letter => ({
  namespace: `org:workspace:pilot-${letter}`,
  entity: { id: `memex-pilot-canary-${letter}-v1`, type: 'Memory', namespace: `org:workspace:pilot-${letter}`,
    name: `SYNTHETIC_MEMEX_PILOT_${letter.toUpperCase()}`, source: provenance,
    properties: { status: 'verified', zone: 'human', content: `Synthetic Memex persistence canary ${letter.toUpperCase()} v1; no real user information.` } }
}));
const handle = (ns, access = 'read_only', now = new Date()) => mintHandle(subject, access, secret, 120, now, [ns]);
async function call(credential, name, args) {
  const headers = { 'Content-Type': 'application/json' };
  if (credential !== null) headers.Authorization = `Bearer ${credential}`;
  const response = await fetch('http://127.0.0.1:3000/mcp', {
    method: 'POST', headers, body: JSON.stringify({ jsonrpc: '2.0', id: 1, method: 'tools/call', params: { name, arguments: args } }),
    signal: AbortSignal.timeout(10000)
  });
  return { status: response.status, body: await response.json() };
}
let graph, intake;
let phase = 'start';
try {
  if (mode === 'seed') {
    phase = 'seed-storage';
    // Explicit paths mandatory: never fall back to development data directories.
    assert.equal(process.env.AGENTMEMORY_DB_PATH, '/runtime/graph/graph.db');
    assert.equal(process.env.AGENTMEMORY_INTAKE_DB_PATH, '/runtime/intake/intake.db');
    assert.equal(process.env.AGENTMEMORY_VAULT_PATH, '/runtime/vault');
    graph = await load('graph.ts');
    intake = await load('intake.ts');
    graph.initGraph(process.env.AGENTMEMORY_DB_PATH);
    intake.initIntake(process.env.AGENTMEMORY_INTAKE_DB_PATH);
    for (const { namespace, entity } of canaries) {
      phase = `seed-${namespace}`;
      const expected = { tenant: namespace, namespace, content: entity.properties.content,
        provenance, suggestedEntities: JSON.stringify([entity]), confidence: 1 };
      const candidates = intake.getIntakeDb().prepare('SELECT * FROM intake_proposals WHERE namespace = ? AND provenance = ?').all(namespace, provenance);
      assert.ok(candidates.length <= 1, 'Ambiguous synthetic proposal; manual inspection required');
      let row = candidates[0];
      if (!row) {
        assert.equal(graph.getEntity(entity.id), null, 'Canary ID already belongs to unrelated data');
        const submitted = await call(handle(namespace, 'read_write'), 'agentmemory_submit_proposal', expected);
        assert.equal(submitted.status, 200);
        assert.ok(submitted.body.result && !submitted.body.result.isError);
        row = intake.readProposal(submitted.body.result.content[0].text);
      }
      assert.ok(row);
      for (const key of ['tenant', 'namespace', 'content', 'provenance', 'confidence']) assert.deepEqual(row[key], expected[key]);
      assert.deepEqual(JSON.parse(row.suggestedEntities), [entity]);
      assert.ok(!row.suggestedRelations || row.suggestedRelations === '[]');
      assert.equal(row.proposedBy, subject);
      assert.equal(row.sourceClient, subject);
      assert.ok(['proposed', 'approved', 'promoted'].includes(row.status), 'Unexpected state: do not recover arbitrary pending publication');
      if (row.status === 'proposed') intake.approveProposal(row.id);
      if (row.status !== 'promoted') intake.promoteApprovedProposal(row.id);
      assert.equal(intake.readProposal(row.id).status, 'promoted');
    }
  }
  for (const { namespace, entity } of canaries) {
    phase = `verify-${namespace}`;
    const readHandle = handle(namespace);
    const read = await call(readHandle, 'agentmemory_graph_query', { namespace });
    assert.equal(read.status, 200);
    assert.ok(read.body.result && !read.body.result.isError);
    const matches = JSON.parse(read.body.result.content[0].text).filter(row => row.id === entity.id);
    assert.equal(matches.length, 1);
    for (const key of ['id', 'namespace', 'name', 'source', 'properties']) assert.deepEqual(matches[0][key], entity[key]);
    const other = canaries.find(c => c.namespace !== namespace);
    assert.ok(!JSON.stringify(read.body).includes(other.entity.id));
    assert.ok((await call(readHandle, 'agentmemory_graph_query', { namespace: other.namespace })).body.error);
    assert.ok((await call(readHandle, 'agentmemory_read_vault_file', { filepath: 'Human/private.md' })).body.error);
    assert.ok((await call(readHandle, 'agentmemory_submit_proposal', { tenant: namespace, namespace, content: 'MUST_NOT_PERSIST' })).body.error);
    for (const credential of [null, '', `${readHandle}tampered`, handle(namespace, 'read_only', new Date(Date.now() - 240000))]) {
      assert.equal((await call(credential, 'agentmemory_graph_query', { namespace })).status, 401);
    }
  }
  console.log(JSON.stringify({ mode, syntheticOnly: true, signedHttpRead: 'pass', exactCanaries: 'pass', crossScope: 'denied', rawVault: 'denied', readOnlyWrite: 'denied', unsignedExpiredTampered: 'denied' }));
} catch {
  // Do not print error objects, request headers, keys, handles or database contents.
  console.error(JSON.stringify({ mode, phase, status: 'failed' }));
  process.exitCode = 1;
} finally {
  graph?.closeGraph();
  if (intake) intake.getIntakeDb().close();
}
