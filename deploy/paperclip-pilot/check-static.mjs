// Local authored checks only: reads JSON/text, never imports or executes Paperclip.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
const read = name => JSON.parse(readFileSync(new URL(name, import.meta.url), 'utf8'));
const compose = read('compose.json');
const config = read('paperclip.config.json');
const source = read('source-review.json');
assert.equal(compose.name, 'oria-paperclip-pilot');
assert.deepEqual(Object.keys(compose.services).sort(), ['db', 'paperclip']);
assert.equal(compose.networks['pilot-internal'].internal, true);
assert.equal(compose.services.paperclip.ports, undefined);
assert.equal(compose.services.db.ports, undefined);
for (const service of Object.values(compose.services)) {
  assert.ok(['node', 'postgres'].includes(service.user));
  assert.equal(service.read_only, true);
  assert.deepEqual(service.cap_drop, ['ALL']);
  assert.deepEqual(service.security_opt, ['no-new-privileges:true']);
  assert.ok(service.mem_limit && service.cpus && service.pids_limit);
  assert.equal(service.privileged, undefined);
  assert.equal(service.build, undefined);
  assert.equal(service.network_mode, undefined);
  assert.deepEqual(service.networks, ['pilot-internal']);
  for (const mount of service.volumes) assert.match(mount, /^pilot-(?:postgres|paperclip):\//);
}
assert.equal(config.server.deploymentMode, 'authenticated');
assert.equal(config.auth.disableSignUp, true);
assert.equal(config.telemetry.enabled, false);
assert.equal(compose.services.paperclip.environment.BETTER_AUTH_TRUSTED_ORIGINS, 'http://localhost:3310');
assert.equal(compose.services.paperclip.environment.HEARTBEAT_SCHEDULER_ENABLED, 'false');
assert.match(source.commit, /^[a-f0-9]{40}$/);
assert.match(source.observedOfficialImage, /^ghcr\.io\/paperclipai\/paperclip@sha256:[a-f0-9]{64}$/);
assert.equal(compose.services.paperclip.image, source.observedOfficialImage);
assert.equal(compose.services.db.image, source.postgresImage);
assert.match(source.postgresImage, /^postgres@sha256:[a-f0-9]{64}$/);
assert.equal(source.attestationVerified, true);
assert.ok(!JSON.stringify(compose).includes('docker.sock'));
console.log('PASS: static isolation and source-pin structure; no runtime, image, schema or auth-bootstrap validation implied.');
console.log(`Review gates: attestation=${source.attestationVerified}, postgresPinned=${!!source.postgresImage}, deploymentApproved=${source.deploymentApproved}`);
