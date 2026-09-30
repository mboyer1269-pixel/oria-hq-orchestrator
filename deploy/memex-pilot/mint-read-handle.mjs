// Operator-only: redirect stdout directly to an external protected secret file.
import fs from 'node:fs';
import { mintHandle } from '../src/mcp/handles.ts';
const [subject, namespace, ttlArg = '900'] = process.argv.slice(2);
const ttl = Number(ttlArg);
if (!subject || !namespace || !Number.isInteger(ttl) || ttl < 1 || ttl > 3600) {
  throw new Error('Usage: mint-read-handle.mjs SUBJECT org:PROJECT [TTL_SECONDS <= 3600]');
}
if (process.stdout.isTTY) throw new Error('Redirect handle output to a protected secret file; do not print it to a terminal');
const secret = fs.readFileSync('/run/secrets/handle-signing-key', 'utf8').trim();
process.stdout.write(mintHandle(subject, 'read_only', secret, ttl, new Date(), [namespace]) + '\n');
