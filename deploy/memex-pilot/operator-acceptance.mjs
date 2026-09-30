// Isolated Linux container only, fresh /runtime tmpfs, no operational volumes.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import crypto from 'node:crypto';
process.env.AGENTMEMORY_VAULT_PATH='/runtime/vault';
process.env.AGENTMEMORY_HANDLE_SECRET=crypto.randomBytes(32).toString('hex');
process.env.GATEWAY_DEFAULT_ACCESS='read_write';
process.env.MEMEX_OPERATOR_REVIEW_ENABLED='true';
process.env.MEMEX_OPERATOR_REVIEW_CREDENTIAL_FILE='/runtime/operator.json';
const token=`opr1.${crypto.randomBytes(32).toString('base64url')}`;
const namespace='org:workspace:operator-fixture';
fs.writeFileSync('/runtime/operator.json',JSON.stringify({token,namespace,principal:'hq-synthetic-operator'}),{mode:0o400});
const {initGraph,closeGraph,queryEntities}=await import('../src/graph.ts');
const {initIntake,getIntakeDb}=await import('../src/db/intake.ts');
const {submitProposal}=await import('../src/intake/index.ts');
const {createHttpApp}=await import('../src/mcp/unified-server.ts');
const {mintHandle}=await import('../src/mcp/handles.ts');
initGraph('/runtime/graph.db');initIntake('/runtime/intake.db');
const server=await new Promise(resolve=>{const s=createHttpApp().listen(0,'127.0.0.1',()=>resolve(s));});
const send=async(route,body,credential=token)=>{
 const response=await fetch(`http://127.0.0.1:${server.address().port}/operator/review/${route}`,{method:'POST',headers:{authorization:`Bearer ${credential}`,'content-type':'application/json'},body:JSON.stringify(body)});
 return {status:response.status,body:await response.json()};
};
try{
 const proposal=submitProposal({requestId:'operator-fixture',namespace,tenant:namespace,proposedBy:'contributor',sourceClient:'contributor',content:'Disposable operator HTTP acceptance.'});
 const target={namespace,proposalId:proposal.id};
 const snapshot=await send('snapshot',target);assert.equal(snapshot.status,200);
 const decision={...target,hashVersion:1,expectedPayloadHash:snapshot.body.payloadHash,reviewerId:'synthetic-owner',decisionId:'synthetic-decision',decision:'approve'};
 const agent=mintHandle('agent','read_write',process.env.AGENTMEMORY_HANDLE_SECRET,60,new Date(),[namespace]);
 assert.equal((await send('decision',decision,agent)).status,401);
 assert.equal((await send('snapshot',{...target,namespace:'org:workspace:foreign'})).status,404);
 assert.equal((await send('decision',{...decision,expectedPayloadHash:'0'.repeat(64)})).status,409);
 const receipt=await send('decision',decision);assert.equal(receipt.status,200);
 assert.equal(receipt.body.technicalPrincipal,'hq-synthetic-operator');
 initIntake('/runtime/intake.db');assert.deepEqual(await send('decision',decision),receipt);
 assert.equal((await send('decision',{...decision,decision:'reject'})).status,409);
 assert.deepEqual(queryEntities({namespace}),[]);
 assert.equal(getIntakeDb().prepare('SELECT count(*) AS n FROM intake_human_reviews').get().n,1);
 console.log(JSON.stringify({isolated:true,operatorHttp:'pass',agentDenied:true,scope:'pass',stale:'conflict',durableRetry:'pass',publication:'none'}));
}finally{server.closeAllConnections();await new Promise(resolve=>server.close(resolve));getIntakeDb().close();closeGraph();}
