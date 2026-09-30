import fs from 'node:fs';
import path from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {pathToFileURL} from 'node:url';

const roots=new Set(['src','public','config','docs','scripts','.github']);
const rootFiles=new Set(['AGENTS.md','SOUL.md','README.md','ARCHITECTURE.md','CLAUDE.md','PROJECT.md','ORIGINAL_REQUEST.md','Dockerfile','.dockerignore','.gitignore','.gitattributes','.env.example','.npmrc','package.json','package-lock.json','run-tests.mjs','next.config.ts','next-env.d.ts','tsconfig.json','postcss.config.mjs','eslint.config.mjs','vitest.config.ts','skills-lock.json']);
const textExtensions=new Set(['.ts','.tsx','.js','.jsx','.mjs','.cjs','.json','.md','.mdx','.txt','.css','.scss','.html','.svg','.sql','.yaml','.yml','.toml','.sh','.ps1','.py','.xml','.csv']);
const forbiddenSegments=new Set(['.git','node_modules','.next','.turbo','.cache','coverage','output','dist','build','__pycache__','.ssh','.aws','.azure','secrets','credentials']);
const binaryExtensions=new Set(['.png','.jpg','.jpeg','.gif','.webp','.ico','.woff','.woff2']);
// Defense in depth, not a complete secret detector. Export only a reviewed source
// repository; arbitrary hardcoded secrets and private prose cannot be guaranteed absent.
// Runtime memory and document data are intentionally excluded even if a test expects them.
// Dependencies and Git metadata must be provisioned separately in the isolated workspace.
export function classifyPath(relative){
 if(typeof relative!=='string'||!relative||relative.includes('\\')||relative.startsWith('/')||relative.includes(':')||relative.split('/').some(p=>!p||p==='.'||p==='..'))throw Error('Unsafe inventory path');
 const parts=relative.split('/');const name=parts.at(-1);const lower=name.toLowerCase();
 if(parts.some(p=>forbiddenSegments.has(p.toLowerCase()))||((lower==='.env'||lower.startsWith('.env.'))&&relative!=='.env.example')||/\.(?:pem|key|p12|pfx|sqlite(?:3)?|db|log|exe|dll|zip|tar|gz|pdf|docx|xlsx)$/i.test(name)||/^(?:id_rsa|id_ed25519|credentials(?:\..*)?|token(?:\..*)?|auth\.json)$/i.test(name))return 'private_or_runtime';
 const selected=rootFiles.has(relative)||roots.has(parts[0])||(parts[0]==='db'&&['.sql','.md'].includes(path.posix.extname(relative).toLowerCase()));
 if(!selected)return 'outside_source_scope';
 const ext=path.posix.extname(relative).toLowerCase();
 if(rootFiles.has(relative)||textExtensions.has(ext))return 'text';
 if(binaryExtensions.has(ext)&&(parts[0]==='public'||relative==='src/app/favicon.ico'))return 'public_asset';
 return 'unsupported_asset';
}
export function validateEnvTemplate(text){
 for(const line of text.split(/\r?\n/)){
  if(!line.trim()||line.trimStart().startsWith('#'))continue;
  const match=/^([A-Z][A-Z0-9_]*)=(.*)$/.exec(line);
  if(!match||!(match[2]===''||(/^(?:ORIA_ENABLE_[A-Z0-9_]+|SMOKE_WRITE)$/.test(match[1])&&match[2]==='0')))throw Error('Environment template contains a nonempty or unsupported value');
 }
}
function validateText(bytes,relative){
 let text;try{text=new TextDecoder('utf-8',{fatal:true}).decode(bytes);}catch{throw Error(`Non-text source refused: ${relative}`);}
 if(text.includes('\0'))throw Error(`Binary source refused: ${relative}`);
 if(/-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----|(?:sk-proj-|sk-ant-api\d+-)[A-Za-z0-9_-]{25,}|(?:ghp_|github_pat_)[A-Za-z0-9_]{30,}|AKIA[0-9A-Z]{16}|(?:opr1|amh1)\.[A-Za-z0-9_-]{43,}/.test(text))throw Error(`Credential-like source refused: ${relative}`);
 if(relative==='.env.example')validateEnvTemplate(text);
 if(relative==='.npmrc'){
  if(/auth|registry|https?:\/\//i.test(text))throw Error('Private npm configuration refused');
  const settings=text.split(/\r?\n/).map(line=>line.trim()).filter(line=>line&&!line.startsWith('#')&&!line.startsWith(';'));
  if(settings.length!==1||settings[0]!=='engine-strict=true')throw Error('Unsupported npm configuration refused');
 }
}
function validateAsset(bytes,relative){
 const ext=path.posix.extname(relative).toLowerCase();const head=bytes.subarray(0,12);
 const valid=ext==='.png'?head.subarray(0,8).equals(Buffer.from([137,80,78,71,13,10,26,10])):['.jpg','.jpeg'].includes(ext)?head[0]===255&&head[1]===216&&head[2]===255:ext==='.gif'?head.toString('ascii').startsWith('GIF8'):ext==='.webp'?head.toString('ascii').startsWith('RIFF')&&head.toString('ascii',8,12)==='WEBP':ext==='.ico'?head.subarray(0,4).equals(Buffer.from([0,0,1,0])):ext==='.woff'?head.toString('ascii',0,4)==='wOFF':ext==='.woff2'?head.toString('ascii',0,4)==='wOF2':false;
 if(!valid)throw Error(`Invalid public asset: ${relative}`);
}
function checkedFile(source,relative){
 let current=source;
 for(const part of relative.split('/')){current=path.join(current,part);const stat=fs.lstatSync(current);if(stat.isSymbolicLink())throw Error(`Symlink refused: ${relative}`);}
 const stat=fs.statSync(current);if(!stat.isFile()||stat.size>20*1024*1024)throw Error(`Nonregular/oversized source refused: ${relative}`);
 const bytes=fs.readFileSync(current);return bytes;
}
export function planDevelopmentSnapshot(sourceArg){
 const source=fs.realpathSync(sourceArg);
 const top=fs.realpathSync(execFileSync('git',['-C',source,'rev-parse','--show-toplevel'],{encoding:'utf8'}).trim());if(top!==source)throw Error('Expected repository root');
 const inventory=execFileSync('git',['-C',source,'ls-files','--cached','--others','--exclude-standard','-z'],{maxBuffer:32*1024*1024}).toString('utf8').split('\0').filter(Boolean);
 const files=[];const excluded=[];const casePaths=new Set();
 for(const relative of [...new Set(inventory)].sort()){
  const classification=classifyPath(relative);
  if(!['text','public_asset'].includes(classification)){excluded.push({path:relative,reason:classification});continue;}
  if(casePaths.has(relative.toLowerCase()))throw Error('Case-colliding source paths');casePaths.add(relative.toLowerCase());
  try{fs.lstatSync(path.join(source,relative));}catch(error){if(error.code==='ENOENT'){excluded.push({path:relative,reason:'deleted_working_file'});continue;}throw error;}
  const bytes=checkedFile(source,relative);if(classification==='text')validateText(bytes,relative);else validateAsset(bytes,relative);
  files.push({path:relative,sha256:createHash('sha256').update(bytes).digest('hex'),size:bytes.length,bytes});
 }
 for(const required of ['package.json','package-lock.json','run-tests.mjs','AGENTS.md','SOUL.md','tsconfig.json'])if(!files.some(f=>f.path===required))throw Error(`Required development file missing: ${required}`);
 if(!files.some(f=>f.path.startsWith('src/')&&f.path.endsWith('.test.mjs')))throw Error('Development tests missing');
 return {source,files,excluded};
}
export function exportDevelopmentSnapshot(sourceArg,destinationArg){
 const plan=planDevelopmentSnapshot(sourceArg);const destination=path.resolve(destinationArg);
 if(fs.existsSync(destination))throw Error('Destination already exists');
 const parent=fs.realpathSync(path.dirname(destination));const resolved=path.join(parent,path.basename(destination));
 if(resolved===plan.source||resolved.startsWith(plan.source+path.sep))throw Error('Destination must be outside source');
 // All inputs are validated before creating any output. Copy exactly the validated bytes.
 fs.mkdirSync(resolved);
 for(const file of plan.files){const target=path.join(resolved,file.path);fs.mkdirSync(path.dirname(target),{recursive:true});fs.writeFileSync(target,file.bytes,{flag:'wx'});}
 const manifest={version:1,purpose:'development-source',gitMetadataIncluded:false,dependenciesIncluded:false,files:plan.files.map(({bytes,...entry})=>entry),excluded:plan.excluded};
 fs.writeFileSync(path.join(resolved,'development-source-manifest.json'),JSON.stringify(manifest,null,2)+'\n',{flag:'wx'});
 return {files:manifest.files.length,excluded:manifest.excluded.length};
}
if(process.argv[1]&&import.meta.url===pathToFileURL(path.resolve(process.argv[1])).href){
 const [source,destination]=process.argv.slice(2);if(!source||!destination)throw Error('Expected repository root and new development snapshot directory');
 console.log(JSON.stringify(exportDevelopmentSnapshot(source,destination)));
}
