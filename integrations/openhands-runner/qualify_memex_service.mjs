// Disposable fixture service only. Harness shares a network-none namespace.
// Never run on a production network or mount a production database/secret.
import {createServer} from 'node:http';
import {randomBytes} from 'node:crypto';
import * as graph from '/app/src/graph.ts';
import {createHttpApp} from '/app/src/mcp/unified-server.ts';
import {mintHandle} from '/app/src/mcp/handles.ts';
const namespace='org:synthetic-project-a';
const secret=randomBytes(32).toString('hex');
process.env.AGENTMEMORY_HANDLE_SECRET=secret;
process.env.GATEWAY_DEFAULT_ACCESS='read_only';
delete process.env.GATEWAY_TOKEN;
graph.initGraph(':memory:');
graph.addEntity({id:'anchor-a',type:'Project',namespace,name:'Original decision 🧪',source:'reviewed:test',properties:{status:'verified'}});
graph.addEntity({id:'foreign-b',type:'Project',namespace:'org:synthetic-project-b',name:'FOREIGN_CONTENT_MUST_NOT_APPEAR',source:'reviewed:test',properties:{status:'verified'}});
const handle=mintHandle('disposable-hq-qualification','read_only',secret,600,new Date(),[namespace]);
createHttpApp().listen(4319,'127.0.0.1');
let changed=false;
createServer((req,res)=>{
 res.setHeader('content-type','application/json');
 if(req.method==='GET'&&req.url==='/fixture'){
  res.end(JSON.stringify({namespace,projectId:'project-a',centerEntityId:'anchor-a',readHandle:handle}));
 }else if(req.method==='POST'&&req.url==='/mutate'){
  if(!changed){
   graph.addEntity({id:'later-decision',type:'Decision',namespace,name:'New decision after capture',source:'reviewed:test',properties:{status:'verified'}});
   graph.addRelation({id:'later-link',type:'RELATED_TO',sourceId:'anchor-a',targetId:'later-decision',namespace,source:'reviewed:test'});
   changed=true;
  }
  res.end(JSON.stringify({changed}));
 }else res.writeHead(404).end('{}');
}).listen(4320,'127.0.0.1');
