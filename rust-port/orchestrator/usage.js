// Read-only account usage through AdaL's installed backend client. No inference.
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import {pathToFileURL} from 'node:url';
import {randomUUID} from 'node:crypto';
const install = process.argv[2];
const workspace = process.argv[3];
let backend;
function emit(data) { process.stdout.write(JSON.stringify(data) + '\n'); }
async function main() {
  const files = fs.readdirSync(path.join(install, 'chunks')).filter(x => x.endsWith('.js'));
  const find = marker => {
    const file = files.find(x => fs.readFileSync(path.join(install, 'chunks', x), 'utf8').includes(marker));
    if (!file) throw new Error('Installed AdaL usage adapter is unsupported after this update');
    return pathToFileURL(path.join(install, 'chunks', file)).href;
  };
  const {H, J} = await import(find('function H(e){let t={};if(e.spawnerConfig)'));
  const {U} = await import(find('async getUsage(){return d.request({endpoint:"/auth/usage"})}'));
  if (!H || !J || !U) throw new Error('Installed AdaL usage adapter exports changed');
  const credentials = JSON.parse(fs.readFileSync(path.join(os.homedir(), '.adal/adal_oauth_creds.json'), 'utf8'));
  if (!credentials.access_token) throw new Error('AdaL login is unavailable');
  const sessionId = randomUUID();
  const adapters = H({spawnerConfig: {workingDirectory: workspace, sessionId,
    nonInteractive: true, enabledDefaultTools: 'Read'},
    authConfig: {sessionId, mode: J.HEADLESS, token: credentials.access_token},
    entryScriptPath: path.join(install, 'adal-cli.js'), appUrl: 'https://adal.sylph.ai'});
  backend = adapters.backendSpawner;
  const cleanup = () => { backend?.destroy(); process.exit(0); };
  process.on('SIGTERM', cleanup); process.on('SIGINT', cleanup);
  await backend.start();
  const client = U(backend.getBaseUrl());
  const auth = await adapters.auth.authenticate(client);
  if (!auth.success) throw new Error('AdaL usage authentication failed; sign in through AdaL');
  async function refresh() {
    try {
      const usage = await client.getUsage();
      const weekly = usage.weekly_usage;
      emit({status:'available', updated_at:Date.now()/1000,
        plan: usage.plan?.name || 'Unknown', wallet_balance: usage.wallet_balance,
        weekly: weekly ? {percentage:weekly.usage_percentage, resets_at:weekly.resets_at,
          limited:weekly.is_usage_limited, guidance:weekly.guidance_message} : null});
    } catch { emit({status:'unavailable', error:'AdaL account usage could not be refreshed', updated_at:Date.now()/1000}); }
  }
  await refresh();
  setInterval(refresh, 30000);
}
main().catch(() => {
  emit({status:'unavailable', error:'Installed AdaL usage adapter or login is unavailable', updated_at:Date.now()/1000});
  backend?.destroy(); process.exitCode = 1;
});
