import test from 'node:test';
import assert from 'node:assert/strict';
import http from 'node:http';
import https from 'node:https';
import { execFileSync } from 'node:child_process';
import { mkdtempSync, readFileSync, rmSync, existsSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { once } from 'node:events';
import { createHandler } from './proxy.mjs';

const authorization = `Bearer amh1.synthetic.${'A'.repeat(43)}`;
const headers = { authorization, 'content-type': 'application/json' };
const operatorHeaders = { authorization: `Bearer opr1.${'B'.repeat(43)}`, 'content-type': 'application/json' };
async function fixture(t, upstreamHandler, deadlineMs = 1000) {
  const upstream = http.createServer(upstreamHandler);
  upstream.listen(0, '127.0.0.1'); await once(upstream, 'listening');
  const captured = [];
  const proxy = http.createServer(createHandler({ deadlineMs, request(options, callback) {
    captured.push(options);
    return http.request({ ...options, hostname: '127.0.0.1', port: upstream.address().port }, callback);
  } }));
  proxy.listen(0, '127.0.0.1'); await once(proxy, 'listening');
  t.after(() => { proxy.closeAllConnections(); upstream.closeAllConnections(); proxy.close(); upstream.close(); });
  return { captured, url: `http://127.0.0.1:${proxy.address().port}` };
}
test('fixed upstream and minimal headers; no cookies or upstream metadata forwarded', async t => {
  const f = await fixture(t, (req, res) => { req.resume(); res.writeHead(200, { 'content-type': 'application/json', 'set-cookie': 'private=x' }); res.end('{"ok":true}'); });
  const response = await fetch(`${f.url}/mcp`, { method: 'POST', headers: { ...headers, cookie: 'secret', 'x-forwarded-host': 'attacker' }, body: '{}' });
  assert.equal(response.status, 200); assert.deepEqual(await response.json(), { ok: true });
  assert.equal(response.headers.get('set-cookie'), null);
  assert.equal(f.captured[0].hostname, 'memex'); assert.equal(f.captured[0].port, 3000); assert.equal(f.captured[0].path, '/mcp');
  assert.deepEqual(Object.keys(f.captured[0].headers).sort(), ['accept', 'authorization', 'content-length', 'content-type']);
});
test('route, credential, content type and input size fail before upstream', async t => {
  const f = await fixture(t, () => assert.fail('unexpected upstream'));
  for (const [route, options, status] of [
    ['/mcp?x=1', { method: 'POST', headers, body: '{}' }, 404],
    ['/mcp', {}, 404],
    ['/mcp', { method: 'POST', body: '{}' }, 401],
    ['/mcp', { method: 'POST', headers: { authorization }, body: '{}' }, 415],
    ['/mcp', { method: 'POST', headers, body: 'x'.repeat(1024 * 1024 + 1) }, 413],
  ]) { const r = await fetch(f.url + route, options); assert.equal(r.status, status); await r.text(); }
  assert.equal(f.captured.length, 0);
});

test('operator routes are exact and credential families cannot cross channels', async t => {
  const f = await fixture(t, () => assert.fail('unexpected upstream'));
  for (const [route, authHeaders, status] of [
    ['/operator/review/snapshot', headers, 401],
    ['/operator/review/decision', headers, 401],
    ['/mcp', operatorHeaders, 401],
    ['/operator/review/publish', operatorHeaders, 404],
    ['/operator/review/snapshot?namespace=x', operatorHeaders, 404],
    ['/operator/review/decision/', operatorHeaders, 404],
  ]) {
    const response = await fetch(f.url + route, { method: 'POST', headers: authHeaders, body: '{}' });
    assert.equal(response.status, status); await response.text();
  }
  assert.equal(f.captured.length, 0);
});

test('operator preserves bounded contract errors and never follows redirects', async t => {
  for (const status of [200, 400, 401, 404, 409, 413, 503, 302, 500]) {
    const f = await fixture(t, (req, res) => {
      req.resume(); res.writeHead(status, { 'content-type': 'application/json', 'set-cookie': 'private=x', location: 'https://attacker.invalid/' });
      res.end(JSON.stringify({ error: 'contract_error' }));
    });
    for (const route of ['/operator/review/snapshot', '/operator/review/decision']) {
      const response = await fetch(f.url + route, { method: 'POST', headers: operatorHeaders, body: '{}' });
      assert.equal(response.status, [302, 500].includes(status) ? 502 : status);
      assert.equal(response.headers.get('location'), null); assert.equal(response.headers.get('set-cookie'), null);
      await response.json();
      assert.equal(f.captured.at(-1).hostname, 'memex');
      assert.equal(f.captured.at(-1).path, route);
    }
    assert.equal(f.captured.length, 2);
  }
});

test('operator input has a smaller 16KiB budget', async t => {
  const f = await fixture(t, () => assert.fail('unexpected upstream'));
  const response = await fetch(f.url + '/operator/review/decision', {
    method: 'POST', headers: operatorHeaders, body: 'x'.repeat(16 * 1024 + 1),
  });
  assert.equal(response.status, 413); await response.text();
  assert.equal(f.captured.length, 0);
});
test('redirects, oversized and broken responses never pass through', async t => {
  for (const variant of ['redirect', 'oversize', 'broken']) {
    const f = await fixture(t, (req, res) => {
      req.resume();
      if (variant === 'redirect') { res.writeHead(302, { location: 'https://attacker.invalid/' }); return res.end(); }
      res.writeHead(200, { 'content-type': 'application/json' });
      if (variant === 'oversize') return res.end('x'.repeat(1024 * 1024 + 1));
      res.write('{'); res.destroy();
    });
    const r = await fetch(f.url + '/mcp', { method: 'POST', headers, body: '{}' });
    assert.equal(r.status, 502); assert.equal(r.headers.get('location'), null); await r.text();
    assert.equal(f.captured.length, 1);
  }
});
test('deadline releases capacity and concurrency is bounded to eight requests', async t => {
  const f = await fixture(t, req => req.resume(), 300);
  const pending = Array.from({ length: 8 }, () => fetch(f.url + '/mcp', { method: 'POST', headers, body: '{}' }));
  while (f.captured.length < 8) await new Promise(resolve => setTimeout(resolve, 5));
  const excess = await fetch(f.url + '/mcp', { method: 'POST', headers, body: '{}' });
  assert.equal(excess.status, 503); await excess.text();
  const responses = await Promise.all(pending);
  for (const response of responses) { assert.equal(response.status, 504); await response.text(); }
  const next = await fetch(f.url + '/mcp', { method: 'POST', headers, body: '{}' });
  assert.equal(next.status, 504); await next.text();
  assert.equal(f.captured.length, 9);
});

test('client disconnect destroys the in-flight upstream request', async t => {
  let notifyStarted; let notifyClosed;
  const started = new Promise(resolve => { notifyStarted = resolve; });
  const closed = new Promise(resolve => { notifyClosed = resolve; });
  const f = await fixture(t, (req, res) => { req.resume(); res.on('close', notifyClosed); notifyStarted(); });
  const controller = new AbortController();
  const pending = fetch(f.url + '/mcp', { method: 'POST', headers, body: '{}', signal: controller.signal });
  const rejection = assert.rejects(pending, error => error.name === 'AbortError');
  await started; controller.abort(); await rejection;
  await Promise.race([closed, new Promise((_, reject) => { const timer = setTimeout(() => reject(Error('upstream was not cancelled')), 500); timer.unref(); })]);
});

test('real TLS requires trusted certificate and matching hostname', async t => {
  const openssl = process.platform === 'win32' ? 'C:/Program Files/Git/usr/bin/openssl.exe' : 'openssl';
  if (process.platform === 'win32' && !existsSync(openssl)) return t.skip('OpenSSL unavailable: real TLS still requires qualification');
  const directory = mkdtempSync(path.join(tmpdir(), 'oria-memex-tls-test-'));
  const key = path.join(directory, 'test.key'); const cert = path.join(directory, 'test.crt');
  t.after(() => rmSync(directory, { recursive: true, force: true }));
  execFileSync(openssl, ['req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-sha256', '-days', '1', '-keyout', key, '-out', cert,
    '-subj', '/CN=memex-tls', '-addext', 'subjectAltName=DNS:memex-tls'], { stdio: 'ignore' });
  const server = https.createServer({ key: readFileSync(key), cert: readFileSync(cert), minVersion: 'TLSv1.2' }, createHandler());
  server.on('tlsClientError', () => {});
  server.listen(0, '127.0.0.1'); await once(server, 'listening');
  t.after(() => { server.closeAllConnections(); server.close(); });
  const probe = options => new Promise((resolve, reject) => {
    const req = https.request({ host: '127.0.0.1', port: server.address().port, servername: 'memex-tls', path: '/mcp', method: 'POST', agent: false, ...options }, res => {
      res.resume(); res.on('end', () => resolve(res.statusCode));
    }); req.on('error', reject); req.end();
  });
  // TLS succeeds then application rejects absent authorization, proving both layers.
  assert.equal(await probe({ ca: readFileSync(cert) }), 401);
  await assert.rejects(probe({}), error => error.code === 'DEPTH_ZERO_SELF_SIGNED_CERT');
  await assert.rejects(probe({ ca: readFileSync(cert), servername: 'wrong-host' }), error => error.code === 'ERR_TLS_CERT_ALTNAME_INVALID');
});
