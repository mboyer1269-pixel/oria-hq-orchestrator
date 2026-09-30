import { runAntigravity } from './runner.mjs';
let input='';
try {
  for await(const chunk of process.stdin){input+=chunk;if(Buffer.byteLength(input)>70000)throw Error();}
  const r=JSON.parse(input);if(typeof r.runId!=='string'||r.runId.length>200)throw Error();
  const result=await runAntigravity({executable:'/opt/antigravity/antigravity',cwd:'/workspace',home:'/paperclip',prompt:r.prompt,timeoutMs:r.timeoutMs});
  process.stdout.write(JSON.stringify({runId:r.runId,result}));if(!result.ok)process.exitCode=1;
}catch{process.stdout.write(JSON.stringify({error:'invalid_remote_request'}));process.exitCode=1;}
