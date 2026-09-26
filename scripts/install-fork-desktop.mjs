import { existsSync, mkdirSync, readFileSync, renameSync, writeFileSync } from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const launcher = path.join(root, 'scripts', 'run-fork-local.sh');
const icon = path.join(root, 'extension', 'icons', 'icon128.png');
const applications = path.join(process.env.XDG_DATA_HOME || path.join(os.homedir(), '.local', 'share'), 'applications');
const target = path.join(applications, 'com.27mfp.chatonsteroids.fork.desktop');
const owner = 'X-COS-ForkLauncher=true';

if (!existsSync(launcher) || !existsSync(icon)) {
  throw new Error('The fork launcher or icon is missing from this checkout.');
}
if (existsSync(target) && !readFileSync(target, 'utf8').includes(owner)) {
  throw new Error(`Refusing to replace an unrelated desktop entry: ${target}`);
}

const desktop = [
  '[Desktop Entry]',
  'Type=Application',
  'Name=Chat On Steroids Fork',
  'Comment=Isolated local test build of Chat On Steroids',
  `Exec="${launcher}"`,
  `TryExec=${launcher}`,
  `Icon=${icon}`,
  'Terminal=false',
  'Categories=Development;Utility;',
  owner,
  ''
].join('\n');
mkdirSync(applications, { recursive: true });
const stage = `${target}.${process.pid}.tmp`;
writeFileSync(stage, desktop, { mode: 0o644 });
renameSync(stage, target);
console.log(target);
