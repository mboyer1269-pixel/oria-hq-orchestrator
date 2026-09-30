import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';import os from 'node:os';import path from 'node:path';import {execFileSync} from 'node:child_process';
import {classifyPath,validateEnvTemplate,planDevelopmentSnapshot,exportDevelopmentSnapshot} from './development-snapshot.mjs';
function fixture(){const parent=fs.mkdtempSync(path.join(os.tmpdir(),'hq-dev-snapshot-'));const source=path.join(parent,'repo');fs.mkdirSync(source);execFileSync('git',['init','--quiet',source]);
 const write=(rel,text)=>{const file=path.join(source,rel);fs.mkdirSync(path.dirname(file),{recursive:true});fs.writeFileSync(file,text);};
 for(const file of ['package.json','package-lock.json','tsconfig.json'])write(file,'{}');for(const file of ['AGENTS.md','SOUL.md','run-tests.mjs'])write(file,'// fixture\n');write('src/example.test.mjs','// test\n');write('.gitignore','.env.local\nnode_modules/\n.next/\n');
 execFileSync('git',['-C',source,'add','.']);return {parent,source,write,clean:()=>fs.rmSync(parent,{recursive:true,force:true})};}
test('tracked and new source preserved with test infrastructure; ignored/runtime absent',()=>{const f=fixture();try{
 f.write('src/new.ts','export const value=1;');f.write('docs/guide.md','# Guide');f.write('scripts/audit/check.mjs','// check');f.write('.github/workflows/ci.yml','name: test');f.write('db/schema.sql','select 1;');f.write('.env.example','API_KEY=\nORIA_ENABLE_TEST=0\n');
 for(const file of ['.env.local','node_modules/private.js','.next/cache.json','memory/runtime.md','db/documents.json','src/secrets/key.pem'])f.write(file,'PRIVATE');
 const out=path.join(f.parent,'export');const result=exportDevelopmentSnapshot(f.source,out);assert.ok(result.files>6);
 for(const file of ['AGENTS.md','SOUL.md','run-tests.mjs','src/new.ts','scripts/audit/check.mjs','.github/workflows/ci.yml','.env.example'])assert.equal(fs.readFileSync(path.join(out,file),'utf8'),fs.readFileSync(path.join(f.source,file),'utf8'));
 for(const file of ['.git','.env.local','node_modules','.next','memory','db/documents.json','src/secrets'])assert.equal(fs.existsSync(path.join(out,file)),false);
 const manifest=JSON.parse(fs.readFileSync(path.join(out,'development-source-manifest.json'),'utf8'));assert.ok(manifest.files.find(x=>x.path==='src/new.ts').sha256);assert.equal(manifest.dependenciesIncluded,false);
 }finally{f.clean();}});
test('invalid template and hardcoded credential-like payload abort before destination created',()=>{const f=fixture();try{f.write('.env.example','API_KEY=nonempty\n');const out=path.join(f.parent,'export');assert.throws(()=>exportDevelopmentSnapshot(f.source,out),/template/);assert.equal(fs.existsSync(out),false);fs.unlinkSync(path.join(f.source,'.env.example'));f.write('src/private.ts','const value="'+'sk-proj-'+'a'.repeat(40)+'";');assert.throws(()=>planDevelopmentSnapshot(f.source),/Credential-like/);}finally{f.clean();}});
test('binary masquerading as source, directory symlink and file symlink refused before destination creation',()=>{const f=fixture();try{f.write('src/binary.ts',Buffer.from([0,255,0]));assert.throws(()=>planDevelopmentSnapshot(f.source),/Non-text|Binary/);fs.unlinkSync(path.join(f.source,'src/binary.ts'));const outside=path.join(f.parent,'outside');fs.mkdirSync(outside);fs.writeFileSync(path.join(outside,'unsafe.ts'),'secret');fs.symlinkSync(outside,path.join(f.source,'src/linked'),'junction');assert.throws(()=>planDevelopmentSnapshot(f.source),/Symlink/);const outDir=path.join(f.parent,'export-dir-symlink');assert.throws(()=>exportDevelopmentSnapshot(f.source,outDir),/Symlink/);assert.equal(fs.existsSync(outDir),false);fs.unlinkSync(path.join(f.source,'src/linked'));fs.symlinkSync(path.join(outside,'unsafe.ts'),path.join(f.source,'src/linked.ts'));assert.throws(()=>planDevelopmentSnapshot(f.source),/Symlink/);const outFile=path.join(f.parent,'export-file-symlink');assert.throws(()=>exportDevelopmentSnapshot(f.source,outFile),/Symlink/);assert.equal(fs.existsSync(outFile),false);}finally{f.clean();}});
test('path and destination boundaries, template flags default off only',()=>{for(const p of ['../escape','src/../escape','C:/private','src\\private','/root'])assert.throws(()=>classifyPath(p));assert.equal(classifyPath('src/.env.production'),'private_or_runtime');assert.equal(classifyPath('src/token.json'),'private_or_runtime');assert.throws(()=>validateEnvTemplate('ORIA_ENABLE_TEST=1'));const f=fixture();try{assert.throws(()=>exportDevelopmentSnapshot(f.source,path.join(f.source,'export')),/outside/);assert.throws(()=>exportDevelopmentSnapshot(f.source,f.source),/exists/);}finally{f.clean();}});

test('npmrc permits only engine strict with harmless comments, refuses auth and registry before copy',()=>{const f=fixture();try{
 f.write('.npmrc','# Require supported Node\n; Development setting\nengine-strict=true\n');const valid=planDevelopmentSnapshot(f.source);assert.ok(valid.files.some(file=>file.path==='.npmrc'));
 for(const text of ['engine-strict=true\n//registry.example/:_authToken=synthetic\n','engine-strict=true\nregistry=https://registry.example\n','engine-strict=false\n','engine-strict=true\n# _authToken=synthetic\n']){
  f.write('.npmrc',text);const out=path.join(f.parent,'export');assert.throws(()=>exportDevelopmentSnapshot(f.source,out),/npm configuration/);assert.equal(fs.existsSync(out),false);
 }
 }finally{f.clean();}});

function outsideSentinel(parent){
 const file=path.join(parent,'outside-sentinel.txt');
 fs.writeFileSync(file,'OUTSIDE-SENTINEL\n');
 return file;
}
test('parent directory swapped after it is opened cannot redirect the read',()=>{const f=fixture();const realLstat=fs.lstatSync;const realOpen=fs.openSync;try{
 f.write('src/nested/payload.ts','INSIDE\n');
 const outside=path.join(f.parent,'outside');fs.mkdirSync(path.join(outside,'nested'),{recursive:true});fs.writeFileSync(path.join(outside,'nested/payload.ts'),'OUTSIDE-SENTINEL\n');
 const sentinel=outsideSentinel(f.parent);const nested=path.join(f.source,'src','nested');const kept=path.join(f.parent,'nested-real');
 let swapped=false;
 const swap=()=>{if(swapped)return;swapped=true;fs.lstatSync=realLstat;fs.openSync=realOpen;fs.renameSync(nested,kept);fs.symlinkSync(path.join(outside,'nested'),nested);};
 let directoryChecks=0;
 fs.lstatSync=function(target,options){const stat=realLstat.call(fs,target,options);if(target===nested&&stat.isDirectory()){directoryChecks+=1;if(directoryChecks===2)swap();}return stat;};
 fs.openSync=function(target,flags,mode){const fd=realOpen.call(fs,target,flags,mode);if(typeof target==='string'&&target.startsWith('/proc/self/fd/')&&target.endsWith('/nested'))swap();return fd;};
 const out=path.join(f.parent,'export');
 let exported=null;let refused=false;
 try{exportDevelopmentSnapshot(f.source,out);exported=fs.readFileSync(path.join(out,'src/nested/payload.ts'),'utf8');}
 catch(error){refused=true;assert.match(error.message,/Symlink/);assert.equal(fs.existsSync(out),false);}
 assert.equal(swapped,true);
 assert.equal(fs.lstatSync(nested).isSymbolicLink(),true);
 assert.equal(fs.readFileSync(path.join(outside,'nested/payload.ts'),'utf8'),'OUTSIDE-SENTINEL\n');
 assert.equal(fs.readFileSync(sentinel,'utf8'),'OUTSIDE-SENTINEL\n');
 assert.equal(fs.readFileSync(path.join(kept,'payload.ts'),'utf8'),'INSIDE\n');
 if(!refused){
  assert.equal(exported,'INSIDE\n');
  assert.equal(fs.readFileSync(path.join(out,'development-source-manifest.json'),'utf8').includes('OUTSIDE-SENTINEL'),false);
 }
}finally{fs.lstatSync=realLstat;fs.openSync=realOpen;f.clean();}});

test('directory entry replaced by a symlink before lookup is refused',()=>{const f=fixture();const realOpen=fs.openSync;try{
 f.write('src/nested/payload.ts','INSIDE\n');
 const outside=path.join(f.parent,'outside');fs.mkdirSync(path.join(outside,'nested'),{recursive:true});fs.writeFileSync(path.join(outside,'nested/payload.ts'),'OUTSIDE-SENTINEL\n');
 const nested=path.join(f.source,'src','nested');const kept=path.join(f.parent,'nested-real');
 let swapped=false;
 fs.openSync=function(target,flags,mode){
  const fd=realOpen.call(fs,target,flags,mode);
  if(!swapped&&typeof target==='string'&&target.startsWith('/proc/self/fd/')&&target.endsWith('/src')&&(flags&fs.constants.O_DIRECTORY)){
   swapped=true;fs.openSync=realOpen;fs.renameSync(nested,kept);fs.symlinkSync(path.join(outside,'nested'),nested);
  }
  return fd;
 };
 const out=path.join(f.parent,'export');
 assert.throws(()=>exportDevelopmentSnapshot(f.source,out),/Symlink/);
 assert.equal(swapped,true);
 assert.equal(fs.lstatSync(nested).isSymbolicLink(),true);
 assert.equal(fs.existsSync(out),false);
 assert.equal(fs.readFileSync(path.join(outside,'nested/payload.ts'),'utf8'),'OUTSIDE-SENTINEL\n');
 assert.equal(fs.readFileSync(path.join(kept,'payload.ts'),'utf8'),'INSIDE\n');
}finally{fs.openSync=realOpen;f.clean();}});

test('file replaced by a symlink after its parent directory is opened is refused',()=>{const f=fixture();const realOpen=fs.openSync;try{
 const outside=path.join(f.parent,'outside-file.ts');fs.writeFileSync(outside,'OUTSIDE-SENTINEL\n');
 const target=path.join(f.source,'src/example.test.mjs');const kept=path.join(f.parent,'example-real.mjs');
 let swapped=false;
 fs.openSync=function(file,flags,mode){
  const fd=realOpen.call(fs,file,flags,mode);
  if(!swapped&&typeof file==='string'&&file.startsWith('/proc/self/fd/')&&file.endsWith('/src')&&(flags&fs.constants.O_DIRECTORY)){
   swapped=true;fs.openSync=realOpen;fs.renameSync(target,kept);fs.symlinkSync(outside,target);
  }
  return fd;
 };
 const out=path.join(f.parent,'export');
 assert.throws(()=>exportDevelopmentSnapshot(f.source,out),/Symlink/);
 assert.equal(swapped,true);
 assert.equal(fs.lstatSync(target).isSymbolicLink(),true);
 assert.equal(fs.existsSync(out),false);
 assert.equal(fs.readFileSync(outside,'utf8'),'OUTSIDE-SENTINEL\n');
 assert.equal(fs.readFileSync(kept,'utf8'),'// test\n');
}finally{fs.openSync=realOpen;f.clean();}});

test('deleted tracked file is excluded and a copy failure leaves no destination',()=>{const f=fixture();const realMkdir=fs.mkdirSync;const realRm=fs.rmSync;try{
 f.write('src/gone.ts','temporary\n');execFileSync('git',['-C',f.source,'add','src/gone.ts']);fs.unlinkSync(path.join(f.source,'src/gone.ts'));
 const sentinel=outsideSentinel(f.parent);
 const plan=planDevelopmentSnapshot(f.source);
 assert.equal(plan.excluded.some(item=>item.path==='src/gone.ts'&&item.reason==='deleted_working_file'),true);
 assert.equal(plan.files.some(item=>item.path==='src/gone.ts'),false);
 const out=path.join(f.parent,'export');const result=exportDevelopmentSnapshot(f.source,out);
 assert.equal(fs.existsSync(path.join(out,'src/gone.ts')),false);
 assert.equal(fs.readFileSync(path.join(out,'src/example.test.mjs'),'utf8'),'// test\n');
 assert.equal(result.files,plan.files.length);
 assert.equal(fs.readFileSync(sentinel,'utf8'),'OUTSIDE-SENTINEL\n');
 fs.rmSync(out,{recursive:true,force:true});
 let created=false;
 fs.mkdirSync=function(target,options){if(created)throw Error('injected copy failure');const made=realMkdir.call(fs,target,options);if(target===out)created=true;return made;};
 assert.throws(()=>exportDevelopmentSnapshot(f.source,out),/injected copy failure/);
 assert.equal(fs.existsSync(out),false);
 assert.equal(fs.readFileSync(path.join(f.source,'package.json'),'utf8'),'{}');
 created=false;
 fs.rmSync=()=>{};
 assert.throws(()=>exportDevelopmentSnapshot(f.source,out),/unusable/);
 assert.equal(fs.existsSync(path.join(out,'development-source-manifest.json')),false);
 assert.equal(fs.lstatSync(out).isDirectory(),true);
}finally{fs.mkdirSync=realMkdir;fs.rmSync=realRm;f.clean();}});
