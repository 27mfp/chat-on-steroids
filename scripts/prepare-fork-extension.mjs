import { cpSync, existsSync, mkdirSync, readFileSync, renameSync, rmSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const source = path.join(root, 'extension');
const target = path.join(root, 'outputs', 'fork-extension');
const stage = `${target}.${process.pid}.new`;
const backup = `${target}.old`;
const ports = 'const PORTS = [8765, 8766, 8767, 8768, 8769];';
const appMarker = "body.app === 'chat-on-steroids'";
const background = readFileSync(path.join(source, 'background.js'), 'utf8');
if (background.split(ports).length !== 2) throw new Error('The companion port owner changed; review it before preparing the fork.');
if (background.split(appMarker).length !== 2) throw new Error('The companion app identity changed; review it before preparing the fork.');

mkdirSync(path.dirname(target), { recursive: true });
rmSync(stage, { recursive: true, force: true });
cpSync(source, stage, { recursive: true });
writeFileSync(path.join(stage, 'background.js'), background
  .replace(ports, 'const PORTS = [8769];')
  .replace(appMarker, "body.app === 'chat-on-steroids-fork'"));
const manifestPath = path.join(stage, 'manifest.json');
const manifest = JSON.parse(readFileSync(manifestPath, 'utf8'));
manifest.name = 'Chat On Steroids Fork companion';
manifest.action.default_title = 'Chat On Steroids Fork';
writeFileSync(manifestPath, `${JSON.stringify(manifest, null, 2)}\n`);
if (!existsSync(path.join(stage, 'manifest.json'))) throw new Error('Fork companion staging failed.');

// This is an explicit preparation command, run while the fork profile is closed.
rmSync(backup, { recursive: true, force: true });
if (existsSync(target)) renameSync(target, backup);
try {
  renameSync(stage, target);
  rmSync(backup, { recursive: true, force: true });
} catch (error) {
  if (existsSync(backup) && !existsSync(target)) renameSync(backup, target);
  throw error;
}
console.log(target);
