# Frontend first GPUI port plan

Status: proposed architecture and implementation sequence. Reviewed on 2026-09-30.

Replace the Electron workspace with a Rust/GPUI frontend while preserving the existing backend owners and Chrome extension. First prove that GPUI can deliver the app's text input, transcript, accessibility, and workspace behavior. Then connect it to the current Electron-hosted backend. Removing Electron and optionally rewriting backend modules are later, separate decisions.

This document combines official GPUI documentation with this repository's product contracts. Sourced framework facts are identified below; architecture and acceptance criteria are recommendations for this app. No GPUI build, performance comparison, or live integration has been completed.

## Official references and what they establish

The [GPUI website](https://gpui.rs/) describes a GPU-accelerated Rust framework with hybrid immediate and retained modes. Its documentation links lead to the GPUI crate in the Zed repository. The website also warns that GPUI remains tied to Zed for the near future. Its [examples page](https://gpui.rs/examples) is a discovery entry point; use the pinned source examples below when implementing.

The linked sources were fetched at Zed revision `66432e4ca957383dcc9ec61d1353a4b4bd94c6bc`. This is a research snapshot, not an approved dependency pin or a tested release. The crate manifest at that revision declares GPUI version 0.2.2; that declaration does not establish crates.io availability or compatibility with every linked document.

| Reference | Documented fact | Consequence for this port |
| --- | --- | --- |
| [README](https://github.com/zed-industries/zed/blob/66432e4ca957383dcc9ec61d1353a4b4bd94c6bc/crates/gpui/README.md) | GPUI is pre-1.0, frequently has breaking changes, and requires current stable Rust. Views are entities implementing `Render`; lower-level elements support custom layout and rendering. | Pin a tested dependency set and Rust toolchain. Begin with normal views and elements; introduce custom elements only for measured needs. |
| [Contexts](https://github.com/zed-industries/zed/blob/66432e4ca957383dcc9ec61d1353a4b4bd94c6bc/crates/gpui/docs/contexts.md) | `App` owns entity data; `Context<T>` adds entity services. Async contexts can outlive windows and updates become fallible. | Treat window/view disposal as normal. Revalidate selection and backend incarnation after every await. |
| [Ownership and data flow](https://github.com/zed-industries/zed/blob/66432e4ca957383dcc9ec61d1353a4b4bd94c6bc/crates/gpui/src/_ownership_and_data_flow.rs) | Entities can notify observers and emit typed events. Subscriptions can be retained and dropped to cancel observation. | Give each UI fact one entity owner. Scope subscriptions to their view or selected session rather than accumulating detached observers. |
| [Key dispatch](https://github.com/zed-industries/zed/blob/66432e4ca957383dcc9ec61d1353a4b4bd94c6bc/crates/gpui/docs/key_dispatch.md) | Typed actions and key contexts connect shortcuts to logical operations. | Route menus, buttons, and shortcuts through the same application commands, with composer, transcript, sidebar, and terminal contexts. |
| [Accessibility guide](https://github.com/zed-industries/zed/blob/66432e4ca957383dcc9ec61d1353a4b4bd94c6bc/crates/gpui/src/_accessibility.rs) | GPUI integrates AccessKit. Nodes need global identity and roles. IDs must be unique within a frame and stable between frames. Repeated `text!` calls from the same source location need distinct identity or distinct parent IDs. | Use session/message/input IDs for repeated rows. Add roles, labels, state, and accessible actions as components are built. Screen reader compatibility still needs native testing. |
| [Input example](https://github.com/zed-industries/zed/blob/66432e4ca957383dcc9ec61d1353a4b4bd94c6bc/crates/gpui/examples/input.rs) | Demonstrates focus, selection, clipboard actions, marked text, and input handlers. | Use it to understand platform text input. It is not evidence of a production-ready multiline composer or code editor. |
| [Variable height list example](https://github.com/zed-industries/zed/blob/66432e4ca957383dcc9ec61d1353a4b4bd94c6bc/crates/gpui/examples/list_example.rs) and [uniform list example](https://github.com/zed-industries/zed/blob/66432e4ca957383dcc9ec61d1353a4b4bd94c6bc/crates/gpui/examples/uniform_list.rs) | Examples expose `ListState`/`list` and range-based `uniform_list` rendering. | Evaluate variable-height lists for transcripts and uniform lists only for genuinely uniform rows. Do not copy whole-list measurement from a small demo into an unbounded transcript. |
| [GPUI manifest](https://github.com/zed-industries/zed/blob/66432e4ca957383dcc9ec61d1353a4b4bd94c6bc/crates/gpui/Cargo.toml), [platform manifest](https://github.com/zed-industries/zed/blob/66432e4ca957383dcc9ec61d1353a4b4bd94c6bc/crates/gpui_platform/Cargo.toml), and [Zed UI manifest](https://github.com/zed-industries/zed/blob/66432e4ca957383dcc9ec61d1353a4b4bd94c6bc/crates/ui/Cargo.toml) | GPUI and `gpui_platform` declare Apache-2.0; Zed's `ui` crate declares GPL-3.0-or-later. | Review each dependency and copied component separately. Do not assume Zed's editor, terminal, or UI crates have GPUI's license or standalone API. |

### Platform setup

The pinned README recommends `gpui_platform::application()` to select host windowing and text backends. On macOS it documents Metal rendering and the `font-kit` feature for glyph rasterization; without that feature the placeholder text system does not render glyphs. Linux/FreeBSD require `wayland`, `x11`, or both for desktop windows. Windows uses Win32 and DirectWrite and requires no platform features in the README's example. macOS development also requires the documented Xcode/Metal tooling.

Use that guidance to create a tested build matrix, not to claim shipped support. For this app, validate Linux Wayland and X11, Windows and macOS, and the existing x64/arm64 distribution targets. Check the chosen release's own documentation before selecting features. Avoid the README's wildcard dependency versions in production: commit Cargo.lock and pin the toolchain and mutually compatible crate versions or revisions.

## Scope and ownership

The frontend port covers the shell, setup, settings, projects/sidebar, composer, queue, transcript, workers, plans, usage, plugins, skills, project files, Git diffs, workspace terminals, and pet presentation. It preserves current functionality and identity contracts rather than introducing a new product design.

The following remain authoritative in TypeScript during the port:

- `session/store.ts`, `recorder.ts`, `correlation.ts`, and `read-model.ts`: durable history, attribution, and projections.
- `session/input.ts`, attachments, and `start-input.ts`: acceptance, claims, receipts, queue mutation, and delivery.
- `bridge.ts`, continuation, agents, and Goal owners: browser actions, compaction, worker families, and automation.
- Config, secrets, sandbox, projects, process managers, plugins, and MCP handlers: policy and execution.

The browser extension remains unchanged unless a concrete protocol requirement emerges. GPUI does not embed ChatGPT or take over browser pairing, account model discovery, or native send confirmation. Its tool views display recorded backend evidence.

```text
Rust GPUI workspace
  presentation entities, drafts, focus, selection, scrolling
                 |
     private versioned application transport
                 |
Existing TypeScript application operations
  initially hosted by Electron main, later by standalone Node
                 |
Existing durable owners, MCP surfaces, browser bridge
                 |
Existing Chrome extension and ChatGPT
```

## Frontend integration before Electron removal

First extract transport-independent, validated application operations from `src/main/ipc.ts`, `plugins-ipc.ts`, and `workspace-terminal-ipc.ts`. Electron IPC and the new native transport should be adapters around those same operations. Keep validation, effective permission checks, and durable publication at the existing backend owners. Do not forward arbitrary channel names from the native client.

Initially let Electron main host those operations and retain platform dependencies such as `safeStorage`, dialogs, and native helpers. A dedicated development launch mode starts GPUI and the backend together. Elect one interactive workspace per backend; both frontends may exist for comparison, but must not independently write the same userData store. Native dialogs must have a deliberate owner and correct window parenting or a documented prototype limitation.

The first integration should use private inherited pipes, with bounded length-prefixed frames, an explicit handshake, and a fixed operation registry. Electron's ability to launch and supervise this connection must be proven in Milestone 1. If the process arrangement requires sockets, use OS-local access controls and explicit authentication rather than exposing another unauthenticated loopback service.

The optional control API is not the full frontend protocol. Its current read projections and send/cancel actions do not cover settings, files, terminals, queue editing, and other workspace operations. Reuse its underlying read-model functions where useful; preserve its separate opt-in contract.

### Application protocol requirements

Define wire schemas independently of Electron and GPUI and generate or validate compatible Rust and TypeScript representations. The existing preload allowlist is the inventory, not the finished protocol: it currently imports some types from `main`.

- Every envelope identifies protocol version, backend incarnation, request/subscription ID, and operation. Session-bound operations name the durable local session and any exact turn/input identity required by the existing owner.
- Carry selection/load generation in client request context; reject stale UI updates even when the selected ID matches again after A → B → A.
- Preserve session chronology versus publication sequence. The existing `position`/origin and `seq`/`nextFrom` concepts must not collapse into one cursor.
- Start subscriptions with a snapshot and a defined update boundary. Detect gaps and reread from the owner; transport sequence is not a new durable ledger.
- Bound frames, queued updates, decoded images, text, and caches. Terminal data needs explicit flow control consistent with existing acknowledgement behavior. Large assets need a bounded transfer design rather than unlimited JSON base64.
- Distinguish admitted, delivered, unconfirmed, and rejected input. A transport acknowledgement proves neither browser insertion nor ChatGPT acceptance.
- Reuse stable outbox input IDs when reconciling an uncertain acceptance. Do not invent replay semantics for other mutations; expose readback/reconciliation or backend idempotency before permitting retries.
- Cancel obsolete reads and subscriptions. Cancellation of a client task must not silently cancel accepted durable work.
- Keep secrets out of ordinary projections and logs. Secret setters are explicit sensitive operations; secret reads remain unavailable to the frontend.

UI disposal, transport disconnect, backend restart, and app quit are separate events. On reconnect, disable mutations until handshake and fresh snapshots complete. If the backend is lost, retire its live controls and never resend uncertain work automatically. Full app quit still invokes the existing bounded teardown; a GPUI window crash must not independently decide task completion or cancellation.

## GPUI implementation practices

### Entity boundaries and rendering

Create focused entities for workspace selection, session catalog, selected transcript, composer draft, queue projection, settings draft, worker drawer, and each active dock. These names are proposed responsibilities, not a requirement to create a crate per feature. Keep the initial workspace small: a native executable, a wire-contract module/crate, and a test fixture transport are enough.

Entities own presentation state; backend snapshots own business facts. Use typed events for meaningful UI changes and `notify` only after changes that affect observers or rendering. Retain subscriptions and async tasks at a named lifecycle owner and dispose them when that owner changes. Use weak entity references where appropriate so background work does not keep a closed panel alive.

Keep `Render` free of network calls, durable mutation, filesystem I/O, expensive parsing, and task spawning. Parse Markdown, decode images, and prepare large diffs outside the render path, then publish results through the correct context after rechecking ownership. Do not hold mutable UI access across awaits. Use GPUI's executors deliberately; a separate async runtime, if needed by transport libraries, needs an explicit bridge and shutdown owner.

Translate the current semantic appearance settings into Rust tokens for color, type, spacing, and motion. Reuse the product's Phosphor icon vocabulary with licensed native-compatible assets. GPUI's Tailwind-style builders are layout APIs, not a CSS/DOM compatibility layer. Preserve localization, text scaling, contrast, and reduced motion from the start.

### Transcript identity and scrolling

Build a row projection from canonical message/tool/input identities, not list indices. Preserve exact tool rows, revisions, origin order, disclosure state, image status, pending-input reconciliation, and unread completion receipts. Selecting another session synchronously retires the prior controls; retained painted rows are inert while the destination loads. A failed load clears retained content, and only explicit New Chat shows the welcome view.

Use viewport-based rendering with bounded overscan and cache size. Prototype variable-height measurement, Markdown tables, code blocks, images arriving late, resize, folding, history prepend, and live tail updates. Preserve a stable row anchor plus local offset; follow the tail only while the user is already following it. Virtualization must not break cross-row copy/selection or accessibility; keep logical selection independent of mounted elements or choose another strategy if this cannot be proven.

### Composer and keyboard input

Choose a text component only after testing multiline editing, undo/redo, grapheme navigation, marked text/IME, selection, paste, drag/drop, keyboard layouts, and accessibility. Test Japanese/Chinese composition, accented text, and emoji. Enter during composition must not send. Preserve the current send/newline policy and draft ownership across sessions, projects, and unfiled New Chat.

Use typed actions and scoped key contexts for Send, Stop, End turn, queue editing, sidebar movement, and dock commands. Mouse and keyboard invoke the same validated operation. Focus must survive catalog/status repaints and must not move into a worker drawer or unrelated background completion.

### Accessibility and motion

Assign stable global IDs, roles, labels, values, disabled/expanded state, and accessible actions to interactive components. Avoid source-location-only text IDs for repeated transcript content. Test focus traversal, accessible activation, and screen reader reading order on real platforms; AccessKit integration alone is not acceptance evidence. Suppress redundant announcements during streaming and avoid permanent animation clocks for idle or hidden UI.

## Complete frontend coverage

This inventory covers the current `src/renderer` tree, both `src/preload` entry points, static controls in `index.html`, dynamic controls in renderer modules, and native shell integration. It is the required scope for production parity. A row names behaviors to preserve, not a claim that they already work in GPUI. Where implementation conflicts with AGENTS contracts, preserve the intended invariant and document the discrepancy.

Milestones below use M0 for feasibility, M1 for read-only integration, M2 for task interaction, M3 for complete frontend parity, and M4 for Electron retirement. Features developed in stages remain open until their complete acceptance criteria pass. Electron-hosted dialogs or overlays can support a prototype, but do not count as completed native frontend parity.

| Area and current implementation | Required GPUI coverage | Stage and acceptance evidence |
| --- | --- | --- |
| Shell and screen navigation — `main.ts`, `index.html`, `styles.css`, `settings.css` | Chat, workspace/settings, automation settings, plugins, skills, pets, usage, and log views; sidebar/header navigation, back-to-chat, welcome state, refresh, view menus, toast/status feedback, version/footer | M0/M3: enumerate every reachable view, navigate by pointer and keyboard, preserve selected task and focus |
| Shared UI infrastructure — `dom.ts` | Semantic icon mapping, localized element/attribute bindings, fixed API error handling, toast feedback, reusable controls and safe native equivalents for DOM helpers | M0/M3: all consumers use consistent icons, errors and localization; retire DOM plumbing only after behavior is replaced |
| Appearance — `appearance.ts` | Light/dark theme, accent/background/sidebar colors, hex inputs, contrast, translucency, font and text size, reset, immediate semantic updates; window zoom in/out/reset and native backing/titlebar projection | M0/M3/M4: saved settings, repeated edits, scale extremes, supported fonts and platform rendering |
| Localization — `i18n.ts`, `locales/*`, `flags/*` | English source labels and German, Spanish, French, Japanese, Korean, Brazilian Portuguese, European Portuguese, Turkish, Simplified Chinese and Traditional Chinese; language switch, interpolated text, locale-sensitive dates/numbers, automatic text direction, long-label layout | M3: every surface and dynamic dialog changes language; no untranslated new native controls |
| Setup guide — `setup-guide.ts`, `setup-images/*`, `tool-approval.ts` | Six-step guide, reviewed screenshots, enlargement and written callouts, optional Desktop disclosure, required-field/key-presence cues, folder approval, tunnel/API key entry, connect, extension folder/download/unpair, tool-approval notice and acknowledgement | M3: first-run and existing-config paths, cancelled dialogs, failed connect, dismissed notice persistence |
| Connection — `connection-popover.ts`, `main.ts` | Header/sidebar status, connect/disconnect, separate Core/Desktop/Plugins cards, tunnel and pairing facts, advanced/runtime details, copy and refresh, missing-step guidance and stale/error states | M1/M3: independent surface/pairing/model states remain truthful; popover fits viewport and keeps focus |
| Profiles and tunnel settings — `main.ts` | Add/select/remove profile dialog, last-profile restriction, long names, profile-specific key presence/set/remove, tunnel kind/IDs, binary selection/path | M3: profile changes during pending saves preserve exact backend profile/epoch and credentials |
| Roots and capabilities — `main.ts`, generated permission groups | Add/drop/rename/remove approved roots, distinct project association, grouped tri-state capability toggles and tool names, read-only mode, command policy enable/mode/rule editing, Desktop consent/status links and platform masking | M3: revoke while work exists; validation failures and unsupported capabilities; no widening of permission |
| General and privacy settings — `main.ts`, `image-storage.ts` | Start at login, auto-connect, minimize-to-tray, screenshot/privacy preferences, developer/playful status, recording/retention controls, image storage information and cleanup modes, control API enabled/actions switches | M3/M4: exact saved On/Off, merge behavior, cleanup effects and error views |
| Automation settings — `chat.ts`, `goal-reasoning.ts`, `main.ts` | Automatic Continue; Goal/Loop backend choices including available offline Goal mode; helper and worker model/reasoning; tool details in handoff; workers/attribution/recovery/wait settings; plan backend; finish setting/lead notice; auto-compaction enable/threshold | M3: availability, disabled states and current config consumers agree; independent reasoning choices preserved |
| API provider and prompts — `chat.ts`, `goal-reasoning.ts` | Provider selection, custom base URL/model/key, OpenRouter key, stored-key removal/status, paged API model picker, API reasoning; handoff/Goal/objective/Loop prompt editors and default restoration | M3: keyless provider, failed model load, stale edit, cancellation, settings search and focus |
| Browser preferences — `browser-preferences.ts` | Browser choice, bridge Auto/fixed port with environment override state, background chats, browser-only mode, automatic plugin refresh, overwrite tool rows/duration preferences, refresh and unavailable-extension status | M3: app/extension changes reconcile through backend without granting new browser-opening authority |
| Sidebar and projects — `chat.ts`, `sidebar-order.ts`, `sidebar-completion.ts` | Add/remove grouping, project New Chat and unfiled New Chat, paged sessions/Show more, expansion, parent/worker nesting, project and chat reordering, activity/completion markers, local unread receipts, open provider chat, delete and block/unblock actions | M1/M2/M3: ordering never changes ownership; no stale selection or focus loss; unread acknowledged only after successful live-tail render |
| Sidebar geometry — `sidebar-resize.ts` | Collapse/show, pointer and keyboard resize, bounds, saved width/collapse and responsive layout | M0/M3: narrow/wide windows, zoom, restart and interrupted drag |
| Composer — `chat.ts`, `composer-motion.ts`, `chat-models.ts` | Multiline text/drafts, model and effort pickers, observed availability and refresh, Normal/Goal/Loop selection, continuation timing, objective edit/save, send/inject/after-turn choices, Stop, End turn and status/disabled states | M0/M2: IME/undo/paste/focus, exact draft/session ownership, no send inferred from UI insertion |
| Attachments and skills in composer — `chat.ts`, `skills.ts` | Choose/drop/paste files and images, preview/remove, native versus in-memory staging, text-to-file attachment, share folder, project-file attach, skill autocomplete/picker, selected chips, scope-specific library and Add Skills entry | M2/M3: attachment order/limits/errors, lost-preview status, draft switch during staging, actual native browser upload |
| Input queue — `chat.ts` | Accepted pending bubbles, after-turn/finish entries, edit/reorder/cancel, automation changes, due/delivery/error status, dismissed notices and owner-approved browser retry | M2: claim race, unconfirmed delivery, immutable claimed payload and canonical history reconciliation |
| Generated workflows and task progress — `chat.ts` | Plan generation/loading/live preview/errors/cancel, editable stages and sending state, generated Goal opening, exact task request progress and Generate Goal near finish | M2/M3: cancellation/late progress cannot replace newer draft; checkpoints remain outbox-owned |
| Displayed agent plan — `agent-plan.ts` | Request-scoped progress steps, status, disclosure/collapse, changes and empty state | M1/M3: updates display progress without consuming queue or executing a workflow |
| Automation and recovery — `recovery.ts`, `chat-error.ts`, `chat.ts` | Active objective, Goal/Loop progress/wait/live text, finish hold, recovery countdowns and errors, paused helper list/retry, running-tool activity, exact stop/cancel states | M2/M3: use backend deadlines/facts, retire stale controls, no invented completion or recovery action |
| Context and handoff — `context-meter.ts`, `chat.ts` | Estimate meter, percentage/token display toggle, context limit/threshold, dialog, Compact & Resume/cancel/progress/failure, handoff history/brief display and copy | M2/M3: preserve local session across A/B chats; estimates visibly distinct from provider billing |
| Transcript — `chat.ts`, `timeline-scroll.ts` | User/assistant/native tool/agent/turn/error/handoff rows, chronology and revisions, pagination/live-tail/jump behavior, retained inert rows during selection, working/finished boundaries and durations | M0/M1/M3: variable heights, history prepend, resize, streaming, A → B → A and failed destination load |
| Rich messages and tools — `chat.ts`, `tool-result.ts`, `sanitize-html.ts`, `local-url.ts` | Markdown/code/tables, captured message fallback, references/citations and safe links, code/text copy, recorded reactions, native and local images, truncation/missing assets, raw args/results/facts, exact tool row folding/expansion | M1/M3: representative render fixtures, cross-row selection, safe URL handling, negative tool outcomes break folds |
| Edit review and exports — `chat.ts`, `file-panel.ts` | Tool change summaries and exact-call edit review assets, unavailable/too-large review explanations, answer/session Markdown copy or save, handoff copy and cancelled save feedback | M3: review uses recorded edit rather than current working-tree diff; export scope/turn identity and clipboard failure |
| Worker drawer and communication — `agent-panel.ts`, `agent-communication.ts`, `chat.ts` | Worker cards/model/task/state/context/inbox facts, read-only worker transcript and recorded communication, independent prime families, clear worker/prime and clear swarm results | M1/M3: drawer never switches prime composer; exact run identity and sleeping/revivable states retained |
| Workspace docks — `workspace-docks.ts`, `work-panel-resize.ts`, `tab-reorder.ts`, `panel-motion.ts` | Right work dock and bottom terminal dock, tool/tab launch menus, activate/close/expand/restore, pointer and keyboard tab ordering, divider resize, saved geometry, interruptible motion | M0/M3: fast close/reopen, resize without losing editor/terminal state, narrow layout and reduced motion |
| Project file browser — `file-panel.ts` | Scoped tree/list, directory navigation/watch refresh, create file/folder, rename/delete confirmations, reveal, attach, loading/empty/denied/unsupported states, preview height | M3: project switch, cancelled dialog, revocation, stale watcher and missing/renamed file |
| File preview and editing — `file-panel.ts`, `file-code-editor.ts`, `file-pdf-viewer.ts` | Text/code highlighting/edit/search, Markdown and image previews, PDF page/zoom controls, bounded unsupported/binary/large previews, dirty drafts, save/reload/conflict flow | M3: revision conflict, no overwrite of focused draft, decoding cancellation and bounded memory |
| Git views — `file-panel.ts`, `file-code-editor.ts` | Snapshot/status, base-ref comparison, changed-file list and inline/merge diff presentation, revision-aware refresh, recorded edit-review mode | M3: no implicit Git mutation; changed base or project invalidates old diff without destroying unrelated draft |
| Workspace terminal — `workspace-terminal.ts`, `workspace-docks.ts` | Project/cwd-owned creation, multiple tabs, input/output, resize/fit, copy/paste/selection, close and exit/error indication, acknowledgements and flow control | M3: interactive shells, ANSI/Unicode, flood output, exit while hidden and no cross-owner writes |
| Plugins — `plugins.ts`, `plugin-icons/*`, `plugin-refresh-reminder.ts` | Search/catalog/recipes, custom local/remote servers, bundle import, install/configure/restart/update/uninstall dialogs, credentials, enable plugin/tool, tool schemas/details, OAuth authenticate/cancel, connector setup/link/refresh, legal notices and schema-refresh reminder | M3: every source type and failed/cancelled mutation, no plaintext credential echo, local schema change not presented as ChatGPT refresh proof |
| Skill management — `skills-library.ts` | Search/list managed/recommended skills, install recommended, folder/file/GitHub import dialog, link/check/update repository source, remove and refresh, warnings and scopes | M3: duplicate/invalid import, cancellation, failed check/update and composer library invalidation |
| Usage — `usage.ts` | Message totals/week-start selector, model/shared/feature quota and reset/staleness views, estimated tokens/conversations/days, charts/comparison cost, editable model rates/divisor/multiplier, tooltips and refresh states | M3: saved formula/week start, unknown rate, zero/empty/error data; estimates never become billed-cost claims |
| Diagnostics and logs — `main.ts` | Run checks/result disclosure/close, companion diagnostics, runtime facts, log feed/severity/agent filters/problems, live append and scroll behavior, copy text/JSON, operational errors | M3: redact through existing backend, bounded feed, copy failure and active filters during pushes |
| Updates and notices — `main.ts`, `tool-approval.ts`, `plugin-refresh-reminder.ts` | Available/download/staged/install/error/version states, extension mismatch/update/download guidance, dismissed tool approval and connector reminder | M3/M4: display owner-verified state; install/download buttons cannot manufacture success |
| Pet library — `pets.ts` | Search/favorites, import/enable/favorite/delete, preview, format guide/dialog, copy instructions, library refresh and overlay visibility | M3: malformed assets, cancelled import/delete, disabled pet and bounded preview decoding |
| Pet animation — `pet.ts`, `pet-machine.ts`, `pet-choreography.ts`, `pet-assets/*` | Existing companion migration, drag/menu/gesture, sprite timing and props, autonomous activity, reduced motion, hidden/idle scheduling and cleanup | M3: identical behavioral fixtures, idle wakes and interaction ownership; no independent task authority |
| Separate pet overlay — `pet-overlay.ts`, `pet-overlay.html`, `pet-overlay.css`, `preload/pet-overlay.ts` | Transparent overlay surface, per-pet position, hit regions/click-through, pointer/bounds snapshots, hide, focus/release owner, open library/exact session activity, appearance/library updates | M3/M4: multi-monitor/scaling and native input/focus behavior; port both preload surfaces |
| Native shell integration — `main/index.ts`, window lifecycle/layout, edit context menu, pet-overlay and update owners | Single instance, activation/tray/Dock, window close/minimize/fullscreen, geometry, native edit menus/dialogs, clipboard, URLs/reveal, OS consent, notifications, quit/update handoff | M3 presentation/M4 host: all supported platforms, no delayed window resurrection or orphan backend |

### Assets and presentation state

Port `index.html` and the separate `pet-overlay.html` as native view trees. Account for both main CSS files, overlay CSS, icon CSS/font assets, setup screenshots, locale/flag resources, plugin icons, pet sprites and animation metadata, and `assets.d.ts` bundler declarations. Build metadata may be retired when replaced; visual assets must be copied or deliberately regenerated with their licenses and privacy review preserved.

Inventory saved state separately from backend config: language (`cos.ui.language`), sidebar order and completion receipts, sidebar width/collapse, work-panel width, bottom-panel height, file-preview height, usage formula/week start, dismissed input notices, tool-approval acknowledgement, connector-schema reminder acknowledgements, and per-pet overlay positions. The old `cos.ui.turTurPet.v1` companion preference has a migration path in current source; preserve that behavior rather than assuming it remains the active native storage format. Also inventory in-memory composer/project drafts, disclosures, selected tabs, scroll anchors and editor selections; persistence beyond current behavior is a separate product decision.

For each preference, record its source key/schema, lifetime, native owner, migration rule and corrupt/missing-state handling. Migrate presentation state without copying it into permission or delivery ledgers. Native UI parity includes transient state continuity during ordinary refresh, not just restart persistence.

### Preload operation and event inventory

Both allowlists below are the current frontend contract inventory. Every entry must map to a native application operation/event, a narrow platform adapter, or a documented replacement with equivalent behavior. Renaming or combining transport methods is allowed; losing the capability is not. Electron-specific `File`/DOM argument types need native equivalents and attachment-boundary validation.

#### Main workspace

Source: `src/preload/index.ts`. 123 operations and 14 subscriptions.

**Operations**

- `terminalCreate`, `terminalWrite`, `terminalResize`, `terminalAck`, `terminalClose`, `openLegalNotices`, `pluginsSnapshot`, `pluginsInstall`, `pluginsConfigure`, `pluginsRestart`.
- `pluginsAuthenticate`, `pluginsCancelAuthentication`, `pluginsUpdate`, `pluginsUninstall`, `pluginsSetEnabled`, `pluginsSetToolEnabled`, `pluginsImportBundle`, `chooseFiles`, `petsList`, `petsOverlayState`.
- `petsSetOverlayVisible`, `petsImport`, `petsSetEnabled`, `petsSetFavorite`, `petsDelete`, `petsAsset`, `listSkills`, `listManagedSkills`, `listRecommendedSkills`, `installRecommendedSkill`.
- `skillsImport`, `skillsImportGithub`, `skillsLinkGithub`, `skillsCheckGithub`, `skillsUpdateGithub`, `skillsRemove`, `skillLibrary`, `dropFiles`, `attachText`, `getUsage`.
- `getState`, `saveSettings`, `addRoot`, `addRootPath`, `removeRoot`, `renameRoot`, `setApiKey`, `addSetupProfile`, `selectSetupProfile`, `removeSetupProfile`.
- `setGoalKey`, `setCustomProviderKey`, `listGoalModels`, `pickBinary`, `connect`, `disconnect`, `runDiagnostics`, `requestDesktopAccessibility`, `getLog`, `getLogText`.
- `getLogJson`, `writeClipboard`, `exportMarkdown`, `openLink`, `installUpdate`, `downloadUpdate`, `listSessions`, `listProjects`, `addProject`, `removeProject`.
- `listProjectFiles`, `watchProjectFiles`, `previewProjectFile`, `createProjectFileEntry`, `renameProjectFileEntry`, `saveProjectFile`, `deleteProjectFileEntry`, `revealProjectFileEntry`, `attachProjectFile`, `getProjectGitSnapshot`.
- `getProjectGitDiff`, `getToolEditReview`, `getSessionImage`, `getImageStorage`, `clearImageStorage`, `stopSessionTurn`, `releaseSessionFinish`, `generateFinishGoal`, `getChatModels`, `browserPreferences`.
- `companionDiagnostics`, `requestChatModels`, `getSessionControls`, `setSessionAutomation`, `setSessionObjective`, `compactSession`, `cancelSessionCompaction`, `draftTaskPlan`, `sendInput`, `retryInputBrowser`.
- `listInputs`, `listPausedHelpers`, `runningTools`, `retryHelper`, `editQueuedInput`, `reorderQueuedInputs`, `cancelInput`, `setInputAutomation`, `setZoom`, `getZoom`.
- `openSessionChat`, `setSessionBlocked`, `deleteSession`, `getHandoff`, `unpairExtension`, `downloadExtension`, `extensionPath`, `openExtensionFolder`, `getSwarm`, `resetSwarm`.
- `clearAgent`, `cancelTaskRequest`, `draftGoalOpening`.

**Subscriptions**

- `onTerminalEvent`, `onPluginsChanged`, `onPetOverlayStateChanged`, `onPetOverlayOpenOwner`, `onProjectFilesChanged`, `onProjectGitChanged`, `onToolApprovalNotice`, `onChatModelsChanged`, `onStateChanged`, `onLogEntry`.
- `onSessionChanged`, `onWriteSession`, `onTaskProgress`, `onSwarmChanged`.

#### Separate pet overlay

Source: `src/preload/pet-overlay.ts`. 8 operations and 4 subscriptions.

**Operations**

- `listPets`, `petAsset`, `hidePet`, `setInteractive`, `focusOwner`, `releaseFocus`, `openLibrary`, `openActivity`.

**Subscriptions**

- `onSnapshot`, `onLibraryChanged`, `onPointer`, `onBounds`.


### Coverage maintenance and completion gate

During implementation maintain a row-level ledger with frontend owner, backend operation, GPUI component, milestone, implementation status, test/fixture, native evidence and outstanding gaps. Initial status for every area is planned; none is implemented by this document. Create subrows for independent actions and dialogs when assigning work. A group cannot pass while a child action is missing.

Re-enumerate renderer modules/assets, both preload objects, `index.html` static controls, dynamically generated controls, native menu/window entry points, and UI preference keys when the source changes. Keep an explicit disposition for every file: port logic, reuse assets, replace framework plumbing, or retain unchanged outside GPUI. Map existing `scripts/verify-*.cjs` UI checks and renderer test families to the owning row; retaining backend tests does not cover these surfaces.

At M3, require zero unmapped frontend modules, operations, subscriptions, screens, dialogs or state owners, plus evidence for all rows and their child behaviors. At M4, require zero retained Electron frontend/platform dependencies without an explicit disposition. Internal prototypes may defer features visibly; deferral never counts as parity or silently narrows the production port.

The extension's popup, injected page overlay and browser-control scripts remain browser frontends, retained unchanged outside the GPUI rewrite. Validate pairing, browser preferences, model observations, connector reminders and native delivery against them at the integration gates. Do not omit those touchpoints merely because the extension UI is not being rewritten.

## Components requiring explicit choices

| Existing frontend dependency | GPUI port work | Decision gate |
| --- | --- | --- |
| `marked` plus HTML sanitization | Native Markdown AST rendering, safe links, selectable text, tables, code, images | Representative transcript fidelity, bounded parsing, copy behavior, safe link handling |
| CodeMirror and merge view | Native text editor, highlighting, diff layout, search and revision-conflict UI | Choose maintained components or a deliberately limited first editor; do not assume GPUI supplies an editor |
| xterm.js and addon-fit | Terminal emulation plus native rendering, selection, input, resize and flow control | Interactive shell, Unicode, ANSI behavior, resize, high output volume, reconnect and exact terminal custody |
| PDF.js | Native bounded PDF rendering and page controls | Selected-page rendering, zoom, cancellation, pixel/byte limits, engine license and packaging |
| DOM motion and CSS | Native layout and interruption-safe animation | Dock resize, fast open/close, scaling, reduced motion and idle CPU |
| localStorage preferences | Versioned native UI preference store and migration/export path | Drafts, order, sizes, disclosure, notices, and read receipts survive the chosen cutover |
| Electron pet overlay | Native sprite view and later native overlay/window behavior | Hit testing, multi-monitor placement, scaling, focus, hidden/idle wake behavior |

For component selection, assess maintenance, compatible pinned GPUI version, license, dependency footprint, accessibility, and platform evidence. Reading Zed code is useful for patterns; importing its higher-level crates is a separate architectural and licensing decision. No third-party component library is selected by this plan.

## Implementation milestones and acceptance gates

### Milestone 0 Framework feasibility

Build a separate GPUI prototype using synthetic fixtures only. Include a variable-height transcript and multiline composer, accessible sidebar controls, resizable docks, theme/text scaling, and file drop. Exercise the intended OS families early. Record exact Rust/GPUI pins, build dependencies, GPU/display environment, and results.

Proposed workload: 10,000 logical mixed transcript rows with a bounded loaded window, long Markdown/code blocks, image completion during scrolling, and controlled streaming updates. Measure input responsiveness, frame latency, memory, and idle wakes against an equivalent Electron fixture on the same hardware. Agree numerical budgets from that baseline rather than claiming GPU rendering guarantees improvement.

Exit only when input/IME, text selection, virtualized history anchoring, accessibility, and basic platform setup are demonstrated. A failure should produce a small reproduction and a component or framework decision before application integration grows.

### Milestone 1 Read only workspace

Extract the shared application boundary and private transport. Implement project/session listing, paged transcript, live invalidation, connection status, and the read-only worker drawer using current backend projections. Keep existing business owners untouched.

Exit with contract fixtures passing in Rust and TypeScript, A → B → A requests rejected when stale, subscription gaps recovered, bounded payloads verified, and backend disconnect visibly disabling controls. No mutation methods are exposed yet.

### Milestone 2 Complete task vertical slice

Add composer drafts, observed models/reasoning, immutable attachment staging, outbox send, queue edit/reorder/cancel, and exact-session Stop/End turn/Block. Then expose Goal/Loop, generated checkpoints, and Compact & Resume through existing operations.

Exit with real browser evidence for send and steering, accepted input merging into history exactly once, claimed queue entries remaining immutable, no blind retry after lost acknowledgements, and compaction retaining local session/project/queue identity. Test UI exit and backend restart separately.

### Milestone 3 Workspace parity

Port setup, settings and profiles, plugins/OAuth presentation, skills, usage, plans, files/Git, terminals, pets, exports, and presentation preferences. Preserve settings three-way merge, revision-checked file saves, agent family identity, permission/error views, and all localized labels. A feature may remain visibly unavailable in an internal prototype, but a production replacement must close the parity checklist or have an explicit user-approved scope change.

Exit only when the complete frontend coverage matrix and both preload inventories have no unmapped or unimplemented behaviors, with feature-by-feature evidence and visual/keyboard checks at representative sizes and scales. Preserve history and business facts even when a preview or component fails.

### Milestone 4 Electron retirement

After frontend parity, move the same TypeScript owners to a standalone Node host. Replace remaining Electron services through narrow platform adapters: lifecycle/single-instance lock, paths/resources, secrets, clipboard, dialogs, shell/URLs, notifications/tray, appearance, pet windows, and updates. Rust may supply OS adapters, but each adapter must have explicit permission and process ownership rather than a generic privileged RPC.

Plan credential migration separately. A new OS keyring library cannot be assumed to decrypt Electron's `secrets.bin`; use the old decryptor for a bounded migration, verify the committed replacement before retiring old data, and cover plugin OAuth stores. Preserve Linux rejection of insecure credential fallback. Never export plaintext credentials as migration files.

Package a pinned Node runtime and rebuild/verify native modules such as node-pty, Sharp, tree-sitter, Koffi, and the macOS helper addon against its actual ABI. Preserve extension mirroring, tunnel/rg payloads, native consent identity, notices, updater checksums, and bounded shutdown. Source builds are not installer, consent-continuity, or live-device evidence.

Exit with packaged smoke tests and existing-data migration checks across supported targets. Remove Electron/preload/DOM implementation and obsolete adapters only after this gate. A Rust backend rewrite remains outside this plan and needs its own justification.

## Validation and review evidence

Keep existing TypeScript owner tests. Add shared wire fixtures and malformed/oversized-message cases at both protocol ends. Use GPUI's documented `#[gpui::test]` and `TestAppContext` facilities for UI state, actions, ownership and input simulation, after verifying the APIs against the selected pin. Native platform checks complement simulated tests.

Critical scenarios include stale selection/draft results; pending bubbles resolving into canonical history; history eviction not resurrecting inputs; disconnect after acceptance; backend incarnation change; worker drawer preserving prime focus; queue edits racing a claim; compaction during a queued send; file revision conflicts; terminal backpressure; and secrets excluded from ordinary snapshots/logs.

Adapt current Electron UI checks into reusable behavioral fixtures and GPUI-native interaction tests rather than treating jsdom or Electron screenshots as proof of native behavior. Run the nearest backend suites and repository-required checks when production operations change; this planning document itself requires only documentation review.

Measure total frontend plus backend memory/CPU, cold and warm startup, streaming and scrolling latency, attachment/PDF decoding, and idle behavior. Maintain distinct evidence for source review, tests, build, package, installed payload, and live browser/device behavior. Each milestone report records its actual checks and remaining gaps.

## First implementation assignment

Create the isolated Milestone 0 prototype and a short feasibility report. Its allowed scope is the new native prototype, synthetic fixtures, and relevant build documentation. It does not mutate production userData, change MCP/extension protocols, or extract business owners yet.

Deliver a reproducible launch command, tested dependency pins, platform results, composer and transcript demonstrations, and measured comparison data. Resolve the text component and variable-height selection strategy before scheduling the production vertical slice. This is the smallest useful next step toward the frontend port.

## Repository references and review limits

Relevant source entry points are [AGENTS.md](../../../AGENTS.md), [preload API](../../../src/preload/index.ts), [IPC handlers](../../../src/main/ipc.ts), [session read model](../../../src/main/session/read-model.ts), [chat frontend](../../../src/renderer/chat.ts), [code editor](../../../src/renderer/file-code-editor.ts), [PDF viewer](../../../src/renderer/file-pdf-viewer.ts), [terminal wire types](../../../src/shared/workspace-terminal.ts), [secrets](../../../src/main/secrets.ts), and [package declarations](../../../package.json).

The current package declares 2.1.21; the AGENTS source-alignment baseline names 2.1.18. Use current source for implementation details and the contracts for intended behavior. The coverage review enumerated the renderer/assets tree, both preload APIs, static HTML controls, dynamic renderer entry points, preference storage and UI check inventory. This establishes planning coverage, not line-by-line correctness of every handler or live behavior. Component libraries, a GPUI build and live platform support remain unverified.
