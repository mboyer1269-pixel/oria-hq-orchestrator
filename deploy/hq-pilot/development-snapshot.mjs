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
function rejectUnsafe(relative){
 if(typeof relative!=='string'||!relative||relative.includes('\\')||relative.startsWith('/')||relative.includes(':')||relative.split('/').some(part=>!part||part==='.'||part==='..'))throw Error('Unsafe inventory path');
}
export function classifyPath(relative){
 rejectUnsafe(relative);
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
// Node's synchronous API has no openat. On Linux, opening /proc/self/fd/<dirfd>/<name>
// with O_NOFOLLOW looks the name up in the directory inode already held. That is the
// supported walk. It refuses a symlink at that name. It does not run on native Windows
// and it has no less-safe fallback. WSL2 is Linux for this test; this file does not
// prove a particular Windows machine. A mount on a real directory is not rejected.
const fileFlags=()=>fs.constants.O_RDONLY|fs.constants.O_NOFOLLOW|fs.constants.O_NONBLOCK;
const directoryFlags=()=>fs.constants.O_RDONLY|fs.constants.O_DIRECTORY|fs.constants.O_NOFOLLOW;
const platformRefusal='Development snapshot requires Linux with /proc/self/fd. Native Windows is not supported; use WSL2. There is no fallback.';
export function assertDevelopmentSnapshotPlatform(env={}){
 const platform=env.platform??process.platform;
 const proc=env.proc??'/proc/self/fd';
 if(platform!=='linux')throw Error(platformRefusal);
 let stat;
 try{stat=fs.statSync(proc);}catch{throw Error(platformRefusal);}
 if(!stat.isDirectory())throw Error(platformRefusal);
 if(!Number.isInteger(fs.constants.O_NOFOLLOW)||!Number.isInteger(fs.constants.O_DIRECTORY)||!Number.isInteger(fs.constants.O_NONBLOCK))throw Error(platformRefusal);
}
function symlinkRefusal(relative){return Error(`Symlink refused: ${relative}`);}
function deletedFile(relative){const error=Error(`Deleted working file: ${relative}`);error.code='ENOENT';return error;}
function procPath(dirfd,name){
 if(typeof name!=='string'||!name||name.includes('/')||name==='.'||name==='..')throw Error('Unsafe inventory path');
 return `/proc/self/fd/${dirfd}/${name}`;
}
function assertContained(fd,root,relative){
 const linked=path.resolve(fs.readlinkSync(`/proc/self/fd/${fd}`));
 if(linked!==root&&!linked.startsWith(root+path.sep))throw symlinkRefusal(relative);
}
function interpretChildError(error,dirfd,name,relative){
 if(error.code==='ENOENT')return deletedFile(relative);
 if(error.code==='ELOOP'||error.code==='ENOTDIR'||error.code==='EEXIST'){
  try{if(fs.lstatSync(procPath(dirfd,name)).isSymbolicLink())return symlinkRefusal(relative);}
  catch(statError){if(statError.code==='ENOENT')return deletedFile(relative);throw statError;}
  if(error.code==='ELOOP')return symlinkRefusal(relative);
 }
 return error;
}
function openDirectoryExact(directory){
 assertDevelopmentSnapshotPlatform();
 let fd;
 try{fd=fs.openSync(directory,directoryFlags());}
 catch(error){
  if(error.code==='ELOOP'||error.code==='ENOTDIR')throw Error('Source root is not a directory');
  throw error;
 }
 try{
  const linked=path.resolve(fs.readlinkSync(`/proc/self/fd/${fd}`));
  if(linked!==directory||!fs.fstatSync(fd).isDirectory())throw Error('Source root changed before it was opened');
  return fd;
 }catch(error){fs.closeSync(fd);throw error;}
}
function createWalker(rootFd,rootPath){
 const directories=new Map([['',rootFd]]);const owned=[];
 function close(){for(const fd of owned)fs.closeSync(fd);}
 function directoryFd(parts,relative){
  let key='';let dirfd=rootFd;
  for(const name of parts){
   key=key?`${key}/${name}`:name;
   if(directories.has(key)){dirfd=directories.get(key);continue;}
   let next;
   try{next=fs.openSync(procPath(dirfd,name),directoryFlags());}
   catch(error){throw interpretChildError(error,dirfd,name,relative);}
   try{
    assertContained(next,rootPath,relative);
    if(!fs.fstatSync(next).isDirectory())throw symlinkRefusal(relative);
   }catch(error){fs.closeSync(next);throw error;}
   directories.set(key,next);owned.push(next);dirfd=next;
  }
  return dirfd;
 }
 function openFile(relative){
  rejectUnsafe(relative);
  const parts=relative.split('/');const name=parts.pop();
  const dirfd=directoryFd(parts,relative);
  let fd;
  try{fd=fs.openSync(procPath(dirfd,name),fileFlags());}
  catch(error){throw interpretChildError(error,dirfd,name,relative);}
  try{assertContained(fd,rootPath,relative);return fd;}
  catch(error){fs.closeSync(fd);throw error;}
 }
 return {openFile,close};
}
function writeTree(destination,files,manifestBytes){
 const destFd=openDirectoryExact(destination);const owned=[];const directories=new Map([['',destFd]]);
 try{
  for(const file of files){
   rejectUnsafe(file.path);
   const parts=file.path.split('/');const name=parts.pop();
   let key='';let dirfd=destFd;
   for(const part of parts){
    key=key?`${key}/${part}`:part;
    if(!directories.has(key)){
     try{fs.mkdirSync(procPath(dirfd,part));}
     catch(error){if(error.code!=='EEXIST')throw error;}
     let child;
     try{child=fs.openSync(procPath(dirfd,part),directoryFlags());}
     catch(error){throw interpretChildError(error,dirfd,part,file.path);}
     try{
      assertContained(child,destination,file.path);
      if(!fs.fstatSync(child).isDirectory())throw symlinkRefusal(file.path);
     }catch(error){fs.closeSync(child);throw error;}
     directories.set(key,child);owned.push(child);
    }
    dirfd=directories.get(key);
   }
   const out=fs.openSync(procPath(dirfd,name),fs.constants.O_WRONLY|fs.constants.O_CREAT|fs.constants.O_EXCL|fs.constants.O_NOFOLLOW);
   try{assertContained(out,destination,file.path);fs.writeFileSync(out,file.bytes);}
   finally{fs.closeSync(out);}
  }
  const manifestFd=fs.openSync(procPath(destFd,'development-source-manifest.json'),fs.constants.O_WRONLY|fs.constants.O_CREAT|fs.constants.O_EXCL|fs.constants.O_NOFOLLOW);
  try{
   const linked=path.resolve(fs.readlinkSync(`/proc/self/fd/${manifestFd}`));
   if(linked!==path.join(destination,'development-source-manifest.json'))throw Error('Snapshot manifest escaped the destination');
   fs.writeFileSync(manifestFd,manifestBytes);
  }finally{fs.closeSync(manifestFd);}
 }finally{for(const fd of owned)fs.closeSync(fd);fs.closeSync(destFd);}
}
function directoryIdentity(resolved){
 const stat=fs.lstatSync(resolved);
 if(stat.isSymbolicLink()||!stat.isDirectory())throw Error('Development snapshot failed and left an unusable destination');
 return {dev:stat.dev,ino:stat.ino};
}
function removeExportIfOwned(resolved,identity){
 let stat;
 try{stat=fs.lstatSync(resolved);}catch(error){if(error.code==='ENOENT')return;throw error;}
 if(stat.isSymbolicLink()||!stat.isDirectory()||stat.dev!==identity.dev||stat.ino!==identity.ino)throw Error('Development snapshot failed and left an unusable destination');
 fs.rmSync(resolved,{recursive:true,force:true});
 let remains=true;
 try{fs.lstatSync(resolved);}catch(error){if(error.code==='ENOENT')remains=false;else throw error;}
 if(remains)throw Error('Development snapshot failed and left an unusable destination');
}
export function planDevelopmentSnapshot(sourceArg){
 assertDevelopmentSnapshotPlatform();
 const source=fs.realpathSync(sourceArg);
 const top=fs.realpathSync(execFileSync('git',['-C',source,'rev-parse','--show-toplevel'],{encoding:'utf8'}).trim());if(top!==source)throw Error('Expected repository root');
 const rootFd=openDirectoryExact(source);const walker=createWalker(rootFd,source);
 try{
  const inventory=execFileSync('git',['-C',source,'ls-files','--cached','--others','--exclude-standard','-z'],{maxBuffer:32*1024*1024}).toString('utf8').split('\0').filter(Boolean);
  const files=[];const excluded=[];const casePaths=new Set();
  for(const relative of [...new Set(inventory)].sort()){
   let descriptor;
   try{descriptor=walker.openFile(relative);}
   catch(error){if(error.code==='ENOENT'){excluded.push({path:relative,reason:'deleted_working_file'});continue;}throw error;}
   try{
    const classification=classifyPath(relative);
    if(!['text','public_asset'].includes(classification)){excluded.push({path:relative,reason:classification});continue;}
    if(casePaths.has(relative.toLowerCase()))throw Error('Case-colliding source paths');casePaths.add(relative.toLowerCase());
    const stat=fs.fstatSync(descriptor);
    if(!stat.isFile()||stat.size>20*1024*1024)throw Error(`Nonregular/oversized source refused: ${relative}`);
    const bytes=fs.readFileSync(descriptor);if(classification==='text')validateText(bytes,relative);else validateAsset(bytes,relative);
    files.push({path:relative,sha256:createHash('sha256').update(bytes).digest('hex'),size:bytes.length,bytes});
   }finally{fs.closeSync(descriptor);}
  }
  for(const required of ['package.json','package-lock.json','run-tests.mjs','AGENTS.md','SOUL.md','tsconfig.json'])if(!files.some(f=>f.path===required))throw Error(`Required development file missing: ${required}`);
  if(!files.some(f=>f.path.startsWith('src/')&&f.path.endsWith('.test.mjs')))throw Error('Development tests missing');
  return {source,files,excluded};
 }finally{walker.close();fs.closeSync(rootFd);}
}
export function exportDevelopmentSnapshot(sourceArg,destinationArg){
 assertDevelopmentSnapshotPlatform();
 const plan=planDevelopmentSnapshot(sourceArg);const destination=path.resolve(destinationArg);
 let existing=false;
 try{fs.lstatSync(destination);existing=true;}catch(error){if(error.code!=='ENOENT')throw error;}
 if(existing)throw Error('Destination already exists');
 const parent=fs.realpathSync(path.dirname(destination));const resolved=path.join(parent,path.basename(destination));
 if(resolved===plan.source||resolved.startsWith(plan.source+path.sep))throw Error('Destination must be outside source');
 // Inputs are validated before any output. A later error removes only the directory this call created.
 fs.mkdirSync(resolved);
 const identity=directoryIdentity(resolved);
 try{
  const manifest={version:1,purpose:'development-source',gitMetadataIncluded:false,dependenciesIncluded:false,files:plan.files.map(({bytes,...entry})=>entry),excluded:plan.excluded};
  writeTree(resolved,plan.files,JSON.stringify(manifest,null,2)+'\n');
  return {files:manifest.files.length,excluded:manifest.excluded.length};
 }catch(error){
  removeExportIfOwned(resolved,identity);
  throw error;
 }
}
if(process.argv[1]&&import.meta.url===pathToFileURL(path.resolve(process.argv[1])).href){
 const [source,destination]=process.argv.slice(2);if(!source||!destination)throw Error('Expected repository root and new development snapshot directory');
 console.log(JSON.stringify(exportDevelopmentSnapshot(source,destination)));
}
