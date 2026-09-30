import assert from 'node:assert/strict';
import fs from 'node:fs';
const read = name => fs.readFileSync(new URL(name, import.meta.url), 'utf8');
const c = JSON.parse(read('./antigravity.compose.json'));
const s = c.services['antigravity-runner'];
assert.deepEqual(Object.keys(c.services), ['antigravity-runner']);
assert.equal(s.image, JSON.parse(read('./compose.json')).services['cursor-runner'].image);
assert.equal(s.user, '1000:1000');
assert.equal(s.read_only, true);
assert.deepEqual(s.cap_drop, ['ALL']);
assert.deepEqual(s.security_opt, ['no-new-privileges:true']);
for (const key of ['ports', 'privileged', 'env_file', 'network_mode', 'devices', 'build']) assert.equal(s[key], undefined);
assert.deepEqual(Object.keys(s.environment).sort(), ['HOME', 'NODE_OPTIONS']);
assert.deepEqual(s.networks, ['antigravity-control', 'antigravity-egress']);
assert.equal(c.networks['antigravity-control'].internal, true);
assert.equal(c.volumes['antigravity-home'].external, true);
assert.ok(s.cpus && s.mem_limit && s.pids_limit);
assert.equal(s.volumes.filter(v => typeof v === 'string').length, 3);
for (const mount of s.volumes.filter(v => typeof v === 'object')) {
  assert.equal(mount.read_only, true);
  assert.equal(mount.bind.create_host_path, false);
  assert.ok(!mount.target.includes('docker.sock'));
}
const wrapper = read('./bounded-command.sh');
assert.ok(!wrapper.includes('\r'));
assert.ok(wrapper.includes("trap '' HUP"));
assert.ok(wrapper.includes('--kill-after=5s'));
console.log('Antigravity isolated runner static checks passed; remote execution not tested.');
