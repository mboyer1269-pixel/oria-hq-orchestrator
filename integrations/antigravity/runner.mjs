import { spawn } from 'node:child_process';
import path from 'node:path';
import { parseSessionStream, ProtocolError } from './contract.mjs';

const MAX_PROMPT_BYTES = 64 * 1024;
const MAX_STDOUT_BYTES = 1024 * 1024;
const MAX_STDERR_BYTES = 64 * 1024;

export function buildInvocation({ executable, cwd, home, prompt, timeoutMs = 60000 }) {
  if (![executable, cwd, home].every(value => typeof value === 'string' && path.isAbsolute(value))
    || typeof prompt !== 'string' || !prompt.trim() || /^\s*\//m.test(prompt) || Buffer.byteLength(prompt) > MAX_PROMPT_BYTES
    || !Number.isSafeInteger(timeoutMs) || timeoutMs < 50 || timeoutMs > 300000) {
    throw new TypeError('invalid_runner_configuration');
  }
  return { executable, cwd, timeoutMs,
    args: ['--mode', 'plan', '--input-format', 'stream-json', '--output-format', 'stream-json',
      '--print-timeout', `${timeoutMs}ms`, '--sandbox'],
    input: `${JSON.stringify({ event: 'user', message: { content: prompt } })}\n`,
    // Explicit minimal environment: never inherit arbitrary provider keys or NODE_OPTIONS.
    env: { HOME: home, USERPROFILE: home, AGY_CLI_DISABLE_AUTO_UPDATE: 'true',
      ...(process.env.PATH ? { PATH: process.env.PATH } : {}),
      ...(process.env.SystemRoot ? { SystemRoot: process.env.SystemRoot } : {}) },
  };
}

/** spawnImpl is a test seam, never an API/client option. No provider is invoked on import. */
export function createRunner(spawnImpl = spawn) {
  return async function run(options) {
    const invocation = buildInvocation(options);
    if (options.signal?.aborted) return { ok: false, code: 'cancelled', stopConfirmed: true, stopScope: 'local_child_only' };
    return new Promise(resolve => {
      let child, timeout, escalation, deadline;
      let finished = false;
      let failure = null;
      let stdout = [], stderr = [], outBytes = 0, errBytes = 0;
      const finish = result => {
        if (finished) return;
        finished = true;
        clearTimeout(timeout); clearTimeout(escalation); clearTimeout(deadline);
        options.signal?.removeEventListener('abort', cancel);
        resolve({ ...result, stopScope: 'local_child_only' });
      };
      const kill = signal => {
        if (!child?.pid) return;
        try {
          if (process.platform !== 'win32') process.kill(-child.pid, signal);
          else child.kill(signal);
        } catch { /* Close/deadline determines whether stop is confirmed. */ }
      };
      const stop = code => {
        if (finished || failure) return;
        failure = code;
        kill('SIGTERM');
        escalation = setTimeout(() => kill('SIGKILL'), 250);
        deadline = setTimeout(() => {
          child.stdout?.destroy(); child.stderr?.destroy(); child.stdin?.destroy(); child.unref?.();
          finish({ ok: false, code, stopConfirmed: false });
        }, 2000);
      };
      const cancel = () => stop('cancelled');
      try {
        child = spawnImpl(invocation.executable, invocation.args, {
          cwd: invocation.cwd, env: invocation.env, shell: false, windowsHide: true,
          detached: process.platform !== 'win32', stdio: ['pipe', 'pipe', 'pipe'],
        });
      } catch { finish({ ok: false, code: 'spawn_failed', stopConfirmed: true }); return; }
      options.signal?.addEventListener('abort', cancel, { once: true });
      if (options.signal?.aborted) cancel();
      timeout = setTimeout(() => stop('timeout'), invocation.timeoutMs);
      child.on('error', () => {
        if (child.pid) stop('process_error');
        else finish({ ok: false, code: 'spawn_failed', stopConfirmed: true });
      });
      child.stdin.on('error', () => stop('stdin_failed'));
      child.stdout.on('data', chunk => {
        outBytes += chunk.length;
        if (outBytes > MAX_STDOUT_BYTES) stop('output_limit');
        else if (!failure) stdout.push(chunk);
      });
      child.stderr.on('data', chunk => {
        errBytes += chunk.length;
        if (errBytes > MAX_STDERR_BYTES) stop('output_limit');
        else if (!failure) stderr.push(chunk);
      });
      child.on('close', (exitCode, signal) => {
        if (failure) { finish({ ok: false, code: failure, stopConfirmed: true }); return; }
        if (exitCode !== 0 || signal) { finish({ ok: false, code: 'process_failed', exitCode, stopConfirmed: true }); return; }
        try {
          const decoder = new TextDecoder('utf-8', { fatal: true });
          const result = parseSessionStream(decoder.decode(Buffer.concat(stdout)), decoder.decode(Buffer.concat(stderr)));
          finish({ ok: true, ...result });
        } catch (error) {
          finish({ ok: false, code: error instanceof ProtocolError ? error.code : 'invalid_protocol', stopConfirmed: true });
        } finally { stdout = []; stderr = []; }
      });
      child.stdin.end(invocation.input);
    });
  };
}

export const runAntigravity = createRunner();
