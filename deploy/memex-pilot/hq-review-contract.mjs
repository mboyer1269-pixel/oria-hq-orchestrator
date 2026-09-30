// Disposable integration: real HQ service -> real proxy -> Memex operator router.
// Authentication fixtures stand in for the owner session; this is not browser proof.
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import crypto from 'node:crypto';
import http from 'node:http';
import assert from 'node:assert/strict';
import { pathToFileURL } from 'node:url';
import { createHandler } from '../memex-tls/proxy.mjs';
const [hqArg, memexArg] = process.argv.slice(2);
if (!hqArg || !memexArg) throw Error('Expected HQ and Memex repository directories');
const hq = fs.realpathSync(hqArg), memex = fs.realpathSync(memexArg);
const root = fs.mkdtempSync(path.join(os.tmpdir(), 'hq-memex-review-'));
const namespace = 'org:workspace:contract';
const token = `opr1.${crypto.randomBytes(32).toString('base64url')}`;
const credentialFile = path.join(root, 'operator.json'), tokenFile = path.join(root, 'token');
fs.writeFileSync(credentialFile, JSON.stringify({ token, principal: 'hq-contract-operator', namespace }));
fs.writeFileSync(tokenFile, token);
process.env.AGENTMEMORY_VAULT_PATH = path.join(root, 'vault');
process.env.AGENTMEMORY_HANDLE_SECRET = crypto.randomBytes(32).toString('hex');
process.env.GATEWAY_DEFAULT_ACCESS = 'read_write';
process.env.MEMEX_OPERATOR_REVIEW_ENABLED = 'true';
process.env.MEMEX_OPERATOR_REVIEW_CREDENTIAL_FILE = credentialFile;
delete process.env.GATEWAY_TOKEN; delete process.env.GATEWAY_NAMESPACES;
const load = relative => import(pathToFileURL(path.join(memex, relative)).href);
const { initGraph, closeGraph } = await load('src/graph.ts');
const { initIntake, getIntakeDb } = await load('src/db/intake.ts');
const { createHttpApp } = await load('src/mcp/unified-server.ts');
const { mintHandle } = await load('src/mcp/handles.ts');
const { createJiti } = await import(pathToFileURL(path.join(hq, 'node_modules/jiti/lib/jiti.mjs')).href);
const jiti = createJiti(path.join(hq, 'package.json'), { alias: { '@': path.join(hq, 'src'), 'server-only': path.join(hq, 'src/scripts/smoke/server-only-stub.mjs') } });
const { createMemexProposalService } = await jiti.import(path.join(hq, 'src/server/memory/memex-proposal-service.ts'));
const { createMemexReviewService } = await jiti.import(path.join(hq, 'src/server/memory/memex-review-service.ts'));
initGraph(path.join(root, 'graph.db')); initIntake(path.join(root, 'intake.db'));
const server = await new Promise(resolve => { const s = createHttpApp().listen(0, '127.0.0.1', () => resolve(s)); });
const proxy = http.createServer(createHandler({ request(options, callback) { return http.request({ ...options, hostname: '127.0.0.1', port: server.address().port }, callback); } }));
await new Promise(resolve => proxy.listen(0, '127.0.0.1', resolve));
try {
  const origin = `http://127.0.0.1:${proxy.address().port}`;
  const agentHandle = mintHandle('hq-contract-contributor', 'read_write', process.env.AGENTMEMORY_HANDLE_SECRET, 120, new Date(), [namespace]);
  const env = { ORIA_ENABLE_MEMEX_PROPOSALS: '1', MEMEX_HTTP_HQ_WORKSPACE_ID: 'contract', MEMEX_HTTP_ENDPOINT: `${origin}/mcp`, MEMEX_HTTP_PROPOSAL_HANDLE: agentHandle,
    ORIA_ENABLE_MEMEX_REVIEW: '1', MEMEX_REVIEW_HQ_WORKSPACE_ID: 'contract', MEMEX_REVIEW_ENDPOINT: origin, MEMEX_REVIEW_TOKEN_FILE: tokenFile };
  const contributor = createMemexProposalService({ env: () => env });
  const review = createMemexReviewService({ env: () => env });
  const submitted = await contributor.submitMemexProposal({ workspaceId: 'contract', requestId: crypto.randomUUID(), content: 'Disposable operator review fixture.' });
  assert.equal(submitted.status, 'received');
  const snapshot = await review('contract', submitted.proposalId);
  assert.equal(snapshot.status, 'snapshot');
  assert.equal(snapshot.snapshot.proposal.content, 'Disposable operator review fixture.');
  assert.deepEqual(await review('foreign', submitted.proposalId), { status: 'workspace_unbound' });
  const decision = { proposalId: submitted.proposalId, expectedPayloadHash: snapshot.snapshot.payloadHash, hashVersion: 1, reviewerId: 'synthetic-authenticated-owner', decisionId: crypto.randomUUID(), decision: 'approve' };
  assert.deepEqual(await review('contract', submitted.proposalId, { ...decision, expectedPayloadHash: '0'.repeat(64) }), { status: 'conflict' });
  const post = async (base, route, credential, body) => {
    const response = await fetch(base + route, { method: 'POST', headers: { authorization: `Bearer ${credential}`, 'content-type': 'application/json' }, body: JSON.stringify(body) });
    await response.text(); return response.status;
  };
  const direct = `http://127.0.0.1:${server.address().port}`;
  for (const base of [direct, origin]) {
    assert.equal(await post(base, '/operator/review/decision', agentHandle, { namespace, ...decision }), 401);
    assert.equal(await post(base, '/operator/review/snapshot', token, { namespace: 'org:workspace:foreign', proposalId: submitted.proposalId }), 404);
    assert.equal(await post(base, '/operator/review/decision', token, { namespace, ...decision, technicalPrincipal: 'forged' }), 400);
  }
  const accepted = await review('contract', submitted.proposalId, decision);
  assert.equal(accepted.status, 'decided');
  assert.equal(accepted.receipt.technicalPrincipal, 'hq-contract-operator');
  assert.equal(accepted.receipt.reviewerId, decision.reviewerId);
  initIntake(path.join(root, 'intake.db'));
  assert.deepEqual(await review('contract', submitted.proposalId, decision), accepted);
  assert.deepEqual(await review('contract', submitted.proposalId, { ...decision, decision: 'reject' }), { status: 'conflict' });
  assert.equal(getIntakeDb().prepare('SELECT count(*) AS n FROM intake_human_reviews').get().n, 1);
  assert.equal(getIntakeDb().prepare('SELECT status FROM intake_proposals WHERE id=?').get(submitted.proposalId).status, 'approved');
  const hasJournal = getIntakeDb().prepare("SELECT 1 FROM sqlite_master WHERE type='table' AND name='memory_publications'").get();
  if (hasJournal) assert.equal(getIntakeDb().prepare('SELECT count(*) AS n FROM memory_publications').get().n, 0);
  console.log(JSON.stringify({ realHttpProxyAndServices: 'pass', agentReviewDenied: 'pass', namespaceIsolation: 'pass', staleHash: 'pass', persistedRetry: 'pass', conflictingDecision: 'pass', actorAndPrincipal: 'pass', publication: 'not_performed' }));
} finally {
  proxy.closeAllConnections(); server.closeAllConnections();
  await Promise.all([new Promise(resolve => proxy.close(resolve)), new Promise(resolve => server.close(resolve))]);
  getIntakeDb().close(); closeGraph();
  if (path.dirname(root) !== fs.realpathSync(os.tmpdir()) || !path.basename(root).startsWith('hq-memex-review-')) throw Error('Unsafe cleanup target');
  fs.rmSync(root, { recursive: true, force: true });
}
