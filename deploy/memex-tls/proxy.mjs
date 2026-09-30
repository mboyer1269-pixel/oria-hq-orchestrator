import https from 'node:https';
import http from 'node:http';
import { readFileSync } from 'node:fs';
import { pathToFileURL } from 'node:url';

const MAX_BODY = 1024 * 1024;
const DEADLINE_MS = 10_000;
const MAX_ACTIVE = 8;
const bearer = /^Bearer amh1\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]{43}$/;
const operatorBearer = /^Bearer opr1\.[A-Za-z0-9_-]{43}$/;
const operatorPaths = new Set(['/operator/review/snapshot', '/operator/review/decision']);
const operatorStatuses = new Set([200, 400, 401, 404, 409, 413, 503]);

// The injectable request function exists for offline tests only. Runtime has a
// fixed upstream, no environment-controlled URL and no redirect handling.
export function createHandler({ request = http.request, deadlineMs = DEADLINE_MS } = {}) {
  let active = 0;
  return (incoming, outgoing) => {
    const fail = (status) => {
      if (!outgoing.headersSent) outgoing.writeHead(status, { 'content-type': 'application/json', 'cache-control': 'no-store', connection: 'close' });
      outgoing.end('{"error":"bridge_unavailable"}');
    };
    const operator = operatorPaths.has(incoming.url);
    if (incoming.method !== 'POST' || (incoming.url !== '/mcp' && !operator)) return fail(404);
    const authorization = incoming.headers.authorization;
    if (typeof authorization !== 'string' || authorization.length > 8200
      || !(operator ? operatorBearer : bearer).test(authorization)) return fail(401);
    if (incoming.headers['content-type']?.split(';')[0].trim().toLowerCase() !== 'application/json') return fail(415);
    if (active >= MAX_ACTIVE) return fail(503);
    const maxInput = operator ? 16 * 1024 : MAX_BODY;
    const length = incoming.headers['content-length'];
    if (length && (!/^\d+$/.test(length) || Number(length) > maxInput)) return fail(413);
    active++;
    let settled = false;
    let upstream;
    let upstreamResponse;
    const finish = (status, body) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      active--;
      upstream?.destroy();
      upstreamResponse?.destroy();
      if (outgoing.destroyed) return;
      if (body === undefined) return fail(status);
      outgoing.writeHead(status, { 'content-type': 'application/json', 'cache-control': 'no-store', connection: 'close' });
      outgoing.end(body);
    };
    const timer = setTimeout(() => finish(504), deadlineMs);
    outgoing.once('close', () => finish(499));
    incoming.once('aborted', () => finish(400));
    incoming.once('error', () => finish(400));
    let received = 0;
    const chunks = [];
    incoming.on('data', chunk => {
      if (settled) return;
      received += chunk.length;
      if (received > maxInput) return finish(413);
      chunks.push(chunk);
    });
    incoming.once('end', () => {
      if (settled) return;
      const body = Buffer.concat(chunks);
      try {
        upstream = request({ hostname: 'memex', port: 3000, path: incoming.url, method: 'POST', agent: false,
          headers: { authorization, 'content-type': 'application/json', accept: 'application/json', 'content-length': body.length } }, response => {
          upstreamResponse = response;
          if (settled) return response.destroy();
          if (!response.statusCode || (operator ? !operatorStatuses.has(response.statusCode) : response.statusCode < 200 || response.statusCode >= 300)
            || response.headers['content-type']?.split(';')[0].trim().toLowerCase() !== 'application/json') return finish(502);
          const result = [];
          let bytes = 0;
          response.on('data', chunk => {
            if (settled) return;
            bytes += chunk.length;
            if (bytes > MAX_BODY) return finish(502);
            result.push(chunk);
          });
          response.once('error', () => finish(502));
          response.once('aborted', () => finish(502));
          response.once('end', () => finish(response.statusCode, Buffer.concat(result)));
        });
        upstream.once('error', () => finish(502));
        upstream.end(body);
      } catch { finish(502); }
    });
  };
}

export function start() {
  const server = https.createServer({ key: readFileSync('/run/secrets/tls-key'), cert: readFileSync('/run/secrets/tls-cert'),
    minVersion: 'TLSv1.2', handshakeTimeout: 5_000, maxHeaderSize: 16 * 1024 }, createHandler());
  server.requestTimeout = 12_000;
  server.headersTimeout = 5_000;
  server.keepAliveTimeout = 1_000;
  server.maxConnections = 32;
  server.on('tlsClientError', () => {});
  server.listen(3443, '0.0.0.0');
  // Separate loopback-only liveness socket; never proxies requests.
  const health = http.createServer((req, res) => { res.writeHead(req.method === 'GET' && req.url === '/health' ? 200 : 404); res.end(); });
  health.maxConnections = 8; health.requestTimeout = 3_000; health.headersTimeout = 3_000;
  health.listen(3080, '127.0.0.1');
  const stop = () => { server.close(); health.close(); setTimeout(() => process.exit(0), 12_000).unref(); };
  process.once('SIGTERM', stop); process.once('SIGINT', stop);
}
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) start();
