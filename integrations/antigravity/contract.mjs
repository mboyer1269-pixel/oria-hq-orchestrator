// Protocol observed in Google's headless documentation; fixtures are synthetic.
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const STATUSES = new Set(['SUCCESS', 'ERROR', 'CANCELED', 'INTERRUPTED', 'INVALID', 'WAITING', 'RUNNING']);
const record = value => value !== null && typeof value === 'object' && !Array.isArray(value);
const count = value => Number.isSafeInteger(value) && value >= 0;
export class ProtocolError extends Error {
  constructor(code) { super(code); this.name = 'ProtocolError'; this.code = code; }
}
const invalid = () => { throw new ProtocolError('invalid_protocol'); };

export function parseTerminalResult(value) {
  if (!record(value) || !STATUSES.has(value.status)) invalid();
  if (value.status !== 'SUCCESS') throw new ProtocolError('provider_not_successful');
  if (typeof value.conversation_id !== 'string' || !UUID.test(value.conversation_id)
    || typeof value.response !== 'string' || !value.response.trim()
    || !Number.isFinite(value.duration_seconds) || value.duration_seconds < 0
    || !count(value.num_turns) || value.num_turns !== 1
    || (value.error !== undefined && value.error !== null && value.error !== '')) invalid();
  let usage = null;
  if (value.usage !== undefined && value.usage !== null) {
    if (!record(value.usage)) invalid();
    const keys = ['input_tokens', 'output_tokens', 'thinking_tokens', 'cache_read_tokens', 'total_tokens'];
    if (keys.some(key => !count(value.usage[key]))) invalid();
    usage = Object.fromEntries(keys.map(key => [key, value.usage[key]]));
  }
  return { providerStatus: 'SUCCESS', response: value.response,
    sessionId: value.conversation_id, durationSeconds: value.duration_seconds,
    usage, usageBasis: usage ? 'single_session' : 'unknown',
    deliveryVerified: false };
}

/** Exactly one fresh session and one turn. No automatic continuation or replay. */
export function parseSessionStream(stdout, stderr = '') {
  // Any diagnostic is held for review. This deliberately rejects benign warnings too:
  // Google documents soft permission denial on stderr even with exit code zero.
  if (stderr.trim()) throw new ProtocolError('diagnostic_requires_review');
  const lines = stdout.split(/\r?\n/).filter(line => line.trim());
  if (lines.length < 2 || lines.length > 10000) invalid();
  let sessionId;
  let terminal;
  for (let index = 0; index < lines.length; index++) {
    let event;
    try { event = JSON.parse(lines[index]); } catch { invalid(); }
    if (!record(event) || typeof event.event !== 'string') invalid();
    if (event.event === 'init') {
      if (index !== 0 || !UUID.test(event.conversation_id ?? '') || !record(event.init)) invalid();
      if (event.init.permission_mode !== 'request-review') throw new ProtocolError('unsafe_permission_mode');
      sessionId = event.conversation_id;
    } else if (event.event === 'step_update') {
      if (!sessionId || terminal || !record(event.step_update)
        || event.step_update.conversation_id !== sessionId) invalid();
      if (record(event.step_update.tool_info) && event.step_update.tool_info.error) {
        throw new ProtocolError('tool_failed');
      }
    } else if (event.event === 'result') {
      if (!sessionId || terminal || index !== lines.length - 1) invalid();
      terminal = parseTerminalResult(event.result);
      if (terminal.sessionId !== sessionId) invalid();
    } else invalid();
  }
  if (!terminal) invalid();
  return terminal;
}
