import fs from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';
const [sourceArg, targetArg] = process.argv.slice(2);
if (!sourceArg || !targetArg) throw new Error('Usage: node snapshot.mjs SOURCE_ROOT NEW_SNAPSHOT_DIRECTORY');
const source = fs.realpathSync(sourceArg);
const target = path.resolve(targetArg);
if (fs.existsSync(target)) throw new Error('Snapshot target must not already exist');
const files = ['package.json', 'package-lock.json',
  'fixtures/mcp-tools-list.expected.json', 'fixtures/mcp-resources-list.expected.json'];
function walk(dir) {
  for (const item of fs.readdirSync(path.join(source, dir), { withFileTypes: true })) {
    if (item.isSymbolicLink()) throw new Error('Symlinks forbidden in source snapshot');
    const relative = `${dir}/${item.name}`;
    if (item.isDirectory()) walk(relative);
    else if (item.isFile() && /\.(ts|js|json)$/.test(item.name)) files.push(relative);
    else throw new Error(`Unexpected source asset: ${relative}`);
  }
}
walk('src');
const manifest = [];
for (const relative of files.sort()) {
  if (!fs.lstatSync(path.join(source, relative)).isFile()) throw new Error(`Expected regular source file: ${relative}`);
  const bytes = fs.readFileSync(path.join(source, relative));
  const dest = path.join(target, relative);
  fs.mkdirSync(path.dirname(dest), { recursive: true });
  fs.writeFileSync(dest, bytes);
  manifest.push({ path: relative, sha256: createHash('sha256').update(bytes).digest('hex') });
}
fs.writeFileSync(path.join(target, 'source-manifest.json'), JSON.stringify(manifest, null, 2) + '\n');
console.log(`Source-only snapshot created: ${manifest.length} files. Review manifest before build.`);
