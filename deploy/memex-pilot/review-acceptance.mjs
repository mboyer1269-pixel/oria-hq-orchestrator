// Disposable Linux container only: /runtime is a fresh tmpfs, no production mounts.
import assert from 'node:assert/strict';
process.env.AGENTMEMORY_VAULT_PATH='/runtime/vault';
const {initGraph,closeGraph,queryEntities}=await import('../src/graph.ts');
const {initIntake,getIntakeDb}=await import('../src/db/intake.ts');
const {submitProposal}=await import('../src/intake/index.ts');
const {approveProposal,promoteApprovedProposal}=await import('../src/intake/promotion.ts');
const {getProposalReviewSnapshot,reviewProposal}=await import('../src/intake/review.ts');
initGraph('/runtime/graph.db'); initIntake('/runtime/intake.db');
try {
  const namespace='org:review-acceptance';
  const p=submitProposal({requestId:'synthetic-request',namespace,tenant:namespace,proposedBy:'synthetic-contributor',sourceClient:'synthetic-contributor',content:'Synthetic governed review qualification.'});
  assert.throws(()=>approveProposal(p.id),/Governed review required/);
  const snapshot=getProposalReviewSnapshot(namespace,p.id);
  assert.equal(snapshot.hashVersion,1);
  const decision={namespace,proposalId:p.id,expectedPayloadHash:snapshot.payloadHash,reviewerId:'synthetic-local-operator',decisionId:'synthetic-decision',decision:'approve'};
  assert.throws(()=>reviewProposal({...decision,expectedPayloadHash:'0'.repeat(64)}));
  const receipt=reviewProposal(decision);
  initIntake('/runtime/intake.db');
  assert.deepEqual(reviewProposal(decision),receipt);
  assert.deepEqual(queryEntities({namespace}),[]);
  promoteApprovedProposal(p.id); promoteApprovedProposal(p.id);
  assert.equal(queryEntities({namespace}).length,1);
  const db=getIntakeDb();
  assert.equal(db.prepare('SELECT count(*) AS n FROM intake_human_reviews').get().n,1);
  assert.equal(db.prepare("SELECT count(*) AS n FROM memory_publications WHERE phase='complete'").get().n,1);
  db.prepare('UPDATE intake_proposals SET content=? WHERE id=?').run('Changed after review',p.id);
  assert.throws(()=>promoteApprovedProposal(p.id),/Governed publication review mismatch/);
  console.log(JSON.stringify({synthetic:true,governedReview:'pass',legacyBypass:'denied',stalePayload:'denied',durableDecision:'pass',publicationRetry:'one',postReviewMutation:'denied'}));
} finally {getIntakeDb().close();closeGraph();}
