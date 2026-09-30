// Synthetic cross-language fixture from the actual HQ builders. No DB or model.
import path from 'node:path';
import { createRequire } from 'node:module';
import { writeFile } from 'node:fs/promises';
const [hqRoot, output] = process.argv.slice(2);
if (!hqRoot || !output) throw Error('Usage: node export_hq_memory_fixture.mjs <HQ root> <output JSON>');
const require = createRequire(path.join(hqRoot, 'package.json'));
const { createJiti } = require('jiti');
const jiti = createJiti(import.meta.url, { alias: { '@': path.join(hqRoot, 'src'),
  'server-only': path.join(hqRoot, 'src/scripts/smoke/server-only-stub.mjs') } });
const load = name => jiti.import(path.join(hqRoot, 'src/server/missions', name));
const { createDevelopmentService } = await load('development-mission.ts');
const { prepareOpenHandsMemoryContext } = await load('openhands-memory-context.ts');
const { buildOpenHandsSubmission } = await load('openhands-submission.ts');
let mission;
await createDevelopmentService({enabled:()=>true,store:()=>({save:async m=>(mission=m),load:async()=>mission})}).create({
 requestId:'714ac9b7-6bce-4eb4-b3bd-08d3df8ad46e',title:'Synthetic memory contract',objective:'Verify Unicode 🧪 exchange',scope:'Fixture only',acceptanceCriteria:'Receiver validates exact context'},
 {workspaceId:'synthetic-a',modeId:'hq',actorId:'synthetic-owner'});
const entity={id:'anchor',namespace:'org:synthetic-project',type:'Project',name:'Décision 🧪',source:'reviewed',properties:{status:'verified'}};
const memory=await prepareOpenHandsMemoryContext({workspaceId:'synthetic-a',projectId:'synthetic-project',
 resolveProjectBinding:async()=>({workspaceId:'synthetic-a',projectId:'synthetic-project',namespace:entity.namespace,namespaceScope:'project',centerEntityId:entity.id}),
 transport:{listTools:async()=>['agentmemory_context_pack'],close:async()=>{},callTool:async()=>JSON.stringify({graphContext:{namespace:entity.namespace,tenant:entity.namespace,centerEntity:entity,entities:[entity],relations:[]},provenance:[{id:entity.id,source:entity.source}]})},
 now:()=>new Date('2026-09-30T12:00:00.000Z')});
if(memory.status!=='ready')throw Error('Snapshot unavailable');
mission.input._openhandsMemory=memory.snapshot;
mission.updatedAt='2026-09-30T12:00:00.000Z';
const result=buildOpenHandsSubmission(mission,'synthetic-a',{missionId:mission.id,expectedUpdatedAt:mission.updatedAt,
 commitSha:'a'.repeat(40),executorVersion:'1.50.0',budget:{maxCostCents:100,maxTokens:10000,maxIterations:2,timeoutSeconds:60}});
if(result.status!=='prepared')throw Error('Dossier unavailable');
await writeFile(output,JSON.stringify(result.dossier,null,2)+'\n','utf8');
