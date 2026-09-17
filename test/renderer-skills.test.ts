import { beforeEach, afterEach, expect, it, vi } from 'vitest';
import { JSDOM } from 'jsdom';
import { invokedSkills } from '../src/shared/skill-invocation.js';
import type { LibrarySkill, SkillLibrary } from '../src/shared/skills.js';

let dom: JSDOM;
beforeEach(() => {
  vi.resetModules();
  dom = new JSDOM('<textarea id="input"></textarea><button id="skills">Skills</button><div id="picker" hidden></div><div id="selected" hidden></div>', { url: 'https://local.test' });
  Object.assign(globalThis, { window: dom.window, document: dom.window.document, Event: dom.window.Event, Node: dom.window.Node });
  dom.window.HTMLDialogElement.prototype.showModal = function () { this.open = true; };
  dom.window.HTMLDialogElement.prototype.close = function () { this.open = false; };
});
afterEach(() => dom.window.close());
const skill: LibrarySkill = { id: 'review', name: 'Review', description: 'Check changes', path: '/skills/review/SKILL.md', managed: true, scope: 'managed', source: 'managed', allowImplicitInvocation: true };
const library = (skills = [skill]): SkillLibrary => ({ skills, errors: [], roots: [], includeInstructions: true });
async function fixture() {
  const { initSkills } = await import('../src/renderer/skills.js');
  const input = document.getElementById('input') as HTMLTextAreaElement;
  const button = document.getElementById('skills')!;
  const host = document.getElementById('picker')!;
  let owner = 'a:1';
  const drafts = new Map<string, string>();
  const key = () => owner.split(':')[0]!;
  const list = vi.fn(async () => ({ ok: true as const, data: library() }));
  const importFile = vi.fn(async () => ({ ok: true as const, data: skill }));
  const picker = initSkills({ input, button, host, selectedHost: document.getElementById('selected')!, owner: () => owner,
    scope: () => ({ sessionId: key() }), draft: () => drafts.get(key()), saveDraft: text => drafts.set(key(), text), list, importFile,
    remove: vi.fn(async () => ({ ok: true as const, data: true })), openFolder: vi.fn(async () => ({ ok: true as const, data: undefined })) });
  const type = (value: string) => { input.value = value; input.setSelectionRange(value.length, value.length); input.dispatchEvent(new Event('input')); };
  const press = (value: string) => picker.keydown(new dom.window.KeyboardEvent('keydown', { key: value, cancelable: true }));
  const replace = (value: string) => { drafts.set(key(), value); input.value = value; picker.restore(); };
  return { input, button, host, list, importFile, picker, type, key: press, replace,
    owner: (value: string) => { owner = value; input.value = drafts.get(key()) ?? ''; picker.restore(); } };
}
const settle = async () => { await new Promise(resolve => setTimeout(resolve, 0)); };

it('parses only leading commands, supports /prompt, and deduplicates without consuming prose', () => {
  expect(invokedSkills('/review\n/prompt audit\n/review\nDo this /other')).toEqual(['review', 'audit']);
  expect(invokedSkills('Do /review')).toEqual([]);
  expect(invokedSkills('```\n/review\n```')).toEqual([]);
  expect(invokedSkills('/project/file.md')).toEqual([]);
  expect(() => invokedSkills('/prompt')).toThrow(/Choose/);
});

it('projects /prompt completion into chips while preserving the existing authored draft', async () => {
  const f = await fixture();
  f.type('/audit\n/prompt re'); await settle();
  expect(f.host.hidden).toBe(false);
  expect(f.key('Enter')).toBe(true);
  expect(f.input.value).toBe('');
  expect(invokedSkills(f.picker.authoredText())).toEqual(['audit', 'review']);
  expect(document.querySelectorAll('.composer-selected-skill')).toHaveLength(2);
  f.replace('/audit\nTask must stay exactly here');
  f.button.click(); await settle();
  (document.querySelector('.skill-use') as HTMLButtonElement).click();
  expect(f.input.value).toBe('Task must stay exactly here');
  expect(f.picker.authoredText()).toBe('/audit\n/review\nTask must stay exactly here');
});

it('never traps Enter when loading, empty or unmatched and does not refetch on each character', async () => {
  const f = await fixture();
  let resolve!: (value: { ok: true; data: SkillLibrary }) => void;
  f.list.mockImplementation(() => new Promise(done => { resolve = done; }));
  f.type('/'); expect(f.key('Enter')).toBe(false);
  resolve({ ok: true, data: library([]) }); await settle();
  f.type('/z'); expect(f.key('Enter')).toBe(false);
  f.type('/zz'); expect(f.key('Enter')).toBe(false);
  expect(f.list).toHaveBeenCalledTimes(1);
});

it('does not apply stale choices after caret movement or a selection', async () => {
  const f = await fixture(); f.type('/re'); await settle();
  f.input.setSelectionRange(1, 2);
  expect(f.key('Enter')).toBe(false); expect(f.input.value).toBe('/re');
});
it('waits for committed IME composition before opening autocomplete', async () => {
  const f = await fixture();
  f.input.dispatchEvent(new dom.window.CompositionEvent('compositionstart'));
  f.input.value = '/re'; f.input.setSelectionRange(3, 3);
  f.input.dispatchEvent(new dom.window.InputEvent('input', { isComposing: true }));
  await settle(); expect(f.list).not.toHaveBeenCalled(); expect(f.host.hidden).toBe(true);
  f.input.dispatchEvent(new dom.window.CompositionEvent('compositionend'));
  await settle(); expect(f.list).toHaveBeenCalledTimes(1); expect(f.host.hidden).toBe(false);
});

it('rejects pending import across A→B→A draft epochs and Escape closes button-focused popup', async () => {
  const f = await fixture();
  let resolve!: (value: { ok: true; data: typeof skill }) => void;
  f.importFile.mockImplementation(() => new Promise(done => { resolve = done; }));
  f.type('Original task'); f.button.click(); await settle();
  document.getElementById('skillsImport')!.click();
  f.owner('b:2'); f.picker.close(); f.owner('a:3');
  resolve({ ok: true, data: skill }); await settle();
  expect(f.input.value).toBe('Original task');
  f.button.click(); await settle();
  const button = document.querySelector<HTMLButtonElement>('.skill-use')!; button.focus();
  button.dispatchEvent(new dom.window.KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
  expect((document.getElementById('skillsDialog') as HTMLDialogElement).open).toBe(false);
});

it('keeps chips in the existing per-chat draft through A to B to A and removes only the chosen directive', async () => {
  const f = await fixture();
  f.replace('/review\n/audit\nKeep my task exactly.\nProse /review stays literal.');
  f.owner('b:2'); f.type('Other chat');
  f.owner('a:3');
  expect(document.querySelectorAll('.composer-selected-skill')).toHaveLength(2);
  expect(f.input.value).toBe('Keep my task exactly.\nProse /review stays literal.');
  document.querySelector<HTMLButtonElement>('[data-skill-id="review"] .composer-selected-skill-remove')!.click();
  expect(f.picker.authoredText()).toBe('/audit\nKeep my task exactly.\nProse /review stays literal.');
  f.owner('b:4'); expect(f.picker.authoredText()).toBe('Other chat');
});

it('shows a failed library load with retry controls and ignores the old scope result', async () => {
  const f = await fixture();
  f.list.mockRejectedValueOnce(new Error('Disk is unavailable'));
  f.button.click(); await settle();
  expect(document.getElementById('skillsStatus')!.textContent).toContain('Disk is unavailable');
  expect(document.getElementById('skillsList')!.textContent).toContain('could not be loaded');
  document.getElementById('skillsRefresh')!.click(); await settle();
  expect(document.querySelector('.skill-use')).not.toBeNull();
  f.picker.close();
  let resolve!: (value: { ok: true; data: SkillLibrary }) => void;
  f.list.mockImplementationOnce(() => new Promise(done => { resolve = done; }));
  f.button.click(); f.owner('b:2'); f.type('B draft');
  resolve({ ok: true, data: library() }); await settle();
  expect(f.picker.authoredText()).toBe('B draft');
  expect((document.getElementById('skillsDialog') as HTMLDialogElement).open).toBe(false);
});
