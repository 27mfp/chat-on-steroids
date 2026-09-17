# Workspace refinement — 2026-09-17

## Requested behavior

The final Skills interaction replaces the sidebar/library modal with the composer's leading `/`
menu. Commands and Skills use compact rows; a small icon-only plus at the bottom inserts
`Please add the following skills to my COS skills:` without submitting or importing anything.
This supersedes the earlier file-import and separate library design. The original large library
and Use action came from PR #260; the old separate file/package controls were local adaptations.
Skill discovery and authored selections retain the contributor's underlying implementation.

The workspace also gains an interactive bottom terminal, compact connection controls, consistent
appearance rows, stable setup language layout and an unobscured View menu.

## Implementation

- Removed the Skills sidebar/attachment action, modal and native import/remove/open-directory IPC.
  Existing scoped discovery, selection chips, draft ownership and prepared-input delivery remain.
  Detached menu actions verify their render epoch and owner before changing a draft.
- Added Plan/Goal/Loop/Compact alongside compact Skills and a small footer plus. The prompt is
  editable and requires the user's normal Send action. Skill documents use Markdown.
- Added xterm with a real node-pty shell in the selected project's canonical working directory.
  Tabs retain environment/cwd and output while hidden; closing terminates the shell. Input and
  output are bounded, output uses parser acknowledgements, and access is rechecked on writes.
  Fixed preload IPC admits only the owning main renderer. Reload, destruction and quit retire
  its processes. This human terminal does not take over agent-owned MCP process queues.
- Terminal supports native interactive programs, ANSI output, paste, scrollback, Ctrl+C, multiple
  tabs and mouse/keyboard resizing. Installed CLIs can be run normally; no Codex GUI automation
  is implied. A project must be selected before creating a terminal.
- Connection popover moves outside the translucent sidebar's containing block, narrows to 300px,
  removes extension-only switches and the settings action, and resets both disclosures whenever
  opened. Runtime diagnostics has its own nested disclosure. Header Connect remains until actual
  connected status; successful connection briefly highlights the footer indicator.
- View menu stacking now clears the sidebar. Appearance rows share minimum control/row heights.
  Setup heading uses a responsive grid consistently across languages, including Spanish.
- Updated product documentation, localization, tests and dependency notices. Preserved concurrent
  checkout changes, including removal of the standalone theme header button.

## Validation

The isolated Chromium UI acceptance passed with the current renderer and synthetic backend:
slash selection and prompt insertion, no removed Skills controls, connection disclosures reopening
collapsed, successful Connect state, popover/View hit testing, equal appearance rows and Spanish
heading layout. Existing Files/editor/PDF and draft-switching acceptance remains included.

A separate isolated Electron test used the production terminal IPC and real native PTYs. It passed
keyboard input, project cwd, persistent variables and `cd`, hidden output, two independent tabs,
Ctrl+C interrupt, resize, exit code 7 and refusal to write after closing. Its interrupt probe waits
for the returned shell prompt before sending another command, matching interactive shell behavior.

Initial suite runs identified outdated test fixtures for removed controls, terminal APIs, Electron
lifecycle and Web Animations; these were updated. Two timing/interleaving-sensitive shell tests
passed on focused rerun. Final suite/package/install results are recorded below when complete.

Screenshots and detailed machine-specific evidence remain under ignored outputs, outside the PR.

### Final source gate

`npm run verify` passed: 201 main-suite files, 4,883 tests passed and 44 skipped, followed by
2/2 shutdown tests. Privacy, dependency/native-source notices and TypeScript checks passed.
The final cleanup removed only unused modal/switch CSS; current layout verification is retained.

### Concurrent workspace changes

During packaging, the shared Files implementation and CSS advanced. The first installer was not
used. The latest Files/layout suites passed 72/72; packaging was restarted from a fresh input
snapshot so installation would include those current edits. Existing file-panel and extension
changes are retained as part of the explicitly requested current-tree snapshot.

### Installed Windows build

The rebuilt Windows x64 installer and packaged/native smoke checks passed. All 318 package input
hashes remained unchanged through the final build and installation. The installed 2.1.13 payload
matches all 287 package files, 131 compiled output files and 16 stable extension files. Installed
native-runtime smoke passed; the installed executable owns the loopback bridge listener.

Installed app.asar SHA-256: `3d67456a293cac8eb546ac1cbacfc743931effd170b0d15bfd11b2ed2e2bcf94`.
The current renderer acceptance was rerun after concurrent Files changes and passed. UI tests used
an isolated Chromium window; terminal acceptance used real native PTYs. No live provider chat or
Chrome extension reload was used as acceptance evidence.

The existing public-main snapshot PR #272 is updated with this current tree. Private local
history, machine-specific screenshots and forensic notes remain excluded.
