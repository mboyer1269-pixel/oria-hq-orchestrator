import fs from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';

const [sourceArg, destinationArg] = process.argv.slice(2);
if (!sourceArg || !destinationArg) throw new Error('Expected source repository and new snapshot directory');
const source = fs.realpathSync(sourceArg);
const destination = path.resolve(destinationArg);
if (fs.existsSync(destination)) throw new Error('Snapshot destination already exists');
const files = ['Dockerfile', '.dockerignore', 'package.json', 'package-lock.json',
  'next.config.ts', 'next-env.d.ts', 'tsconfig.json', 'postcss.config.mjs', 'eslint.config.mjs',
  'scripts/check-docker-public-env.mjs'];
function walk(relative) {
  for (const entry of fs.readdirSync(path.join(source, relative), { withFileTypes: true })) {
    const child = `${relative}/${entry.name}`;
    if (entry.isSymbolicLink()) throw new Error(`Symlink refused: ${child}`);
    if (entry.name.startsWith('.') || /\.(pem|key|p12|pfx|sqlite|db)$/i.test(entry.name)) throw new Error(`Private/runtime asset refused: ${child}`);
    if (entry.isDirectory()) walk(child);
    else if (entry.isFile()) files.push(child);
    else throw new Error(`Non-regular asset refused: ${child}`);
  }
}
for (const directory of ['src', 'public', 'config']) walk(directory);
const manifest = [];
for (const relative of files.sort()) {
  const origin = path.join(source, relative);
  if (!fs.lstatSync(origin).isFile()) throw new Error(`Expected regular file: ${relative}`);
  const bytes = fs.readFileSync(origin);
  const target = path.join(destination, relative);
  fs.mkdirSync(path.dirname(target), { recursive: true });
  fs.writeFileSync(target, bytes);
  manifest.push({ path: relative, sha256: createHash('sha256').update(bytes).digest('hex') });
}
fs.writeFileSync(path.join(destination, 'source-manifest.json'), JSON.stringify(manifest, null, 2) + '\n');
console.log(JSON.stringify({ files: manifest.length, envFilesIncluded: false, sourceRoots: ['src', 'public', 'config'] }));
