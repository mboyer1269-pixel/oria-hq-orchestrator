// Operator-side, inside the existing Memex container. Proposal only; never approve
// or publish. The transient scoped handle is not printed or written to disk.
import fs from 'node:fs';
import {mintHandle} from '/app/src/mcp/handles.ts';
const namespace='org:project:oria-hq';
const subject='hq-project-bootstrap';
const requestId='oria-hq-project-foundation-v1';
const content=[
 'Projet : ORIA HQ.',
 'Objectif demandé par Michael : construire un assistant de développement accessible dans son application web, capable de planifier, répartir, réaliser et vérifier des missions, puis utiliser cet outil pour améliorer ORIA HQ.',
 'Direction retenue à qualifier : OpenHands pour exécuter le travail de développement, HQ pour le pilotage, Memex pour le contexte propre au projet.',
 'Contraintes : limiter les tokens et le contexte transmis, réutiliser les outils existants, travailler dans des environnements isolés, présenter les preuves et les limites, préserver les modifications existantes, ne pas déployer automatiquement.',
 'Une préparation ou une réservation de mission ne prouve pas son exécution. Une capacité est déclarée opérationnelle seulement après une validation correspondante.',
 'AgentMemory local est réservé à la mémoire de développement ; il ne doit pas être confondu avec la mémoire du projet hébergée dans Memex.'
].join('\n');
const entity={id:'oria-hq-project-foundation-v1',type:'Project',namespace,name:'ORIA HQ — cadre du projet',
 source:'user-direction:oria-hq-integration',properties:{status:'verified',zone:'agent',content}};
if(!process.argv.includes('--submit')){
 console.log(JSON.stringify({namespace,requestId,content,suggestedEntity:entity,publication:false},null,2));
}else{
 const secret=fs.readFileSync('/run/secrets/handle-signing-key','utf8').trim();
 const handle=mintHandle(subject,'read_write',secret,120,new Date(),[namespace]);
 const response=await fetch('http://127.0.0.1:3000/mcp',{method:'POST',
  headers:{authorization:`Bearer ${handle}`,'content-type':'application/json'},signal:AbortSignal.timeout(10000),
  body:JSON.stringify({jsonrpc:'2.0',id:1,method:'tools/call',params:{name:'agentmemory_submit_proposal',arguments:{
   namespace,tenant:namespace,requestId,content,provenance:'user-direction:oria-hq-integration',
   suggestedEntities:JSON.stringify([entity]),suggestedRelations:'[]',confidence:1}}})});
 const body=await response.json();
 if(!response.ok||body.error||body.result?.isError)throw Error('Proposal submission failed; inspect receipt before retry');
 // Return the proposal status/identity, never the signed handle.
 console.log(JSON.stringify({namespace,requestId,receipt:body.result,publicationRequested:false}));
}
