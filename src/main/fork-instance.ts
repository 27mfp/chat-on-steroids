/** A source-checkout launcher that keeps this fork's test work away from an installed app. */
import { mkdirSync } from 'node:fs';
import path from 'node:path';
import type { App } from 'electron';

type Paths = Pick<App, 'getPath' | 'setPath' | 'setName'>;

export function forkInstanceEnabled(env: NodeJS.ProcessEnv = process.env): boolean {
  return env.COS_FORK_INSTANCE === '1';
}

export function bridgeAppId(env: NodeJS.ProcessEnv = process.env): string {
  return forkInstanceEnabled(env) ? 'chat-on-steroids-fork' : 'chat-on-steroids';
}

export function prepareForkInstance(app: Paths, env: NodeJS.ProcessEnv = process.env): boolean {
  if (!forkInstanceEnabled(env)) return false;
  const userData = path.join(app.getPath('appData'), 'chat-on-steroids-fork');
  mkdirSync(userData, { recursive: true, mode: 0o700 });
  app.setName('Chat On Steroids Fork');
  app.setPath('userData', userData);
  app.setPath('sessionData', userData);
  return true;
}
