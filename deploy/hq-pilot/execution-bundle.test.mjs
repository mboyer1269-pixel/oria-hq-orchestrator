import test from 'node:test';
import assert from 'node:assert/strict';
import {buildBundle} from './execution-bundle.mjs';
const root=process.env.HQ_SOURCE_ROOT;
if(!root)throw Error('HQ_SOURCE_ROOT must identify the real HQ source and dependencies');
const input={bridgeImage:'sha256:'+'a'.repeat(64),webImage:'sha256:'+'b'.repeat(64),projectId:'project',sourceRoot:'/opt/project-source',
  profile:{context:{workspaceId:'workspace',actorId:'owner',runnerId:'runner'},config:{imageDigest:'sha256:'+'c'.repeat(64),executorVersion:'1.50.0',runnerId:'runner',permissionPolicy:'deny',maxCostCents:100,maxTokens:10000,maxIterations:10,timeoutSeconds:120,hardTokenLimitEnforced:false}}};
test('one canonical profile produces identical web/consumer settings and inactive isolated bridge',async()=>{
  const result=await buildBundle(input,root);
  const profile=JSON.parse(result['profile.json']);
  const web=JSON.parse(result['hq.execution.overlay.json']).services.hq;
  assert.deepEqual(JSON.parse(web.environment.ORIA_OPENHANDS_LAUNCH_CONFIG),profile.config);
  assert.equal(web.environment.ORIA_ENABLE_OPENHANDS_LAUNCH,'0');
  const consumer=JSON.parse(result['consumer.json']);
  const bridge=JSON.parse(result['bridge.compose.json']).services.bridge;
  assert.deepEqual(consumer.bridgeCommand.slice(0,5),['/usr/bin/docker','exec','--user','0:0','-i']);
  assert.equal(bridge.volumes[0].source,consumer.hostConfigRoot);
  assert.equal(bridge.volumes[0].target,consumer.bridgeConfigRoot);
  assert.equal(bridge.volumes[0].read_only,true);
  assert.equal(bridge.volumes.length,1);assert.equal(bridge.ports,undefined);
  assert.equal(bridge.user,'1000:1000');assert.deepEqual(bridge.profiles,['execution-bridge']);
  assert.equal(JSON.parse(result['project-sources.json']).entries[0].runnerId,profile.config.runnerId);
});
test('rejects inconsistent runner, unsupported policy, excessive budget and unknown credentials',async()=>{
  for(const patch of [{runnerId:'different'},{permissionPolicy:'allow'},{maxTokens:200001},{apiKey:'sentinel'}]){
    await assert.rejects(buildBundle({...input,profile:{...input.profile,config:{...input.profile.config,...patch}}},root));
  }
  await assert.rejects(buildBundle({...input,credential:'sentinel'},root));
});
test('rejects floating images and ambiguous paths before writing',async()=>{
  for(const sourceRoot of ['relative','/','/opt/../etc','/opt/project/','/opt/$HOME','/opt/test\nvalue'])await assert.rejects(buildBundle({...input,sourceRoot},root));
  await assert.rejects(buildBundle({...input,webImage:'latest'},root));
  await assert.rejects(buildBundle({...input,profile:{...input.profile,context:{...input.profile.context,actorId:'${OWNER}'}}},root));
});
