// Synthetic executable only. No vendor code, network or model calls.
let input = '';
for await (const chunk of process.stdin) input += chunk;
const message = JSON.parse(input);
const mode = message.message.content;
const session = '11111111-1111-4111-8111-111111111111';
if (mode === 'hang') { setInterval(() => {}, 1000); }
else if (mode === 'nonzero') { process.stderr.write('synthetic private diagnostic'); process.exitCode = 7; }
else if (mode === 'malformed') { process.stdout.write('{broken'); }
else if (mode === 'oversize') { process.stdout.write('x'.repeat(1100000)); }
else {
  if (mode === 'soft-denial') process.stderr.write('Tool run_command soft-denied: permission required');
  if (mode === 'plan-warning') process.stderr.write("WARNING: --mode plan has no effect while slash command expansion is disabled.");
  const result = { conversation_id: session, status: 'SUCCESS', response: 'Synthetic plan.',
    duration_seconds: 0.1, num_turns: 1 };
  if (mode !== 'missing-usage') result.usage = { input_tokens: 20, output_tokens: 3, thinking_tokens: 1, cache_read_tokens: 0, total_tokens: 23 };
  process.stdout.write(JSON.stringify({ event: 'init', conversation_id: session, init: { permission_mode: 'request-review' } }) + '\n');
  process.stdout.write(JSON.stringify({ event: 'result', result }) + '\n');
}
