// Agent-side transport only. Squid outside the job remains the policy boundary.
import net from 'node:net';
const sockets = new Set();
const server = net.createServer(client => {
  if (sockets.size >= 16) { client.destroy(); return; }
  sockets.add(client);
  const upstream = net.createConnection({path:'/provider/provider.sock'});
  sockets.add(upstream);
  const close = () => { client.destroy(); upstream.destroy(); };
  for (const socket of [client, upstream]) {
    socket.setTimeout(60000, close);
    socket.on('error', close);
    socket.on('close', () => { sockets.delete(socket); close(); });
  }
  client.pipe(upstream); upstream.pipe(client);
});
server.on('error', () => { process.exitCode=1; stop(); });
function stop() {
  server.close();
  for (const socket of sockets) socket.destroy();
}
process.on('SIGTERM', stop); process.on('SIGINT', stop);
server.listen(3129,'127.0.0.1',() => process.stdout.write('ready\n'));
