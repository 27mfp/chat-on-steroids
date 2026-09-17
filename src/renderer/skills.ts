import type { LibrarySkill, SkillLibrary, SkillSummary, SkillsDraftScope } from '../shared/skills.js';
import { el, icon } from './dom.js';
import { t, ui } from './i18n.js';
import { skillDirectives } from '../shared/skill-invocation.js';

/** Completion is limited to the leading command block and a collapsed caret. */
export function skillCompletion(text: string, start: number, end = start): { start: number; end: number; query: string } | null {
  if (start !== end || /\S/.test(text.slice(end).split(/\s/, 1)[0] ?? '')) return null;
  const before = text.slice(0, start);
  const match = /(?:^|\s)(\/(?:prompt(?:\s+[a-z0-9._-]*)?|[a-z0-9._-]*))$/i.exec(before);
  if (!match) return null;
  const at = start - match[1]!.length;
  const preceding = text.slice(0, at).trim();
  if (preceding && !/^(?:\/(?!prompt(?:\s|$))[a-z0-9._-]+|\/prompt\s+[a-z0-9._-]+)(?:\s+(?:\/(?!prompt(?:\s|$))[a-z0-9._-]+|\/prompt\s+[a-z0-9._-]+))*$/i.test(preceding)) return null;
  const token = match[1]!;
  return { start: at, end, query: token === '/prompt' ? '' : token.replace(/^\/prompt\s+|^\//, '').toLowerCase() };
}

type Reply<T> = { ok: true; data: T } | { ok: false; error: string };
type Options = {
  input: HTMLTextAreaElement; button: HTMLElement; host: HTMLElement; selectedHost: HTMLElement;
  owner: () => string;
  scope: () => SkillsDraftScope;
  draft: () => string | undefined;
  saveDraft: (authored: string) => void;
  list: (scope: SkillsDraftScope) => Promise<Reply<SkillLibrary>>;
  importFile: (kind: 'file' | 'package') => Promise<Reply<SkillSummary | null>>;
  remove: (id: string) => Promise<Reply<boolean>>;
  openFolder: () => Promise<Reply<void>>;
};

function split(text: string): ReturnType<typeof skillDirectives> {
  try { return skillDirectives(text); }
  catch { return { ids: [], prefix: '', body: text }; } // Incomplete typed commands remain visible.
}
const title = (skill: LibrarySkill): string => skill.displayName || skill.name;
const scopeLabel = (skill: LibrarySkill): string => skill.scope === 'repo' ? t('Project')
  : skill.scope === 'system' ? t('System') : skill.scope === 'admin' ? t('Admin') : t('Personal');

/** PR #260's library/chips are projections of the existing authored draft, not a second selection ledger. */
export function initSkills(options: Options) {
  const { input, button, host, selectedHost } = options;
  const dialog = el('dialog', 'skills-dialog') as HTMLDialogElement;
  dialog.id = 'skillsDialog'; dialog.setAttribute('aria-labelledby', 'skillsDialogTitle');
  const heading = el('div', 'skills-dialog-head'), caption = el('div');
  const headingText = el('h2', '', () => t('Skills')); headingText.id = 'skillsDialogTitle';
  caption.append(headingText, el('p', '', () => t('Reusable instructions for your chats.')));
  const control = (label: string, className = 'btn'): HTMLButtonElement => {
    const node = el('button', className, () => t(label)) as HTMLButtonElement; node.type = 'button'; return node;
  };
  const dismiss = control('Close skills', 'btn btn-icon'); dismiss.id = 'skillsClose';
  dismiss.replaceChildren(icon('i-x')); ui(dismiss, 'aria-label', () => t('Close skills'));
  heading.append(caption, dismiss);
  const body = el('div', 'skills-dialog-body'), searchLabel = el('label', 'skills-search');
  const search = document.createElement('input'); search.type = 'search'; search.id = 'skillsSearch'; search.autocomplete = 'off';
  ui(search, 'placeholder', () => t('Search skills')); ui(search, 'aria-label', () => t('Search skills'));
  searchLabel.append(icon('i-search'), search);
  const status = el('p', 'skills-status'); status.id = 'skillsStatus'; status.setAttribute('role', 'status');
  const list = el('div', 'skills-list'); list.id = 'skillsList';
  body.append(searchLabel, status, list);
  const actions = el('div', 'skills-dialog-actions');
  const refresh = control('Refresh'), importFile = control('Import skill file'), importPackage = control('Import package'), openFolder = control('Open skill directory');
  refresh.id = 'skillsRefresh'; importFile.id = 'skillsImport'; importPackage.id = 'skillsImportPackage'; openFolder.id = 'skillsOpenFolder';
  actions.append(openFolder, refresh, importFile, importPackage); dialog.append(heading, body, actions); document.body.append(dialog);
  host.className = 'skill-autocomplete'; host.setAttribute('role', 'listbox');

  const cache = new Map<string, SkillLibrary>();
  let epoch = 0, surfaceOwner = '', loadedKey: string | null = null, loading = false, error = '', composing = false;
  let library: SkillLibrary | null = null, choices: LibrarySkill[] = [], selected = 0, painted = '';
  // This is only the current textarea projection. The existing draft map holds the
  // complete authored command block across navigation, failures and retries.
  let displayedPrefix = '', prefixOwner = options.owner();
  const scopeKey = (): string => JSON.stringify(options.scope());
  const selectionKey = (): string => `${input.value}\0${input.selectionStart}\0${input.selectionEnd}`;
  const authoredText = (): string => (prefixOwner === options.owner() ? displayedPrefix : '') + input.value;
  const fragment = () => skillCompletion(input.value, input.selectionStart, input.selectionEnd);
  const current = (): boolean => surfaceOwner === options.owner();
  const hideInline = (): void => {
    host.hidden = true; choices = []; input.removeAttribute('aria-controls'); input.removeAttribute('aria-expanded'); input.removeAttribute('aria-activedescendant');
  };
  const close = (): void => {
    epoch++; loading = false; loadedKey = null; hideInline();
    if (dialog.open) dialog.close();
    if (prefixOwner !== options.owner()) { selectedHost.replaceChildren(); selectedHost.hidden = true; }
  };
  const renderSelected = (): void => {
    selectedHost.replaceChildren();
    const ids = split(prefixOwner === options.owner() ? displayedPrefix : '').ids;
    selectedHost.hidden = !ids.length;
    const catalog = cache.get(scopeKey());
    for (const id of ids) {
      const skill = catalog?.skills.find(row => row.id === id);
      const name = skill ? title(skill) : id;
      const chip = el('div', 'composer-selected-skill'); chip.dataset.skillId = id;
      chip.title = skill?.path ?? `/${id}`;
      const remove = control('Remove', 'composer-selected-skill-remove'); remove.replaceChildren(icon('i-x'));
      ui(remove, 'aria-label', () => t('Remove {0}', [name]));
      const owner = options.owner();
      remove.addEventListener('click', () => {
        if (owner !== options.owner()) return;
        const retained = split(displayedPrefix).ids.filter(value => value !== id);
        project(`${retained.map(value => `/${value}\n`).join('')}${input.value}`);
        input.focus();
      });
      chip.append(icon('i-skill', 'ico composer-selected-skill-icon'), el('span', 'composer-selected-skill-title', name), remove);
      selectedHost.append(chip);
    }
  };
  const restore = (): void => {
    close();
    const draft = split(options.draft() ?? input.value);
    displayedPrefix = draft.prefix; prefixOwner = options.owner(); input.value = draft.body;
    renderSelected();
  };
  const project = (authored: string): void => {
    options.saveDraft(authored);
    const draft = split(authored); displayedPrefix = draft.prefix; prefixOwner = options.owner(); input.value = draft.body;
    renderSelected(); input.setSelectionRange(input.value.length, input.value.length);
    input.dispatchEvent(new input.ownerDocument.defaultView!.Event('input', { bubbles: true }));
  };
  const choose = (skill: LibrarySkill): void => {
    if (!current() || composing) { close(); return; }
    const range = fragment();
    if (!dialog.open && (!range || painted !== selectionKey())) { close(); return; }
    const text = range ? input.value.slice(0, range.start) + input.value.slice(range.end).replace(/^\s+/, '') : input.value;
    const draft = split((prefixOwner === options.owner() ? displayedPrefix : '') + text);
    const prefix = draft.ids.includes(skill.id) ? draft.prefix
      : `${draft.prefix}${draft.prefix && !/\s$/.test(draft.prefix) ? '\n' : ''}/${skill.id}\n`;
    close(); project(prefix + draft.body); input.focus();
  };
  const filtered = (query: string): LibrarySkill[] => {
    const needle = query.trim().toLocaleLowerCase();
    return (library?.skills ?? []).filter(skill => `${skill.id} ${title(skill)} ${skill.description} ${skill.scope}`.toLocaleLowerCase().includes(needle));
  };
  const paintInline = (): void => {
    if (!current() || dialog.open || composing) { hideInline(); return; }
    const range = fragment();
    if (!range) { hideInline(); return; }
    choices = loading && !library ? [] : filtered(range.query).slice(0, 12);
    selected = Math.min(selected, Math.max(0, choices.length - 1)); painted = selectionKey();
    host.replaceChildren(); host.hidden = !choices.length;
    if (host.hidden) { hideInline(); return; }
    input.setAttribute('aria-expanded', 'true'); input.setAttribute('aria-controls', host.id);
    for (const [index, skill] of choices.entries()) {
      const row = control('Use', 'skill-choice skill-autocomplete-option slash-menu-option');
      row.replaceChildren(); row.id = `skill-option-${index}`; row.setAttribute('role', 'option'); row.setAttribute('aria-selected', String(index === selected));
      row.dataset.skillId = skill.id; row.title = skill.path;
      const copy = el('span', 'slash-menu-copy'); copy.append(el('strong', '', title(skill)), el('small', '', skill.shortDescription ?? skill.description));
      row.append(icon('i-skill', 'ico slash-menu-icon'), copy, el('span', 'slash-menu-meta', () => scopeLabel(skill)));
      row.addEventListener('pointerdown', event => event.preventDefault()); row.addEventListener('click', () => choose(skill)); host.append(row);
    }
    input.setAttribute('aria-activedescendant', `skill-option-${selected}`);
  };
  const paintDialog = (): void => {
    if (!dialog.open || !current()) return;
    refresh.disabled = loading;
    status.textContent = error || (library?.errors.join('\n') ?? ''); status.classList.toggle('skills-errors', !!status.textContent);
    list.replaceChildren();
    const rows = filtered(search.value);
    if (!rows.length) {
      list.append(el('p', 'skills-empty', () => loading ? t('Loading skills…') : error ? t('Skills could not be loaded.')
        : search.value.trim() ? t('No skills match your search.') : t('No skills installed. Import a Markdown or text file.')));
      return;
    }
    for (const skill of rows) {
      const row = el('article', 'skill-row'); row.dataset.skillId = skill.id;
      const copy = el('div', 'skill-row-copy'), heading = el('div', 'skill-row-heading');
      heading.append(el('strong', '', title(skill)), el('span', 'skill-row-scope', () => scopeLabel(skill)));
      copy.append(heading, el('p', '', skill.description), el('code', 'skill-row-source', skill.path));
      const actions = el('div', 'skill-row-actions');
      if (skill.managed) {
        const remove = control('Remove', 'btn skill-remove'); ui(remove, 'aria-label', () => t('Remove {0}', [title(skill)]));
        remove.addEventListener('click', async () => {
          const owner = options.owner(), request = epoch; remove.disabled = true;
          try {
            const result = await options.remove(skill.id);
            if (owner !== options.owner() || request !== epoch) return;
            if (!result.ok) { error = result.error; paintDialog(); }
            else if (result.data) await load();
          } catch (failure) { if (request === epoch && current()) { error = String(failure); paintDialog(); } }
          finally { if (remove.isConnected) remove.disabled = false; }
        });
        actions.append(remove);
      }
      const use = control('Use', 'btn btn-solid skill-use'); ui(use, 'aria-label', () => t('Use {0}', [title(skill)]));
      use.addEventListener('click', () => choose(skill)); actions.append(use); row.append(copy, actions); list.append(row);
    }
  };
  const load = async (): Promise<void> => {
    const request = ++epoch, owner = options.owner(), scope = options.scope(), key = JSON.stringify(scope);
    surfaceOwner = owner; loadedKey = key; loading = true; error = ''; library = cache.get(key) ?? null;
    paintDialog(); paintInline();
    try {
      const result = await options.list(scope);
      if (request !== epoch || owner !== options.owner() || scopeKey() !== key) return;
      if (!result.ok) error = result.error;
      else {
        library = result.data; cache.delete(key); cache.set(key, library);
        while (cache.size > 12) cache.delete(cache.keys().next().value!);
      }
    } catch (failure) { if (request === epoch && current()) error = failure instanceof Error ? failure.message : String(failure); }
    finally { if (request === epoch && current()) { loading = false; paintDialog(); paintInline(); renderSelected(); } }
  };
  const open = (): void => {
    hideInline(); surfaceOwner = options.owner(); search.value = '';
    if (!dialog.open) dialog.showModal(); search.focus(); void load();
  };
  const importSelected = async (kind: 'file' | 'package', button: HTMLButtonElement): Promise<void> => {
    const owner = options.owner(), request = epoch; button.disabled = true;
    try {
      const result = await options.importFile(kind);
      if (owner !== options.owner() || request !== epoch) return;
      if (!result.ok) { error = result.error; paintDialog(); }
      else if (result.data) await load();
    } catch (failure) { if (request === epoch && current()) { error = String(failure); paintDialog(); } }
    finally { button.disabled = false; }
  };
  const update = (): void => {
    options.saveDraft(authoredText());
    if (composing || dialog.open) return;
    if (!fragment()) { hideInline(); loadedKey = null; return; }
    selected = 0;
    if (loadedKey !== scopeKey() || !current()) void load(); else paintInline();
  };
  button.addEventListener('click', open); dismiss.addEventListener('click', close);
  refresh.addEventListener('click', () => void load()); search.addEventListener('input', paintDialog);
  search.addEventListener('keydown', event => {
    if (!event.isComposing && (event.key === 'ArrowDown' || event.key === 'Enter')) {
      const first = list.querySelector<HTMLButtonElement>('.skill-use');
      if (first) { event.preventDefault(); first.focus(); }
    }
  });
  list.addEventListener('keydown', event => {
    if (event.isComposing || !['ArrowDown', 'ArrowUp'].includes(event.key)) return;
    const buttons = [...list.querySelectorAll<HTMLButtonElement>('.skill-use')];
    const at = buttons.indexOf(document.activeElement as HTMLButtonElement);
    if (at >= 0 && buttons.length) { event.preventDefault(); buttons[(at + (event.key === 'ArrowDown' ? 1 : buttons.length - 1)) % buttons.length]!.focus(); }
  });
  importFile.addEventListener('click', () => void importSelected('file', importFile)); importPackage.addEventListener('click', () => void importSelected('package', importPackage));
  openFolder.addEventListener('click', async () => {
    const request = epoch;
    try { const result = await options.openFolder(); if (request === epoch && !result.ok) { error = result.error; paintDialog(); } }
    catch (failure) { if (request === epoch && current()) { error = String(failure); paintDialog(); } }
  });
  dialog.addEventListener('click', event => { if (event.target === dialog) close(); });
  dialog.addEventListener('cancel', event => { event.preventDefault(); close(); input.focus(); });
  dialog.addEventListener('keydown', event => { if (event.key === 'Escape' && !event.isComposing) { event.preventDefault(); close(); input.focus(); } });
  input.addEventListener('compositionstart', () => { composing = true; hideInline(); });
  input.addEventListener('compositionend', () => { composing = false; update(); });
  input.addEventListener('input', event => { if ((event as InputEvent).isComposing) { hideInline(); return; } update(); });
  input.addEventListener('click', () => { if (!host.hidden) paintInline(); });
  document.addEventListener('click', event => {
    if (!host.contains(event.target as Node) && !button.contains(event.target as Node) && event.target !== input) hideInline();
  });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && !event.isComposing && !host.hidden) { hideInline(); input.focus(); }
  });
  return { open, close, restore, authoredText, keydown: (event: KeyboardEvent): boolean => {
    if (host.hidden || !current() || composing || event.isComposing) return false;
    if (!fragment() || painted !== selectionKey()) { hideInline(); return false; }
    if (event.key === 'Escape') { hideInline(); event.preventDefault(); return true; }
    if (!choices.length || loading || event.shiftKey || event.ctrlKey || event.altKey || event.metaKey) return false;
    if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
      selected = (selected + (event.key === 'ArrowDown' ? 1 : choices.length - 1)) % choices.length; paintInline();
    } else if (event.key === 'Enter' || event.key === 'Tab') choose(choices[selected]!);
    else return false;
    event.preventDefault(); return true;
  } };
}
