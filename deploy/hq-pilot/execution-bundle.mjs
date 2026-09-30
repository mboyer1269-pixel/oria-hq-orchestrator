/** Generate inactive operator configuration; never installs or starts services. */
import fs from 'node:fs';
import path from 'node:path';
import {createRequire} from 'node:module';
import {createHash} from 'node:crypto';
import {pathToFileURL} from 'node:url';

const digest=/^sha256:[a-f0-9]{64}$/;
const hostRoot='/var/lib/oria-hq/host-config';
const mappedRoot='/protected/hq';
function absoluteSource(value){
  return typeof value==='string' && value.startsWith('/') && value!=='/'
    && value.length<=4096 && !/[\x00-\x1f\x7f\\$]/.test(value)
    && path.posix.normalize(value)===value && !value.endsWith('/');
}
export async function buildBundle(input,hqRoot){
  if(!input || Object.keys(input).sort().join(',')!=='bridgeImage,profile,projectId,sourceRoot,webImage')throw Error('Exact bundle fields required');
  if(!digest.test(input.bridgeImage)||!digest.test(input.webImage))throw Error('Pinned images required');
  if(!absoluteSource(input.sourceRoot))throw Error('Canonical absolute source path required');
  if(typeof input.projectId!=='string'||!input.projectId.trim()||input.projectId.trim()!==input.projectId||input.projectId.length>160)throw Error('Project identity required');
  const root=fs.realpathSync(hqRoot);
  const require=createRequire(path.join(root,'package.json'));
  const {createJiti}=require('jiti');
  const jiti=createJiti(import.meta.url,{alias:{'@':path.join(root,'src'),'server-only':path.join(root,'src/scripts/smoke/server-only-stub.mjs')}});
  const {pendingLaunchProfileSchema}=await jiti.import(path.join(root,'src/server/missions/openhands-pending-launches.ts'));
  const profile=pendingLaunchProfileSchema.parse(input.profile);
  // Compose interpolates dollars even inside JSON string environment values.
  // Reject rather than silently modify canonical identifiers/configuration.
  if(JSON.stringify(profile).includes('$'))throw Error('Compose interpolation refused in profile');
  const consumer={bridgeCommand:['/usr/bin/docker','exec','--user','0:0','-i','hq-host-bridge','node'],
    bridgeScriptsRoot:'/workspace/hq/src/scripts',bridgeConfigRoot:mappedRoot,hostConfigRoot:hostRoot,
    profileFile:hostRoot+'/profile.json',registryFile:'/etc/oria-hq/project-sources.json',
    jobsRoot:'/var/lib/oria-hq/jobs',controlRoot:'/run/oria-hq-control'};
  const files={
    'profile.json':profile,
    'consumer.json':consumer,
    'project-sources.json':{version:1,entries:[{workspaceId:profile.context.workspaceId,projectId:input.projectId,runnerId:profile.context.runnerId,sourceRoot:input.sourceRoot}]},
    'hq.execution.overlay.json':{services:{hq:{image:input.webImage,environment:{
      ORIA_OPENHANDS_LAUNCH_CONFIG:JSON.stringify(profile.config),ORIA_ENABLE_OPENHANDS_LAUNCH:'0',
      ORIA_ENABLE_OPENHANDS_CONFIRMATION:'0',ORIA_ENABLE_OPENHANDS_TOOL_REVIEW:'0'}}}},
    'bridge.compose.json':{name:'oria-hq-execution',services:{bridge:{
      image:input.bridgeImage,container_name:'hq-host-bridge',profiles:['execution-bridge'],
      user:'1000:1000',entrypoint:['node'],command:['-e','setInterval(()=>{},3600000)'],
      restart:'no',read_only:true,cap_drop:['ALL'],security_opt:['no-new-privileges:true'],
      cpus:'1.0',mem_limit:'512m',memswap_limit:'512m',pids_limit:64,
      env_file:[{path:'/etc/oria-hq/bridge-runtime.env',format:'raw'}],
      environment:{NODE_ENV:'production',NEXT_TELEMETRY_DISABLED:'1',HOME:'/tmp/hq-bridge'},
      tmpfs:['/tmp:rw,nosuid,nodev,size=64m,mode=1777'],
      volumes:[{type:'bind',source:hostRoot,target:mappedRoot,read_only:true,bind:{create_host_path:false}}],
      networks:['hq-egress'],logging:{driver:'json-file',options:{'max-size':'10m','max-file':'2'}}
    }},networks:{'hq-egress':{name:'oria-hq-egress',external:true}}}
  };
  const encoded=Object.fromEntries(Object.entries(files).map(([name,value])=>[name,JSON.stringify(value,null,2)+'\n']));
  const manifest={version:1,activated:false,files:Object.fromEntries(Object.entries(encoded).map(([name,value])=>[name,createHash('sha256').update(value).digest('hex')]))};
  encoded['manifest.json']=JSON.stringify(manifest,null,2)+'\n';
  return encoded;
}

async function main(){
  const [hqRoot,inputFile,output]=process.argv.slice(2);
  if(!hqRoot||!inputFile||!output||process.argv.length!==5)throw Error('Expected HQ root, input JSON, new output directory');
  const bytes=fs.readFileSync(inputFile);if(bytes.length>16384)throw Error('Oversized input');
  const files=await buildBundle(JSON.parse(bytes.toString('utf8')),hqRoot);
  // Exclusive directory: retain any partial write for inspection, never overwrite.
  fs.mkdirSync(output,{mode:0o700});
  for(const [name,value]of Object.entries(files))fs.writeFileSync(path.join(output,name),value,{flag:'wx',mode:0o600});
  console.log(JSON.stringify({generatedFiles:Object.keys(files).length,activated:false,credentialsIncluded:false}));
}
if(process.argv[1]&&import.meta.url===pathToFileURL(path.resolve(process.argv[1])).href){
  main().catch(()=>{console.error('Execution bundle rejected or incomplete; no activation performed.');process.exitCode=1;});
}
