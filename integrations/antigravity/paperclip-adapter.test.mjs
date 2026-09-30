import test from 'node:test';
import assert from 'node:assert/strict';
import {createServerAdapter as factory} from './paperclip-adapter.mjs';
const createServerAdapter=options=>factory({renderTask:c=>c.context.prompt,stopAndVerify:async c=>{await c.stopRemoteStartup();return {stopped:true,scope:'exclusive_runner',runId:c.runId,environmentId:c.executionTarget.environmentId};},...options});
const result={ok:true,providerStatus:'SUCCESS',sessionId:'00000000-0000-4000-8000-000000000001',response:'plan',durationSeconds:1,usage:null};
const context=()=>({runId:'run-1',config:{qualifiedRemoteRunner:true},context:{prompt:'Plan a small change'},executionTarget:{kind:'remote',transport:'ssh',environmentId:'runner-1',remoteCwd:'/workspace',spec:{strictHostKeyChecking:true,knownHosts:'fixture'}},stopRemoteStartup:async()=>{}});
test('qualified SSH dispatch is bounded and never forwards host or application secrets',async()=>{
 let args,stopped=false;const c=context();c.authToken='not-forwarded';c.stopRemoteStartup=async()=>{stopped=true;};
 const adapter=createServerAdapter({loadTransport:async()=>({runAdapterExecutionTargetProcess:async(...a)=>{args=a;return{exitCode:0,stdout:JSON.stringify({runId:c.runId,result}),stderr:''};}})});
 const r=await adapter.execute(c);assert.equal(r.exitCode,0);assert.equal(stopped,true);assert.deepEqual(args[4].env,{HOME:'/paperclip'});assert.equal(args[3][1],'63');assert.equal(r.costUsd,null);assert.equal(r.usage,undefined);assert.equal(r.resultJson.deliveryVerified,false);
});
test('missing isolation rejects before importing transport',async()=>{let called=false;const a=createServerAdapter({loadTransport:async()=>{called=true;}});const c=context();delete c.executionTarget.environmentId;assert.equal((await a.execute(c)).exitCode,1);assert.equal(called,false);});
test('disconnect fails and requires verified host stop without retry',async()=>{let stopped=0;const c=context();c.stopRemoteStartup=async()=>{stopped++;};const a=createServerAdapter({loadTransport:async()=>({runAdapterExecutionTargetProcess:async()=>({exitCode:255,stdout:'',stderr:''})})});const r=await a.execute(c);assert.equal(r.exitCode,1);assert.equal(stopped,1);assert.equal(r.errorMeta.retryAuthorized,false);});
test('cancelled execution awaits host termination even if transport returns success',async()=>{const c=context(),ac=new AbortController();c.signal=ac.signal;let stopped=0;c.stopRemoteStartup=async()=>{stopped++;};const a=createServerAdapter({loadTransport:async()=>({runAdapterExecutionTargetProcess:async()=>{ac.abort();return{exitCode:0,stdout:JSON.stringify({runId:c.runId,result}),stderr:''};}})});const r=await a.execute(c);assert.equal(r.errorCode,'cancelled');assert.equal(stopped,1);});

test('false or mismatched stop receipts and rejected stops cannot yield success',async()=>{
 for(const stopAndVerify of [async()=>undefined,async()=>({stopped:false}),async()=>({stopped:true,scope:'exclusive_runner',runId:'wrong',environmentId:'runner-1'}),async()=>{throw Error();}]){
 const c=context();const a=createServerAdapter({stopAndVerify,loadTransport:async()=>({runAdapterExecutionTargetProcess:async()=>({exitCode:0,stdout:JSON.stringify({runId:c.runId,result}),stderr:''})})});assert.equal((await a.execute(c)).errorCode,'remote_stop_unverified');}
});
test('timeout reports unverified stop and never authorizes replay',async()=>{
 const a=createServerAdapter({stopAndVerify:async()=>undefined,loadTransport:async()=>({runAdapterExecutionTargetProcess:async()=>({exitCode:null,timedOut:true,stdout:'',stderr:''})})});const r=await a.execute(context());assert.equal(r.timedOut,true);assert.equal(r.errorMeta.stopConfirmed,false);assert.equal(r.errorMeta.retryAuthorized,false);
});
