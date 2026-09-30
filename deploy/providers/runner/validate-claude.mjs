import assert from 'node:assert/strict';
import fs from 'node:fs';
const read = name => JSON.parse(fs.readFileSync(new URL(name, import.meta.url), 'utf8'));
const c = read('./claude.compose.json');
const s = c.services['claude-runner'];
assert.deepEqual(Object.keys(c.services), ['claude-runner']);
assert.equal(s.image, read('./compose.json').services['cursor-runner'].image);
assert.equal(s.user, '1000:1000');
assert.equal(s.read_only, true);
assert.deepEqual(s.cap_drop, ['ALL']);
assert.deepEqual(s.security_opt, ['no-new-privileges:true']);
for (const key of ['ports', 'privileged', 'env_file', 'network_mode', 'devices', 'build']) assert.equal(s[key], undefined);
assert.deepEqual(Object.keys(s.environment).sort(), ['HOME', 'NODE_OPTIONS']);
assert.deepEqual(s.networks, ['claude-control', 'claude-egress']);
assert.equal(c.networks['claude-control'].internal, true);
assert.ok(s.cpus && s.mem_limit && s.pids_limit);
assert.deepEqual(s.volumes, [
  'claude-home:/paperclip',
  'claude-workspace:/workspace', 'claude-hostkeys:/var/lib/oria-ssh'
]);
assert.deepEqual(c.volumes['claude-home'], {name:'oria-claude-home'});
assert.ok(!JSON.stringify(c).includes('pilot-paperclip'));
assert.ok(!JSON.stringify(c).includes('subpath'));
assert.equal(s.configs[0].source, 'claude-authorized-keys');
console.log('Claude dedicated-home isolation static checks passed; daemon mount/authentication remain untested.');
