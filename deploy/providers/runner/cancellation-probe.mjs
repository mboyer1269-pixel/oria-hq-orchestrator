// Synthetic fixture only. Run exclusively in an idle pilot container.
// A detached child keeps writing to a marker outside the candidate repository.
import fs from 'node:fs';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
const marker = '/workspace/hq-cancellation-probe.marker';
if (process.argv[2] === 'child') {
  setInterval(() => fs.appendFileSync(marker, 'tick\n'), 100);
} else {
  fs.writeFileSync(marker, 'fixture\n', { flag: 'wx', mode: 0o600 });
  spawn(process.execPath, [fileURLToPath(import.meta.url), 'child'], { detached: true, stdio: 'ignore' }).unref();
  setInterval(() => {}, 1000);
}
