import { parseTerminalResult } from './contract.mjs';
const type='antigravity_plan_prototype';
const fail=errorCode=>({exitCode:1,signal:null,timedOut:false,errorCode,costUsd:null,clearSession:true});
export function createServerAdapter({loadTransport=()=>import('@paperclipai/adapter-utils/execution-target'),stopAndVerify,renderTask}={}) {
  const valid=c=>c?.config?.qualifiedRemoteRunner===true&&c.executionTarget?.kind==='remote'&&c.executionTarget.transport==='ssh'&&c.executionTarget.spec?.strictHostKeyChecking===true&&!!c.executionTarget.spec?.knownHosts?.trim()&&c.executionTarget.remoteCwd==='/workspace'&&typeof stopAndVerify==='function'&&typeof renderTask==='function'&&typeof c.executionTarget.environmentId==='string'&&!!c.executionTarget.environmentId;
  return {type,supportsLocalAgentJwt:false,
    async testEnvironment(c){return {adapterType:type,status:valid(c)?'pass':'fail',testedAt:new Date().toISOString(),checks:[{code:'remote_contract',level:valid(c)?'info':'error',message:'Checks host SSH contract only; no provider probe.'}]};},
    async execute(c){
      if(!valid(c))return fail('unsafe_or_missing_remote_runner');
      let prompt;try{prompt=await renderTask(c);}catch{return fail('task_render_failed');}const timeoutMs=c.config.timeoutMs??60000;
      if(typeof prompt!=='string'||!prompt.trim()||/^\s*\//m.test(prompt)||Buffer.byteLength(prompt)>65536||!Number.isSafeInteger(timeoutMs)||timeoutMs<1000||timeoutMs>300000||typeof c.runId!=='string'||!c.runId)return fail('invalid_bounded_task');
      if(c.signal?.aborted)return fail('cancelled');
      let t;try{t=await loadTransport();}catch{return fail('host_transport_unavailable');}
      let stopping;const stop=()=>stopping??=(Promise.resolve().then(()=>stopAndVerify(c)).then(r=>r?.stopped===true&&r.scope==='exclusive_runner'&&r.runId===c.runId&&r.environmentId===c.executionTarget.environmentId,()=>false));
      const cancel=()=>{void stop();};c.signal?.addEventListener('abort',cancel,{once:true});
      try{
        await c.onCancellationReady?.();if(c.signal?.aborted){await stop();return fail('cancelled');}
        c.onDispatch?.();
        const p=await t.runAdapterExecutionTargetProcess(c.runId,c.executionTarget,'/bin/sh',['/opt/oria-runner/bounded-command.sh',String(Math.ceil(timeoutMs/1000)+3),'node','/opt/oria-antigravity/remote-entry.mjs'],{cwd:'/workspace',env:{HOME:'/paperclip'},timeoutSec:Math.ceil(timeoutMs/1000)+10,graceSec:2,stdin:JSON.stringify({prompt,timeoutMs,runId:c.runId}),onSpawn:c.onSpawn,onLog:async()=>{}});
        if(c.signal?.aborted||p.timedOut||p.signal||p.exitCode!==0)return {...fail(c.signal?.aborted?'cancelled':'remote_failed'),timedOut:!!p.timedOut,errorMeta:{stopConfirmed:await stop(),retryAuthorized:false}};
        if(p.stderr?.trim()||Buffer.byteLength(p.stdout??'')>1100000)throw Error();
        const e=JSON.parse(p.stdout);if(e.runId!==c.runId||e.result?.ok!==true)throw Error();const r=e.result;
        const result=parseTerminalResult({status:r.providerStatus,conversation_id:r.sessionId,response:r.response,duration_seconds:r.durationSeconds,num_turns:1,usage:r.usage});
        if(!await stop())return fail('remote_stop_unverified');await c.onProviderStopped?.();
        return {exitCode:0,signal:null,timedOut:false,costUsd:null,clearSession:true,usageBasis:result.usage?'per_run':null,...(result.usage?{usage:{inputTokens:result.usage.input_tokens,outputTokens:result.usage.output_tokens,cachedInputTokens:result.usage.cache_read_tokens}}:{}),summary:result.response,resultJson:{...result,deliveryVerified:false,retryAuthorized:false,runId:c.runId}};
      }catch{return {...fail('remote_execution_failed'),errorMeta:{stopConfirmed:await stop(),retryAuthorized:false}};}
      finally{c.signal?.removeEventListener('abort',cancel);}
    }
  };
}
