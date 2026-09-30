// Read-only synthetic canary check. Credential arrives on stdin, never in logs.
import assert from 'node:assert/strict';
import https from 'node:https';
let input=''; for await (const part of process.stdin) input += part;
const {handle}=JSON.parse(input);
const namespace='org:workspace:pilot-a';
async function rpc(name,args,credential=handle) {
  const result=await fetch('https://memex-tls:3443/mcp',{method:'POST',headers:{'Content-Type':'application/json',Authorization:`Bearer ${credential}`},body:JSON.stringify({jsonrpc:'2.0',id:1,method:'tools/call',params:{name,arguments:args}}),signal:AbortSignal.timeout(5000)});
  return {status:result.status,body:await result.json()};
}
function rejectedTls(options) {
  return new Promise(resolve=>{const req=https.request('https://memex-tls:3443/mcp',options,res=>{res.resume();resolve(false)});req.on('error',()=>resolve(true));req.setTimeout(5000,()=>{req.destroy();resolve(false)});req.end()});
}
try {
  const result=await rpc('agentmemory_graph_query',{namespace,limit:50});
  assert.equal(result.status,200);
  const records=JSON.parse(result.body.result.content[0].text);
  assert.ok(records.some(row=>row.id==='memex-pilot-canary-a-v1'));
  assert.ok(records.every(row=>row.namespace===namespace));
  assert.ok((await rpc('agentmemory_graph_query',{namespace:'org:workspace:pilot-b'})).body.error);
  assert.ok((await rpc('agentmemory_submit_proposal',{namespace,tenant:namespace,content:'MUST_NOT_PERSIST'})).body.error);
  const receipt=await rpc('agentmemory_proposal_status',{namespace,proposalId:'nonexistent-synthetic-proposal'});
  assert.equal(receipt.body.result.content[0].text,'null');
  assert.notEqual((await rpc('agentmemory_graph_query',{namespace},handle+'tampered')).status,200);
  assert.equal(await rejectedTls({ca:[]}),true);
  assert.equal(await rejectedTls({servername:'wrong-memex-host'}),true);
  console.log(JSON.stringify({tls:'verified',canary:'pass',crossProject:'denied',write:'denied',receipt:'scoped',unknownCa:'denied',wrongSan:'denied',tampered:'denied'}));
} catch {console.error('Memex TLS qualification failed');process.exitCode=1;}
