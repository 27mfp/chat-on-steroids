import { existsSync, mkdtempSync, rmSync } from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { afterEach, expect, it, vi } from 'vitest';
import { bridgeAppId, prepareForkInstance } from '../src/main/fork-instance.js';
import { surfaceDefinition } from '../src/main/mcp/surfaces.js';

const roots: string[] = [];
afterEach(() => { for (const root of roots.splice(0)) rmSync(root, { recursive: true, force: true }); });

it('gives the fork bridge a distinct companion identity', () => {
  expect(bridgeAppId({})).toBe('chat-on-steroids');
  expect(bridgeAppId({ COS_FORK_INSTANCE: '1' })).toBe('chat-on-steroids-fork');
});

it('names the fork connector separately from the installed app', () => {
  vi.stubEnv('COS_FORK_INSTANCE', '1');
  try {
    expect(surfaceDefinition('core').connectorName).toBe('Chat On Steroids Fork Core');
    expect(surfaceDefinition('core').serverName).toBe('chat-on-steroids-core');
  } finally {
    vi.unstubAllEnvs();
  }
  expect(surfaceDefinition('core').connectorName).toBe('Chat On Steroids Core');
});

it('sets fork storage and identity before startup while preserving an ordinary launch', () => {
  const appData = mkdtempSync(path.join(os.tmpdir(), 'cos-fork-'));
  roots.push(appData);
  const app = {
    getPath: vi.fn(() => appData),
    setPath: vi.fn(),
    setName: vi.fn()
  };

  expect(prepareForkInstance(app as Parameters<typeof prepareForkInstance>[0], {})).toBe(false);
  expect(app.getPath).not.toHaveBeenCalled();
  expect(app.setPath).not.toHaveBeenCalled();

  expect(prepareForkInstance(app as Parameters<typeof prepareForkInstance>[0], { COS_FORK_INSTANCE: '1' })).toBe(true);
  const isolated = path.join(appData, 'chat-on-steroids-fork');
  expect(existsSync(isolated)).toBe(true);
  expect(app.getPath).toHaveBeenCalledWith('appData');
  expect(app.setName).toHaveBeenCalledWith('Chat On Steroids Fork');
  expect(app.setPath).toHaveBeenCalledWith('userData', isolated);
  expect(app.setPath).toHaveBeenCalledWith('sessionData', isolated);
});
