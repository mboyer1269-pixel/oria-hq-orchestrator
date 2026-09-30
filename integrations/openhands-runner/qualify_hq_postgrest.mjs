// Isolated PostgreSQL/PostgREST qualification. Requires the disposable harness.
import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {readFile,writeFile,rename,chmod} from 'node:fs/promises';
import {spawn} from 'node:child_process';
import {createRequire} from 'node:module';
const require=createRequire('/workspace/hq/package.json');
const {createJiti}=require('jiti');
const phase=process.argv[2];
const liveMemex=process.env.QUALIFICATION_LIVE_MEMEX==='1';
const lifecycle=process.env.QUALIFICATION_LIFECYCLE==='1';
const providerBinding=process.env.QUALIFICATION_PROVIDER_BINDING==='1';
const syntheticProvider=process.env.QUALIFICATION_SYNTHETIC_PROVIDER==='1';
const dockerJob=process.env.QUALIFICATION_DOCKER_JOB==='1';
const validDossier=process.env.QUALIFICATION_VALID_DOSSIER==='1';
const reviewService=process.env.QUALIFICATION_REVIEW_SERVICE==='1';
const reviewControl=process.env.QUALIFICATION_REVIEW_CONTROL==='1';
const reviewHost=process.env.QUALIFICATION_REVIEW_HOST==='1';
if(!['seed','verify'].includes(phase))throw Error('Unknown qualification phase');
// Mimics only the Supabase /rest/v1 gateway prefix. No production credential/auth.
const proxy=createServer(async(req,res)=>{
 try {
  if(!req.url.startsWith('/rest/v1/')){res.writeHead(404).end();return;}
  const chunks=[];for await(const c of req)chunks.push(c);
  const headers={...req.headers};delete headers.authorization;delete headers.apikey;delete headers.host;delete headers['content-length'];
  const response=await fetch('http://127.0.0.1:3000'+req.url.slice('/rest/v1'.length),{method:req.method,headers,body:chunks.length?Buffer.concat(chunks):undefined});
  res.writeHead(response.status,Object.fromEntries(response.headers));res.end(Buffer.from(await response.arrayBuffer()));
 }catch{res.writeHead(502).end();}
});
await new Promise(resolve=>proxy.listen(0,'127.0.0.1',resolve));
try {
 process.env.NEXT_PUBLIC_SUPABASE_URL=`http://127.0.0.1:${proxy.address().port}`;
 process.env.SUPABASE_SERVICE_ROLE_KEY='synthetic-local-qualification';
 process.env.NODE_ENV='test';
 for(let attempt=0;;attempt++){
  try{const r=await fetch('http://127.0.0.1:3000/');if(r.ok)break;}catch{}
  if(attempt>=30)throw Error('PostgREST not ready');await new Promise(resolve=>setTimeout(resolve,250));
 }
 const jiti=createJiti(import.meta.url,{alias:{'@':'/workspace/hq/src','server-only':'/workspace/hq/src/scripts/smoke/server-only-stub.mjs'}});
 const load=name=>jiti.import('/workspace/hq/src/server/missions/'+name);
 const {createDevelopmentService,createDevelopmentStore,developmentMissionId}=await load('development-mission.ts');
 const {createOpenHandsMemorySnapshotStore}=await load('openhands-memory-snapshot-store.ts');
 const {createOpenHandsMemoryAttachmentService,createOpenHandsMemoryAttachmentStore}=await load('openhands-memory-attachment.ts');
 const {createOpenHandsConfirmationService}=await load('openhands-confirmation.ts');
 const {createOptionalSupabaseAdminClient}=await jiti.import('/workspace/hq/src/server/supabase/admin.ts');
 let snapshot=JSON.parse(await readFile('/qualification/fixtures/hq-memory-dossier.json','utf8')).memory;
 const ctx={workspaceId:'synthetic-a',actorId:'11111111-1111-4111-8111-111111111111'};
 const requestId='714ac9b7-6bce-4eb4-b3bd-08d3df8ad46e';
 const store=createDevelopmentStore(),snapshots=createOpenHandsMemorySnapshotStore();
 const missionId=developmentMissionId(ctx.workspaceId,requestId);
 if(phase==='seed'){
  const created=await createDevelopmentService({enabled:()=>true}).create({requestId,title:'PostgREST lifecycle',objective:'Durable memory test',scope:'Synthetic only',acceptanceCriteria:'Survives database restart'}, {...ctx,modeId:'hq'});
  assert.equal(created.status,'saved');
 }
 let mission=await store.load(ctx.workspaceId,missionId);assert.ok(mission);
 const request={missionId,expectedUpdatedAt:mission.updatedAt,commitSha:validDossier?process.env.QUALIFICATION_COMMIT:'a'.repeat(40),executorVersion:'1.50.0',budget:{maxCostCents:100,maxTokens:10000,maxIterations:2,timeoutSeconds:60}};
 const service=createOpenHandsConfirmationService();
 let memoryReads=0;
 let liveFixture;
 let createTransport;
 if(liveMemex&&phase==='seed'){
  for(let attempt=0;;attempt++){
   try{const r=await fetch('http://127.0.0.1:4320/fixture');if(r.ok){liveFixture=await r.json();break;}}catch{}
   if(attempt>=40)throw Error('Memex fixture readiness failed');
   await new Promise(resolve=>setTimeout(resolve,250));
  }
  const {createProjectHttpMemexTransport}=await jiti.import('/workspace/hq/src/server/mcp/memex-http-transport.ts');
  createTransport=async()=>createProjectHttpMemexTransport({...liveFixture,workspaceId:ctx.workspaceId,endpoint:'http://127.0.0.1:4319/mcp'},async(...args)=>{memoryReads++;return fetch(...args);});
 }
 if(phase==='seed'){
  if(!liveMemex){
   const scope={...ctx,projectId:snapshot.projectId,missionId,missionVersion:mission.updatedAt};
   const [a,b]=await Promise.all([snapshots.persist(scope,snapshot),snapshots.persist(scope,snapshot)]);assert.deepEqual(a,b);
  }
  const binding=liveMemex?liveFixture:snapshot;
  const attach=createOpenHandsMemoryAttachmentService({store:createOpenHandsMemoryAttachmentStore(),snapshots,
   resolveProjectBinding:async()=>({workspaceId:ctx.workspaceId,projectId:binding.projectId,namespace:binding.namespace,centerEntityId:binding.centerEntityId,namespaceScope:'project'}),
   createTransport:liveMemex?createTransport:async()=>{throw Error('Must reuse stored capture');}});
  const outcomes=liveMemex?[await attach(ctx,{...request,projectId:binding.projectId})]:await Promise.all([attach(ctx,{...request,projectId:binding.projectId}),attach(ctx,{...request,projectId:binding.projectId})]);
  assert.equal(outcomes.filter(r=>r.status==='attached').length,1);
  mission=await store.load(ctx.workspaceId,missionId);request.expectedUpdatedAt=mission.updatedAt;
  if(liveMemex){
   snapshot=mission.input._openhandsMemory;
   assert.ok(snapshot.content.includes('Original decision'));
   assert.ok(!snapshot.content.includes('FOREIGN_CONTENT'));
   assert.equal(memoryReads,2);
   const mutation=await fetch('http://127.0.0.1:4320/mutate',{method:'POST'});assert.equal(mutation.status,200);
   const fresh=await fetch('http://127.0.0.1:4319/mcp',{method:'POST',headers:{authorization:`Bearer ${liveFixture.readHandle}`,'content-type':'application/json'},body:JSON.stringify({jsonrpc:'2.0',id:9,method:'tools/call',params:{name:'agentmemory_context_pack',arguments:{namespace:binding.namespace,centerEntityId:binding.centerEntityId,format:'json'}}})});
   assert.ok(JSON.stringify(await fresh.json()).includes('New decision after capture'));
  }
  assert.deepEqual(mission.input._openhandsMemory,snapshot);
  const preview=await service(ctx,request);assert.equal(preview.status,'prepared');
  const result=await service(ctx,request,{confirm:true,expectedPayloadHash:preview.dossier.payloadHash});assert.equal(result.status,'reserved');
  if(liveMemex){assert.equal(memoryReads,2);assert.deepEqual(preview.dossier.memory,snapshot);}
 }else{
  const receipt=mission.input._openhandsReservation;assert.equal(receipt.state,'audit_recorded');
  request.expectedUpdatedAt=receipt.missionVersion;
  const result=await service(ctx,request,{confirm:true,expectedPayloadHash:receipt.payloadHash});
  assert.equal(result.status,lifecycle?'ineligible_mission':'already_reserved');
  if(liveMemex){
   const memory=mission.input._openhandsMemory;
   assert.ok(memory.content.includes('Original decision'));
   assert.ok(!memory.content.includes('New decision after capture'));
  }else assert.deepEqual(mission.input._openhandsMemory,snapshot);
 }
 assert.equal(await store.load('foreign-workspace',missionId),null);
 const db=createOptionalSupabaseAdminClient();
 const {data,error}=await db.from('action_ledger').select('action_type').eq('workspace_id',ctx.workspaceId).eq('mission_id',missionId);
 const expectedLedger=['mission.openhands_authorization','mission.openhands_memory_snapshot','mission.openhands_reservation'];
 if(lifecycle&&phase==='verify')expectedLedger.push('mission.openhands_launch_authorization','mission.openhands_tool_decision','mission.openhands_tool_consumption');
 assert.equal(error,null);assert.deepEqual(data.map(r=>r.action_type).sort(),expectedLedger.sort());
 if(liveMemex){
  const {data:captures,error:captureError}=await db.from('action_ledger').select('payload').eq('workspace_id',ctx.workspaceId).eq('mission_id',missionId).eq('action_type','mission.openhands_memory_snapshot');
  assert.equal(captureError,null);assert.equal(captures.length,1);
  assert.deepEqual(captures[0].payload,mission.input._openhandsMemory);
 }
 if(lifecycle){
  const {createOpenHandsLaunchService}=await load('openhands-launch.ts');
  const {createOpenHandsLaunchStore}=await load('openhands-launch-store.ts');
  const runtimeImage=syntheticProvider?'sha256:ecfafc87bc148d922dd4d43c3c5d3bb80f4a0828e4ff9af22ef80b7bd5c2924d':process.env.QUALIFICATION_PERMISSION_WORKER==='1'
   ?'sha256:3d8c97af6b8f1e6979596709f659124ca8f0319d5949e0f6f06f9c0287a7e11e'
   :'sha256:152df564b18fd7381e0bdfdd18ff57918eb9fa9a6e1d47a4820318e34c159da2';
  const config={imageDigest:dockerJob?runtimeImage:'sha256:'+'a'.repeat(64),executorVersion:'1.50.0',runnerId:'qualification',permissionPolicy:'deny',...request.budget,hardTokenLimitEnforced:false};
  if(providerBinding)config.providerProfile={id:'synthetic-policy',policySha256:'1'.repeat(64),provider:'claude',authentication:'subscription',network:'restricted-proxy',accountConnectors:'disabled'};
  if(syntheticProvider)config.providerProfile=JSON.parse(process.env.QUALIFICATION_PROVIDER_PROFILE);
  if(phase==='seed'){
   const launches=createOpenHandsLaunchService({store:()=>createOpenHandsLaunchStore()});
   const preview=await launches(ctx,{missionId,config});assert.equal(preview.status,'prepared');
   const acquired=await launches(ctx,{missionId,config},{confirm:true,expectedLaunchHash:preview.binding.launchHash});assert.equal(acquired.status,'claimed');
   const {createPendingOpenHandsLaunchReader}=await load('openhands-pending-launches.ts');
   const pendingReader=createPendingOpenHandsLaunchReader();
   const pending=await pendingReader({context:{...ctx,runnerId:config.runnerId},config});
   assert.equal(pending.status,'ready');assert.equal(pending.jobs.length,1);assert.equal(pending.jobs[0].launchId,acquired.claim.launchId);
   if(providerBinding||syntheticProvider){
    const withoutPolicy={...config};delete withoutPolicy.providerProfile;
    for(const altered of [withoutPolicy,{...config,providerProfile:{...config.providerProfile,policySha256:'2'.repeat(64)}}]){
     const rejected=await pendingReader({context:{...ctx,runnerId:config.runnerId},config:altered});
     assert.equal(rejected.status,'ready');assert.equal(rejected.jobs.length,0);assert.equal(rejected.rejected,1);
    }
    const recorded=await db.from('action_ledger').select('payload').eq('workspace_id',ctx.workspaceId).eq('mission_id',missionId).eq('action_type','mission.openhands_launch_authorization');
    assert.equal(recorded.error,null);assert.equal(recorded.data.length,1);
    assert.deepEqual(recorded.data[0].payload.config.providerProfile,config.providerProfile);
    console.log(JSON.stringify({actualProviderPolicyPersistence:true,changedPolicyExcluded:true,removedPolicyExcluded:true,syntheticPolicy:true}));
   }
   const foreignPending=await pendingReader({context:{...ctx,workspaceId:'foreign',runnerId:config.runnerId},config});
   assert.equal(foreignPending.status,'ready');assert.equal(foreignPending.jobs.length,0);
   console.log(JSON.stringify({canonicalPendingDiscovery:true,foreignDiscoveryExcluded:true}));
   if(process.getuid()===0){
    const profilePath='/run/hq-discovery/profile.json';
    await writeFile(profilePath,JSON.stringify({context:{...ctx,runnerId:config.runnerId},config}),{mode:0o600});
    async function discover(){return await new Promise((resolve,reject)=>{
     const child=spawn(process.execPath,['/workspace/hq/src/scripts/openhands-pending-launches.mjs',profilePath],{env:process.env,stdio:['ignore','pipe','pipe'],timeout:30000});
     let stdout='';child.stdout.on('data',chunk=>stdout+=chunk);child.stderr.resume();child.on('error',reject);
     child.on('close',code=>{try{resolve({code,result:JSON.parse(stdout)});}catch(error){reject(error);}});
    });}
    const discovered=await discover();assert.equal(discovered.code,0);assert.equal(discovered.result.jobs[0].launchId,acquired.claim.launchId);
    await chmod(profilePath,0o666);const unsafe=await discover();assert.equal(unsafe.code,2);assert.equal(unsafe.result.status,'unavailable');
    console.log(JSON.stringify({actualDiscoveryCli:true,writableProfileRejected:true}));
   }
   await writeFile('/tmp/lifecycle-job.json',JSON.stringify({context:{...ctx,runnerId:'qualification'},missionId,launchId:acquired.claim.launchId,config}));
   async function step(transition){
    return await new Promise((resolve,reject)=>{
     const child=spawn(process.execPath,['/workspace/hq/src/scripts/openhands-lifecycle.mjs','/tmp/lifecycle-job.json'],{env:process.env});
     let output='';child.stdout.on('data',chunk=>{output+=chunk;});child.stderr.resume();
     child.on('error',reject);child.on('close',code=>{try{resolve({code,result:JSON.parse(output)});}catch(e){reject(e);}});
     child.stdin.end(JSON.stringify(transition));
    });
   }
   if(dockerJob){
    const canonicalMission=await store.load(ctx.workspaceId,missionId);
    const dossier=await createOpenHandsLaunchStore().readSubmission(canonicalMission,ctx.actorId);
    assert.ok(dossier);assert.equal(dossier.payloadHash,acquired.claim.payloadHash);
    await writeFile('/tmp/host-ready.json',JSON.stringify({launchId:acquired.claim.launchId,config,dossier,context:{...ctx,runnerId:config.runnerId},workspaceId:ctx.workspaceId,url:process.env.NEXT_PUBLIC_SUPABASE_URL}));
    for(let i=0;;i++){
     try{await readFile('/tmp/host-done');break;}catch{}
     if(i>600)throw Error('Host dispatch timeout');
     await new Promise(resolve=>setTimeout(resolve,250));
    }
   }else for(const transition of [
    {expected:'claimed',next:'creation_requested'},
    {expected:'creation_requested',next:'container_created',containerId:'d'.repeat(64)},
    {expected:'container_created',next:'start_requested',containerId:'d'.repeat(64)},
    ...(reviewHost?[]:reviewService?[
     {expected:'start_requested',next:'running',containerId:'d'.repeat(64),sessionId:'synthetic'},
    ]:[{expected:'start_requested',next:'execution_finished',containerId:'d'.repeat(64),process:{exitCode:0,containerStopped:true,deadlineExceeded:false}}]),
   ]){const response=await step(transition);assert.equal(response.code,0);assert.equal(response.result.status,'recorded');}
   const repeat=await step({expected:'claimed',next:'creation_requested'});assert.equal(repeat.code,3);assert.equal(repeat.result.status,'conflict');
   const {createOpenHandsToolDecisionStore}=await load('openhands-tool-decision-store.ts');
   const toolStore=createOpenHandsToolDecisionStore();let toolNow=Date.now();
   let toolRequest={version:1,workspaceId:ctx.workspaceId,missionId,launchId:acquired.claim.launchId,runnerId:'qualification',
    containerId:'d'.repeat(64),sessionId:'synthetic',toolCallId:'synthetic-call',inputJson:'{"command":"synthetic-argument-never-store"}',
    options:[{optionId:'allow',kind:'allow_once'}],requestedAt:new Date(toolNow).toISOString(),expiresAt:new Date(toolNow+30000).toISOString()};
   if(reviewService){
    const {createOpenHandsToolReview}=await load('openhands-tool-review.ts');
    const {createOpenHandsToolService}=await load('openhands-tool-service.ts');
    const {bindToolPermission}=await load('openhands-tool-permission.ts');
    const tools=createOpenHandsToolService({launches:createOpenHandsLaunchStore,decisions:()=>toolStore});
    let pendingId='33333333-3333-4333-8333-333333333333';
    let review=createOpenHandsToolReview({loadPending:async(owner,id)=>
     owner.actorId===ctx.actorId&&owner.workspaceId===ctx.workspaceId&&id===pendingId
      ?{request:toolRequest,config,actorId:ctx.actorId,runnerId:'qualification'}:null,
     approve:tools.approve});
    if(reviewControl){
     const root='/run/oria-hq-control/';
     const current=await store.load(ctx.workspaceId,missionId);
     await writeFile(root+'fixture.json.tmp',JSON.stringify({request:toolRequest,config,actorId:ctx.actorId,
      hostFlow:reviewHost,url:process.env.NEXT_PUBLIC_SUPABASE_URL,startRequestedAt:current.input._openhandsLaunch.startRequestedAt}));
     await rename(root+'fixture.json.tmp',root+'fixture.json');
     for(let attempt=0;;attempt++){
      try{await readFile(root+'ready');break;}catch{}
      if(attempt>=80)throw Error('Control registry not ready');
      await new Promise(resolve=>setTimeout(resolve,50));
     }
     const {createOpenHandsToolInbox}=await load('openhands-tool-inbox.ts');
     const inbox=createOpenHandsToolInbox(acquired.claim.launchId);
     const listed=await inbox.list(ctx);assert.equal(listed.status,'ready');assert.equal(listed.items.length,1);
     assert.equal(listed.items[0].inputJson,toolRequest.inputJson);
     pendingId=listed.items[0].requestId;
     if(reviewHost){
      const {createOpenHandsControlClient}=await load('openhands-control-client.ts');
      const pending=await createOpenHandsControlClient(root+acquired.claim.launchId+'/review.sock').load(ctx,pendingId);
      assert.ok(pending);toolRequest=pending.request;toolNow=Date.now();
     }
     assert.deepEqual((await inbox.list({...ctx,workspaceId:'foreign'})).items,[]);
     review=(owner,selection)=>inbox.decide(owner,selection);
    }
    const selection={requestId:pendingId,expectedRequestHash:bindToolPermission(toolRequest,toolNow).requestHash,optionId:'allow'};
    assert.equal((await review({...ctx,actorId:'foreign-owner'},selection)).status,'not_found');
    assert.equal((await review(ctx,{...selection,expectedRequestHash:'0'.repeat(64)})).status,'changed_request');
    assert.equal((await review(ctx,{...selection,request:toolRequest})).status,'invalid_selection');
    assert.equal(await toolStore.read(toolRequest,ctx.actorId,toolNow),null);
    const approved=await review(ctx,selection);assert.equal(approved.status,'recorded');
    if(reviewControl){
     assert.equal(approved.notified,true);
     for(let attempt=0;;attempt++){
      try{await readFile('/run/oria-hq-control/notified');break;}catch{}
      if(attempt>=40)throw Error('Host notification not observed');
      await new Promise(resolve=>setTimeout(resolve,50));
     }
    }
    if(reviewHost){
     const response=JSON.parse(await readFile('/run/oria-hq-control/consumed','utf8'));
     assert.deepEqual(response,{outcome:{outcome:'selected',optionId:'allow'}});
    }
    const contenders=await Promise.all([step({operation:'consume_tool',request:toolRequest}),step({operation:'consume_tool',request:toolRequest})]);
    assert.equal(contenders.filter(x=>x.result.outcome.outcome==='selected'&&x.result.outcome.optionId==='allow').length,reviewHost?0:1);
    assert.equal(contenders.filter(x=>x.result.outcome.outcome==='cancelled').length,reviewHost?2:1);
    const finished=await step({expected:'running',next:'execution_finished',containerId:'d'.repeat(64),process:{exitCode:0,containerStopped:true,deadlineExceeded:false}});
    assert.equal(finished.result.status,'recorded');
    if(reviewControl)await writeFile('/run/oria-hq-control/done','');
    console.log(JSON.stringify({actualReviewService:true,actualPersistentDecision:true,concurrentLifecycleConsumers:2,selectedExactlyOnce:true,hostPendingSource:reviewControl?'actual-python-registry-synthetic-request':'synthetic',actualInboxAndControlSocket:reviewControl,actualPermissionHostAndAgentSocket:reviewHost,ownerAuthQualified:false}));
   }else await toolStore.persist(toolRequest,ctx.actorId,'allow',toolNow);
   const inactive=await step({operation:'consume_tool',request:toolRequest});
   assert.equal(inactive.code,0);assert.equal(inactive.result.outcome.outcome,'cancelled');
   const consumed=await Promise.all([toolStore.consume(toolRequest,ctx.actorId,toolNow),toolStore.consume(toolRequest,ctx.actorId,toolNow)]);
   assert.equal(consumed.filter(Boolean).length,reviewService?0:1);
   assert.equal(await toolStore.consume(toolRequest,ctx.actorId,toolNow),null);
   const toolRows=await db.from('action_ledger').select().eq('workspace_id',ctx.workspaceId).in('action_type',['mission.openhands_tool_decision','mission.openhands_tool_consumption']);
   assert.equal(toolRows.error,null);assert.equal(toolRows.data.length,2);
   assert.ok(!JSON.stringify(toolRows.data).includes('synthetic-argument-never-store'));
  }else{
   const restored=await store.load(ctx.workspaceId,missionId);
   assert.equal(restored.input._openhandsLaunch.state,'execution_finished');
   if(dockerJob){assert.match(restored.input._openhandsLaunch.containerId,/^[a-f0-9]{64}$/);assert.equal(restored.input._openhandsLaunch.process.exitCode,syntheticProvider?0:1);}
   else assert.equal(restored.input._openhandsLaunch.containerId,'d'.repeat(64));
   assert.equal(restored.status,'draft');
   if(providerBinding||syntheticProvider){
    const rows=await db.from('action_ledger').select('payload').eq('workspace_id',ctx.workspaceId).eq('mission_id',missionId).eq('action_type','mission.openhands_launch_authorization');
    assert.equal(rows.error,null);assert.equal(rows.data.length,1);
    assert.deepEqual(rows.data[0].payload.config.providerProfile,config.providerProfile);
    console.log(JSON.stringify({providerPolicySurvivedDatabaseRestart:true,syntheticPolicy:true}));
   }
  }
 }
 console.log(JSON.stringify({phase,actualHqStores:true,postgresAndPostgrest:true,localLifecycleProcesses:lifecycle,syntheticContainerIdentity:lifecycle&&!dockerJob,realDockerJob:dockerJob,realSignedMemexHttp:liveMemex,memoryReads,ledgerRows:data.length,foreignWorkspaceRejected:true,productionDatabaseUsed:false,ownerAuthQualified:false,rlsQualified:false,modelCalled:false}));
 if(process.env.QUALIFICATION_RECOVERY_REPORT==='1'){
  const {createOpenHandsRecoveryReader}=await load('openhands-recovery.ts');
  const reader=createOpenHandsRecoveryReader();
  const diagnostic=await reader(ctx,missionId);
  assert.equal(diagnostic.status,'ready');assert.equal(diagnostic.stale,false);
  assert.equal(diagnostic.containerState,'absent');assert.equal(diagnostic.networkState,'absent');
  assert.equal(diagnostic.canonicalState,'execution_finished');
  assert.equal((await reader({...ctx,actorId:'foreign'},missionId)).status,'not_found');
  assert.equal((await reader({...ctx,workspaceId:'foreign'},missionId)).status,'not_found');
  const readonly=await import('node:fs/promises');
  await assert.rejects(()=>readonly.writeFile('/run/oria-hq-reports/forbidden','no'),error=>error.code==='EROFS');
  if(phase==='verify')assert.equal(process.getuid(),1000);
  console.log(JSON.stringify({phase,actualHqRecoveryFileReader:true,hostPublishedReport:true,readOnlyMountVerified:true,foreignReaderDenied:true,readerUid:process.getuid()}));
 }
}finally{proxy.closeAllConnections();await new Promise(resolve=>proxy.close(resolve));}
