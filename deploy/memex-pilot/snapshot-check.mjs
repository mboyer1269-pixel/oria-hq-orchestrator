// Packaging regression: load capability catalogs from the generated snapshot.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { execFileSync } from 'node:child_process';
const source = process.argv[2];
if (!source) throw new Error('Usage: node --experimental-strip-types snapshot-check.mjs SOURCE_ROOT');
const temporary = fs.mkdtempSync(path.join(os.tmpdir(), 'memex-package-check-'));
try {
  const snapshot = path.join(temporary, 'snapshot');
  execFileSync(process.execPath, [fileURLToPath(new URL('./snapshot.mjs', import.meta.url)), source, snapshot]);
  const manifest = JSON.parse(fs.readFileSync(path.join(snapshot, 'source-manifest.json'), 'utf8'));
  const fixtures = manifest.filter(row => row.path.startsWith('fixtures/')).map(row => row.path).sort();
  assert.deepEqual(fixtures, ['fixtures/mcp-resources-list.expected.json', 'fixtures/mcp-tools-list.expected.json']);
  assert.ok(manifest.every(row => row.path.startsWith('src/') || fixtures.includes(row.path) || ['package.json', 'package-lock.json'].includes(row.path)));
  const capabilities = await import(pathToFileURL(path.join(snapshot, 'src/mcp/capabilities.ts')).href);
  assert.ok(capabilities.getAuthorizedTools('remote').length > 0);
  assert.ok(Array.isArray(capabilities.getAuthorizedResources()));
  console.log('Generated snapshot loads both MCP catalogs; no runtime-data paths included.');
} finally {
  fs.rmSync(temporary, { recursive: true, force: true });
}
