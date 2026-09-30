import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const read = path => readFileSync(new URL(path, import.meta.url), 'utf8');
const compose = JSON.parse(read('./compose.json'));
const pilot = JSON.parse(read('../../paperclip-pilot/compose.json'));
const dockerfile = read('./Dockerfile');
assert.equal(dockerfile.split('\n')[0], `FROM ${pilot.services.paperclip.image}`);
assert.match(dockerfile, /USER node\nENTRYPOINT/);
assert.match(dockerfile, /CMD \[\]/);
const allVolumes = new Set();
for (const provider of ['gemini', 'cursor']) {
  const service = compose.services[`${provider}-runner`];
  assert.equal(service.user, '1000:1000');
  assert.equal(service.read_only, true);
  assert.deepEqual(service.cap_drop, ['ALL']);
  assert.deepEqual(service.security_opt, ['no-new-privileges:true']);
  for (const forbidden of ['ports', 'privileged', 'network_mode', 'pid', 'env_file', 'devices', 'cap_add']) {
    assert.equal(service[forbidden], undefined, forbidden);
  }
  assert.deepEqual(Object.keys(service.environment).sort(), ['HOME', 'NODE_OPTIONS']);
  assert.ok(service.cpus && service.mem_limit && service.pids_limit);
  assert.equal(service.mem_limit, service.memswap_limit);
  assert.deepEqual(service.networks, [`${provider}-control`, `${provider}-egress`]);
  assert.equal(compose.networks[`${provider}-control`].internal, true);
  assert.equal(compose.volumes[`${provider}-home`].external, true);
  for (const [suffix, target] of [['home', '/paperclip'], ['workspace', '/workspace'], ['hostkeys', '/var/lib/oria-ssh']]) {
    assert.ok(service.volumes.includes(`${provider}-${suffix}:${target}`));
    const name = compose.volumes[`${provider}-${suffix}`].name;
    assert.ok(!allVolumes.has(name), 'No shared provider volumes');
    allVolumes.add(name);
  }
  assert.ok(!JSON.stringify(service.volumes).includes('docker.sock'));
  assert.equal(service.configs[0].source, `${provider}-authorized-keys`);
  assert.equal(service.configs[0].mode, 0o444);
}
const cursor = compose.services['cursor-runner'].volumes.find(v => typeof v === 'object');
assert.equal(cursor.target, '/opt/cursor');
assert.equal(cursor.read_only, true);
assert.equal(cursor.bind.create_host_path, false);
const ssh = read('./sshd_config');
for (const line of ['Port 2222', 'UsePAM no', 'PermitRootLogin no', 'PasswordAuthentication no', 'AuthenticationMethods publickey', 'AllowUsers node', 'StrictModes yes', 'AllowTcpForwarding no', 'AllowAgentForwarding no', 'PermitUserRC no', 'PermitTTY no']) {
  assert.ok(ssh.split('\n').includes(line), line);
}
assert.ok(!read('./entrypoint.sh').includes('\r'), 'Shell script must use LF');
const overlay = JSON.parse(read('./paperclip.networks.json'));
assert.deepEqual(Object.keys(overlay.services), ['paperclip']);
assert.deepEqual(overlay.services.paperclip.networks, ['pilot-internal', 'gemini-control', 'cursor-control']);
console.log('Runner static isolation checks passed; runtime evidence is recorded separately in README and validation reports.');
