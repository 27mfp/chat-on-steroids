# Ordered implementation task cards

Read [the execution guide](execution-guide.md) before choosing a card. Every card below starts
as **planned**; historical prototype checks do not close new tasks. Allowed paths are relative
to `rust-port/` unless they begin `src/`, `test/` or name a main/renderer owner. The common
procedure, bounds/disposal audit, documentation verifier and handoff template apply to every
card. New production adapters must stay within the named owner; record concrete files in the
assignment before editing. Split broad M3/M4 cards into independently reviewable child cards
and ledger subrows; a card is a work package, not a demand for one enormous commit.

## Dependency index

| Task | Milestone | Work | Requires |
| --- | --- | --- | --- |
| [R00](#r00) | M0 | Baseline and dependency report | none |
| [R01](#r01) | M0 | Synthetic tail append | R00 |
| [R02](#r02) | M0 | Painted viewport anchoring | R01 |
| [R03](#r03) | M0 | Reflow and bounded transcript fixture | R02 |
| [R04](#r04) | M0 | Native multiline composer | R00 |
| [R05](#r05) | M0 | Transcript selection decision | R02,R04 |
| [R06](#r06) | M0 | Shell, focus and accessibility | R03,R04 |
| [R07](#r07) | M0 | Platform and performance matrix | R03,R05,R06 |
| [R08](#r08) | M0 | Feasibility gate report | R01–R07 |
| [R10](#r10) | M1 | Freeze minimal wire contract | R08 |
| [R11](#r11) | M1 | Private transport and lifecycle | R10 |
| [R12](#r12) | M1 | Catalog and session selection | R11 |
| [R13](#r13) | M1 | Canonical history and worker read view | R12 |
| [R14](#r14) | M1 | Read-only integration gate | R12,R13 |
| [R15](#r15) | M2 | Drafts, observed models and native staging | R14 |
| [R16](#r16) | M2 | Send and receipt reconciliation | R15 |
| [R17](#r17) | M2 | Queue steering and distinct controls | R16 |
| [R18](#r18) | M2 | Goal, Loop, workflow and worker interaction | R17 |
| [R19](#r19) | M2 | Compact and Resume continuity | R17,R18 |
| [R20](#r20) | M2 | Task interaction gate | R16–R19 |
| [R21](#r21) | M3 | Theme, localization and UI preferences | R20 |
| [R22](#r22) | M3 | Setup, security and settings | R21 |
| [R23](#r23) | M3 | Rich transcript and review details | R21 |
| [R24](#r24) | M3 | Docks, files and revision-safe editor | R21,R22 |
| [R25](#r25) | M3 | Git and recorded edit review | R24 |
| [R26](#r26) | M3 | Bounded image and PDF preview | R24 |
| [R27](#r27) | M3 | PTY terminal parity | R24 |
| [R28](#r28) | M3 | Plugins, OAuth and skills | R22 |
| [R29](#r29) | M3 | Usage, diagnostics, updates and pets | R21,R22,R23 |
| [R30](#r30) | M3 | Full frontend parity audit | R21–R29 |
| [R31](#r31) | M4 | Standalone host adapter design | R30 |
| [R32](#r32) | M4 | Credential migration | R31 |
| [R33](#r33) | M4 | Host lifecycle and native services | R31,R32 |
| [R34](#r34) | M4 | Packaging, upgrade and rollback | R33 |
| [R35](#r35) | M4 | Retirement and release gate | R34 |

Ranges in the dependency index mean every card in that range. R09 is intentionally unused;
M1 begins at R10. R04 may run independently of transcript work after R00; no delegation
is implied. Later tasks must respect the milestone gate even if their code looks independent.

## Validation sets

**Prototype (R00–R08):** locked metadata for R00; for code changes, `cargo +stable fmt --check`,
`cargo test --locked -j 1`, `cargo check --locked -j 1`, `cargo build --locked -j 1` from
`rust-port/gpui-prototype`. Tests must exercise production action methods, not duplicate logic.
Paint/input/a11y/platform cards additionally require the native observations they name.

**Integration (R10–R30):** matching Rust/TS fixtures, nearest owner suites found in `test/`,
Rust entity/race tests and repository `npm run verify` for production changes. Native controls
require painted, keyboard/a11y evidence; delivery/compaction require real signed-in browser.
Renderer reference changes also run `npm run build` and `npm run verify:ui`.

**Host/release (R31–R35):** preceding integration checks plus ABI, migration interruption,
process/shutdown, target packaging, installed-data and live-device/extension checks. Record
each target separately. Planning-only cards need documentation checks, not invented runtime proof.

<a id="r00"></a>
## R00: Baseline and dependency report

**Milestone / prerequisites:** M0; none. **Status:** planned.

**Allowed edits:** rust-port/docs/; both crate READMEs.

**Read first:** both Cargo.toml, Cargo.lock, rust-toolchain.toml and existing worklogs.

**Implementation recipe:** Record commit, Rust/rustfmt versions, exact GPUI pin, enabled features, actual Linux prerequisites and existing checks. Confirm the selected prototype never reads userData. Update README commands only if verified.

**Positive acceptance:** Locked metadata succeeds for both crates; dependencies and environment are reproducible.

**Negative / stop condition:** An unavailable dependency or unsupported target stays open; never regenerate locks to make a metadata check pass.

**Validation and handoff:** Run the milestone validation set above and name the exact tests
for both acceptance cases. Record actual outcomes, platform gaps, bounds/disposal and ledger
updates using the execution-guide template. The task stays open if its acceptance is unproven.

<a id="r01"></a>
## R01: Synthetic tail append

**Milestone / prerequisites:** M0; R00. **Status:** planned.

**Allowed edits:** gpui-prototype/src/main.rs and fixtures.rs; docs.

**Read first:** PrototypeApp, prepend_older, ListState use and existing GPUI tests.

**Implementation recipe:** Add deterministic next-ID fixture rows and a typed append action. Use one append method from action and tests. Keep resident IDs and the ListState owner stable. Observe whether the reader follows the tail before mutation; apply the pinned list update API and notify once.

**Positive acceptance:** Append at bottom follows the new tail; append off-tail preserves row ID and intra-row offset. Empty and repeated append cases retain unique IDs.

**Negative / stop condition:** A reader in the middle must not jump to bottom. A reset/rebuilt list is the negative control. Logical assertions alone do not satisfy R02.

**Validation and handoff:** Run the milestone validation set above and name the exact tests
for both acceptance cases. Record actual outcomes, platform gaps, bounds/disposal and ledger
updates using the execution-guide template. The task stays open if its acceptance is unproven.

<a id="r02"></a>
## R02: Painted viewport anchoring

**Milestone / prerequisites:** M0; R01. **Status:** planned.

**Allowed edits:** gpui-prototype/src/; docs.

**Read first:** GPUI pinned list/test APIs; R01 action and prepend tests.

**Implementation recipe:** Create a painted-window harness using supported pinned test APIs. Observe the top visible stable row and pixel offset before/after prepend and append. If the harness cannot inspect paint, document that limit and perform the native interaction separately.

**Positive acceptance:** Painted and native checks retain the same off-tail row/offset; followed append reaches tail. Record viewport size, scale and tolerance with the test.

**Negative / stop condition:** Do not substitute logical_scroll_top() or an unobserved timeout smoke for painted evidence. Preserve anchor after an empty/failed older page.

**Validation and handoff:** Run the milestone validation set above and name the exact tests
for both acceptance cases. Record actual outcomes, platform gaps, bounds/disposal and ledger
updates using the execution-guide template. The task stays open if its acceptance is unproven.

<a id="r03"></a>
## R03: Reflow and bounded transcript fixture

**Milestone / prerequisites:** M0; R02. **Status:** planned.

**Allowed edits:** gpui-prototype/src/; docs.

**Read first:** ListState splice/reset documentation and fixture generation.

**Implementation recipe:** Add manually triggered delayed-image dimensions, code disclosure and stream revisions; do not add a production watcher/timer. Exercise wrapping/resize and a bounded loaded-page eviction model while retaining canonical fixture IDs. Count resident rows/decoded assets and measured rows.

**Positive acceptance:** Off-tail anchor survives reflow, fold/unfold, older-page eviction and resize; followed reader follows streaming. Empty and large rows render with explicit limits.

**Negative / stop condition:** A revision cannot change row identity or imply a final turn; no whole-10,000-row measure_all pass or unbounded image cache.

**Validation and handoff:** Run the milestone validation set above and name the exact tests
for both acceptance cases. Record actual outcomes, platform gaps, bounds/disposal and ledger
updates using the execution-guide template. The task stays open if its acceptance is unproven.

<a id="r04"></a>
## R04: Native multiline composer

**Milestone / prerequisites:** M0; R00. **Status:** planned.

**Allowed edits:** gpui-prototype/src/; docs; dependency proposals only.

**Read first:** Pinned gpui input.rs/example; feasibility composer.

**Implementation recipe:** Implement a dedicated input entity with UTF-8/UTF-16 conversion, selection, marked range, replacement and native input handler. Add undo/redo, multiline paste and typed Enter/Shift+Enter actions. Keep synthetic Send inert.

**Positive acceptance:** Selection/replacement handles emoji, combining characters, RTL and multiline; undo restores selection. Native Japanese/Chinese IME candidate placement and Enter composition are observed.

**Negative / stop condition:** Enter while marked text exists must not Send; focus changes and view updates must not erase the draft. Do not promote the key-event-only editor to production.

**Validation and handoff:** Run the milestone validation set above and name the exact tests
for both acceptance cases. Record actual outcomes, platform gaps, bounds/disposal and ledger
updates using the execution-guide template. The task stays open if its acceptance is unproven.

<a id="r05"></a>
## R05: Transcript selection decision

**Milestone / prerequisites:** M0; R02,R04. **Status:** planned.

**Allowed edits:** gpui-prototype/src/; docs.

**Read first:** Current native composer and virtualized transcript.

**Implementation recipe:** Prove cross-row selection/copy across virtualization, code and mixed rows. If GPUI row text cannot support it, compare an explicit selection model or maintained selectable renderer; record APIs/license and a small reproduction.

**Positive acceptance:** Copied text matches the selected canonical content, including Unicode and offscreen continuation; native keyboard and pointer checks are recorded.

**Negative / stop condition:** Eviction cannot select a different row by recycled index; selection must not copy hidden unrelated tool details. Unresolved component choice blocks M0.

**Validation and handoff:** Run the milestone validation set above and name the exact tests
for both acceptance cases. Record actual outcomes, platform gaps, bounds/disposal and ledger
updates using the execution-guide template. The task stays open if its acceptance is unproven.

<a id="r06"></a>
## R06: Shell, focus and accessibility

**Milestone / prerequisites:** M0; R03,R04. **Status:** planned.

**Allowed edits:** gpui-prototype/src/; docs.

**Read first:** feasibility shell/theme/drop; pinned accessibility/key dispatch.

**Implementation recipe:** Integrate tested shell ideas into the selected crate: typed actions/key contexts, sidebar, resizable docks, modal focus, theme/text scale/reduced motion and synthetic file drop. Give repeated rows global stable accessible IDs.

**Positive acceptance:** Tab traversal, Escape/modal return, screen-reader names/roles/state/reading order, narrow layout and scaling work on native windows.

**Negative / stop condition:** Composer/terminal contexts cannot steal each other’s bindings; changing theme/scale preserves draft/focus. File drops remain synthetic and grant no access.

**Validation and handoff:** Run the milestone validation set above and name the exact tests
for both acceptance cases. Record actual outcomes, platform gaps, bounds/disposal and ledger
updates using the execution-guide template. The task stays open if its acceptance is unproven.

<a id="r07"></a>
## R07: Platform and performance matrix

**Milestone / prerequisites:** M0; R03,R05,R06. **Status:** planned.

**Allowed edits:** rust-port/ fixtures and docs; isolated benchmark fixtures.

**Read first:** Electron rendering/UI fixtures; exact GPUI pin.

**Implementation recipe:** Construct equivalent 10,000-row workloads and run Electron and GPUI on the same hardware. Record cold/warm startup, resident/GPU memory, idle CPU/wakes, scroll-frame and input latency with reproducible sampling. Exercise Linux Wayland/X11, Windows/macOS and required architectures.

**Positive acceptance:** Numeric measurements and agreed budgets have raw summaries/environment; input/a11y/render results name each actual target.

**Negative / stop condition:** Missing hardware, compile-only cross targets or a process smoke cannot pass a platform row. Compare total frontend plus host cost, not only the Rust process.

**Validation and handoff:** Run the milestone validation set above and name the exact tests
for both acceptance cases. Record actual outcomes, platform gaps, bounds/disposal and ledger
updates using the execution-guide template. The task stays open if its acceptance is unproven.

<a id="r08"></a>
## R08: Feasibility gate report

**Milestone / prerequisites:** M0; R01–R07. **Status:** planned.

**Allowed edits:** rust-port/docs/.

**Read first:** M0 evidence and component choices.

**Implementation recipe:** Summarize every M0 requirement, chosen components/licenses, measured budgets and failures. Obtain a documented reviewer go/no-go; retain Electron if a required behavior is blocked.

**Positive acceptance:** M0 input, selection, anchoring, accessibility and platform decisions have evidence; unresolved rows have explicit approved disposition.

**Negative / stop condition:** M1 stays closed if only the logical tests/build have passed.

**Validation and handoff:** Run the milestone validation set above and name the exact tests
for both acceptance cases. Record actual outcomes, platform gaps, bounds/disposal and ledger
updates using the execution-guide template. The task stays open if its acceptance is unproven.

<a id="r10"></a>
## R10: Freeze minimal wire contract

**Milestone / prerequisites:** M1; R08. **Status:** planned.

**Allowed edits:** new rust-port transport specification/fixtures; narrow TS adapter proposal.

**Read first:** src/preload/index.ts, pet-overlay.ts, main/ipc.ts, session/read-model.ts, shared/session.ts.

**Implementation recipe:** Select only catalog/state/history/worker read operations. Specify handshake, frame limits, schemas, errors, incarnation/load fencing, snapshot/gap recovery and writer election. Resolve immutable origins vs live revision cursors from source. Fill ledger rows before writing adapters.

**Positive acceptance:** Matching TS/Rust fixture examples include success, refusal, missing owner, malformed, oversized, truncated, gap and reincarnation cases with concrete budgets.

**Negative / stop condition:** No generic IPC/eval/credential/path operation; do not assume presentation reads have no backend maintenance effects.

**Validation and handoff:** Run the milestone validation set above and name the exact tests
for both acceptance cases. Record actual outcomes, platform gaps, bounds/disposal and ledger
updates using the execution-guide template. The task stays open if its acceptance is unproven.

<a id="r11"></a>
## R11: Private transport and lifecycle

**Milestone / prerequisites:** M1; R10. **Status:** planned.

**Allowed edits:** new transport modules in rust-port; named main host adapter and nearest tests.

**Read first:** Current startup/shutdown and the frozen R10 contract.

**Implementation recipe:** Implement private inherited pipe framing, fixed allowlist, handshake and bounded pending/event queues. Supervise the native child in explicit dev mode. Retain subscriptions/tasks in one owner; handle EOF and shutdown through existing lifecycle.

**Positive acceptance:** Both decoders pass shared fixtures; malformed/oversized/truncated frames fail before unsafe allocation. EOF/restart disables actions and rejects old replies.

**Negative / stop condition:** A frontend crash cannot orphan another backend writer; cancellation suppresses UI publication without cancelling accepted owner work.

**Validation and handoff:** Run the milestone validation set above and name the exact tests
for both acceptance cases. Record actual outcomes, platform gaps, bounds/disposal and ledger
updates using the execution-guide template. The task stays open if its acceptance is unproven.

<a id="r12"></a>
## R12: Catalog and session selection

**Milestone / prerequisites:** M1; R11. **Status:** planned.

**Allowed edits:** native catalog entities; named TS read adapters and tests.

**Read first:** projects.ts, session/read-model.ts, ipc catalog handlers.

**Implementation recipe:** Render paged projects/sessions and connection state. Retain each selection generation. Load A, pause its response, select B, return to A and release the original A response.

**Positive acceptance:** Only the current generation publishes; null/missing session and reconnect are visible; owner read suites and Rust races pass.

**Negative / stop condition:** Selected conversation ID is not session identity; removing a project grouping must not detach/delete its sessions.

**Validation and handoff:** Run the milestone validation set above and name the exact tests
for both acceptance cases. Record actual outcomes, platform gaps, bounds/disposal and ledger
updates using the execution-guide template. The task stays open if its acceptance is unproven.

<a id="r13"></a>
## R13: Canonical history and worker read view

**Milestone / prerequisites:** M1; R12. **Status:** planned.

**Allowed edits:** native transcript/worker read entities; narrow read adapters/tests.

**Read first:** shared/session.ts, shared/chronology.ts, session/store.ts/read-model.ts, agents.ts.

**Implementation recipe:** Load bounded recent/older pages by origin and revisions by nextFrom. Merge stable identities, recover subscription gaps and preserve off-tail anchor. Show exact prime-family worker views without changing prime selection.

**Positive acceptance:** Revised old messages stay in their page; failed older loads preserve cursors; duplicate events deduplicate; gaps reread; cache residency is bounded.

**Negative / stop condition:** Old worker/session replies cannot overwrite current views; history eviction cannot resurrect a pending bubble or revive worker execution.

**Validation and handoff:** Run the milestone validation set above and name the exact tests
for both acceptance cases. Record actual outcomes, platform gaps, bounds/disposal and ledger
updates using the execution-guide template. The task stays open if its acceptance is unproven.

<a id="r14"></a>
## R14: Read-only integration gate

**Milestone / prerequisites:** M1; R12,R13. **Status:** planned.

**Allowed edits:** rust-port/docs/ and wire fixtures.

**Read first:** M1 transport/entities and current read-owner suites.

**Implementation recipe:** Record matching Rust/TS contract, race/disconnect/bounds tests and native read views. Audit exported operation enum for absence of user mutations.

**Positive acceptance:** Canonical views agree with Electron; native keyboard/a11y observations exist; one elected writer remains Electron.

**Negative / stop condition:** A connected screenshot alone does not establish subscription correctness or read-only authority.

**Validation and handoff:** Run the milestone validation set above and name the exact tests
for both acceptance cases. Record actual outcomes, platform gaps, bounds/disposal and ledger
updates using the execution-guide template. The task stays open if its acceptance is unproven.

<a id="r15"></a>
## R15: Drafts, observed models and native staging

**Milestone / prerequisites:** M2; R14. **Status:** planned.

**Allowed edits:** native composer/draft entities; named staging adapters and owner tests.

**Read first:** renderer/chat.ts/chat-models.ts, session/input-attachments.ts/input-images.ts/start-input.ts.

**Implementation recipe:** Key project/unfiled drafts separately with replacement generations. Preserve drafts on navigation. Use observed model/effort catalog. Stage immutable originals through the TS owner and retain opaque IDs/preview bounds.

**Positive acceptance:** A -> B -> A import/model response cannot attach to the returned draft; manual deletion stays deleted; cancelled/failed staging is truthful.

**Negative / stop condition:** Do not fake missing native uploads with file references; model labels never prove entitlement. Draft storage grants no permission.

**Validation and handoff:** Run the milestone validation set above and name the exact tests
for both acceptance cases. Record actual outcomes, platform gaps, bounds/disposal and ledger
updates using the execution-guide template. The task stays open if its acceptance is unproven.

<a id="r16"></a>
## R16: Send and receipt reconciliation

**Milestone / prerequisites:** M2; R15. **Status:** planned.

**Allowed edits:** native Send/input status; named input adapter and integration tests.

**Read first:** session/input.ts and bridge.ts; renderer input reconciliation.

**Implementation recipe:** Elect one interactive writer. Submit frozen payloads through the outbox with stable IDs and display the owner’s exact stages. Reconcile only exact canonical input/history matches; resolve unknown outcomes via readback.

**Positive acceptance:** One accepted input produces one canonical bubble; late/lost reply and restart preserve debt without duplicate Send; signed-in native browser flow is observed.

**Negative / stop condition:** Insertion/transport ACK/button click cannot claim sent. Never retry an ambiguous authorized Send on disconnect.

**Validation and handoff:** Run the milestone validation set above and name the exact tests
for both acceptance cases. Record actual outcomes, platform gaps, bounds/disposal and ledger
updates using the execution-guide template. The task stays open if its acceptance is unproven.

<a id="r17"></a>
## R17: Queue steering and distinct controls

**Milestone / prerequisites:** M2; R16. **Status:** planned.

**Allowed edits:** native queue/control entities; named existing owner adapters/tests.

**Read first:** input.ts, session/finish.ts, blocked-chats.ts, bridge controls.

**Implementation recipe:** Add editable/reorderable/cancellable unclaimed queue, immediate/after-turn/finish delivery and exact-session Stop, End turn and Block as separate actions. Freeze display from owner responses.

**Positive acceptance:** Pause edit before claim, claim elsewhere, release edit and prove rejection; cancellation/late receipt is reconciled; real browser steering is checked.

**Negative / stop condition:** Stop is not outbox cancel, End turn is not verified completion, and Block does not imply native generation stopped.

**Validation and handoff:** Run the milestone validation set above and name the exact tests
for both acceptance cases. Record actual outcomes, platform gaps, bounds/disposal and ledger
updates using the execution-guide template. The task stays open if its acceptance is unproven.

<a id="r18"></a>
## R18: Goal, Loop, workflow and worker interaction

**Milestone / prerequisites:** M2; R17. **Status:** planned.

**Allowed edits:** native automation/plan/worker views; existing owner adapters/tests.

**Read first:** goal.ts, session/task-request.ts/finish.ts, agents.ts, shared/agent-plan.ts.

**Implementation recipe:** Project objective/mode and planner results with original task scope. Expose workflow checkpoints, displayed plans, worker inbox/report and wait setting through their owners. Keep stale draft planning results fenced.

**Positive acceptance:** Goal can stop and Loop stays within brief; checkpoints wait for real boundaries; family/run ownership and cancelled helper replies are tested.

**Negative / stop condition:** A displayed update_plan does not consume queue entries. Corrections extend the original task; stale helper prose cannot narrow it.

**Validation and handoff:** Run the milestone validation set above and name the exact tests
for both acceptance cases. Record actual outcomes, platform gaps, bounds/disposal and ledger
updates using the execution-guide template. The task stays open if its acceptance is unproven.

<a id="r19"></a>
## R19: Compact and Resume continuity

**Milestone / prerequisites:** M2; R17,R18. **Status:** planned.

**Allowed edits:** native compaction/recovery views; named continuation adapters/tests.

**Read first:** session/continuation.ts/resume-gate.ts/handoff.ts, bridge.ts.

**Implementation recipe:** Present continuation WAL phases and ambiguity faithfully. Keep the same local session/project/queue through A -> B provider rebinding; fence replies by token and epoch.

**Positive acceptance:** Compaction with queued input/worker work and restart preserves exact obligations; installed extension/browser flow confirms the rebind.

**Negative / stop condition:** Never infer resume success from tab opening or transport phase alone; old A receipts cannot mutate B.

**Validation and handoff:** Run the milestone validation set above and name the exact tests
for both acceptance cases. Record actual outcomes, platform gaps, bounds/disposal and ledger
updates using the execution-guide template. The task stays open if its acceptance is unproven.

<a id="r20"></a>
## R20: Task interaction gate

**Milestone / prerequisites:** M2; R16–R19. **Status:** planned.

**Allowed edits:** rust-port/docs/.

**Read first:** M2 native/TS suites and live provider evidence.

**Implementation recipe:** Document complete start/steer/inspect/continue flow, each failure/uncertain state, writer election and retained obligations on exit/restart.

**Positive acceptance:** Native input plus signed-in Send/attachments/stop/worker/compaction cases pass alongside owner and wire tests.

**Negative / stop condition:** Keep M2 open if only simulated receipts exist; real test actions must not replay uncertain work.

**Validation and handoff:** Run the milestone validation set above and name the exact tests
for both acceptance cases. Record actual outcomes, platform gaps, bounds/disposal and ledger
updates using the execution-guide template. The task stays open if its acceptance is unproven.

<a id="r21"></a>
## R21: Theme, localization and UI preferences

**Milestone / prerequisites:** M3; R20. **Status:** planned.

**Allowed edits:** native theme/locale/preference modules; docs.

**Read first:** appearance.ts, i18n.ts, locale catalogs and renderer preference owners.

**Implementation recipe:** Map assets and every preference key/default/lifetime/corruption/import rule. Port semantic tokens, labels/placeholders, locale search/dates and native menus/dialog actions. Preserve authored/provider/path text.

**Positive acceptance:** Language/theme switch retains draft/focus/selection; CJK, Turkish, long/narrow labels and corrupt preference import cases pass.

**Negative / stop condition:** Do not migrate send/history/permission/Goal authority into UI storage; use source inventory rather than hardcoded locale count.

**Validation and handoff:** Run the milestone validation set above and name the exact tests
for both acceptance cases. Record actual outcomes, platform gaps, bounds/disposal and ledger
updates using the execution-guide template. The task stays open if its acceptance is unproven.

<a id="r22"></a>
## R22: Setup, security and settings

**Milestone / prerequisites:** M3; R21. **Status:** planned.

**Allowed edits:** native setup/settings views; narrow existing adapters/tests.

**Read first:** config.ts, setup-profiles.ts, secrets.ts, connection.ts and settings IPC.

**Implementation recipe:** Port guide/pairing, roots/capabilities/read-only/command policy, profile selection, model/helper settings and three-way settings saves. Backend retains secret writes and profile epoch.

**Positive acceptance:** Stale save cannot undo new browser settings; revoked roots/permissions, failed picker and profile/key epoch race refuse safely.

**Negative / stop condition:** No secret snapshots, generic settings authority or bypass of OS Desktop consent; connection/pairing/model availability stay distinct.

**Validation and handoff:** Run the milestone validation set above and name the exact tests
for both acceptance cases. Record actual outcomes, platform gaps, bounds/disposal and ledger
updates using the execution-guide template. The task stays open if its acceptance is unproven.

<a id="r23"></a>
## R23: Rich transcript and review details

**Milestone / prerequisites:** M3; R21. **Status:** planned.

**Allowed edits:** native rich rows/review; named image/export adapters/tests.

**Read first:** renderer/chat.ts/tool-result.ts/agent-plan.ts, shared/session.ts, main/session/markdown-export.ts.

**Implementation recipe:** Select reviewed safe Markdown/rendering components; add citations/links/images/tool details/folding/copy/export/plan/unread views. Load bounded details outside render and preserve anchors.

**Positive acceptance:** Large/malformed content, failed image and Unicode citation cases preserve exact evidence; keyboard/selectable copy/a11y work.

**Negative / stop condition:** No active markup/remote image execution; historical tool-edit assets are not current Git diffs. Cancellation retires decoders.

**Validation and handoff:** Run the milestone validation set above and name the exact tests
for both acceptance cases. Record actual outcomes, platform gaps, bounds/disposal and ledger
updates using the execution-guide template. The task stays open if its acceptance is unproven.

<a id="r24"></a>
## R24: Docks, files and revision-safe editor

**Milestone / prerequisites:** M3; R21,R22. **Status:** planned.

**Allowed edits:** native dock/files/editor views; project-file owner adapters/tests.

**Read first:** project-files.ts/project-file-watcher.ts; renderer workspace-docks/file-code-editor.ts.

**Implementation recipe:** Choose reviewed editor, then port dock tab order/resize/hide, bounded tree/watchers, create/rename/reveal/attach/trash and revision-checked save. Keep unsaved drafts through navigation and concurrent edits.

**Positive acceptance:** Pending save plus newer edit stays dirty; project switch/revocation/symlink/revision conflict is fenced; hiding panel retires watches.

**Negative / stop condition:** Never overwrite a conflict, change permissions via project selection, or truncate an original after failed staging. Native dialogs need correct OS parent.

**Validation and handoff:** Run the milestone validation set above and name the exact tests
for both acceptance cases. Record actual outcomes, platform gaps, bounds/disposal and ledger
updates using the execution-guide template. The task stays open if its acceptance is unproven.

<a id="r25"></a>
## R25: Git and recorded edit review

**Milestone / prerequisites:** M3; R24. **Status:** planned.

**Allowed edits:** native review view; existing project-git/review adapters/tests.

**Read first:** main/project-git.ts; renderer review modules; getToolEditReview handler.

**Implementation recipe:** Port read-only working/branch-merge-base comparisons and exact recorded tool before/after assets with distinct identities. Fence selection by project/ref/HEAD generation.

**Positive acceptance:** Changed ref/HEAD cannot publish stale diff; nonrepo/binary/oversized/truncated states are explicit.

**Negative / stop condition:** No fetch/stage/commit/reset authority added; a historical tool review never reads today’s file as historical proof.

**Validation and handoff:** Run the milestone validation set above and name the exact tests
for both acceptance cases. Record actual outcomes, platform gaps, bounds/disposal and ledger
updates using the execution-guide template. The task stays open if its acceptance is unproven.

<a id="r26"></a>
## R26: Bounded image and PDF preview

**Milestone / prerequisites:** M3; R24. **Status:** planned.

**Allowed edits:** native preview entities; reviewed component integration/tests.

**Read first:** project-files.ts, renderer/file-pdf-viewer.ts and preview bounds.

**Implementation recipe:** Choose licensed maintained rendering engine. Match current input/pixel/backing-size limits; render selected pages only and cancel old project/page/zoom tasks before publication.

**Positive acceptance:** Oversized/malformed assets refuse; page/project/zoom races cannot paint stale pixels; memory/decode and native scaling checks pass.

**Negative / stop condition:** A tiny visual thumbnail is not a decode bound; unsupported previews offer truthful attach/reveal instead of invented content.

**Validation and handoff:** Run the milestone validation set above and name the exact tests
for both acceptance cases. Record actual outcomes, platform gaps, bounds/disposal and ledger
updates using the execution-guide template. The task stays open if its acceptance is unproven.

<a id="r27"></a>
## R27: PTY terminal parity

**Milestone / prerequisites:** M3; R24. **Status:** planned.

**Allowed edits:** native terminal and flow-control adapter/tests.

**Read first:** shared/workspace-terminal.ts, main/workspace-terminal.ts/workspace-terminal-ipc.ts; current terminal renderer.

**Implementation recipe:** Choose reviewed terminal emulator and port ANSI/Unicode/input/selection/resize/tabs plus owner acknowledgement/backpressure. Preserve process custody through hide/show; closing tab calls its owner.

**Positive acceptance:** Flood output remains bounded; resize/reconnect, pending spawn close, hidden exit and interactive keyboard cases pass on devices.

**Negative / stop condition:** Do not acknowledge bytes merely received if rendering/backpressure contract differs; no duplicate process on uncertain spawn. Use the exact current terminal owner paths before editing.

**Validation and handoff:** Run the milestone validation set above and name the exact tests
for both acceptance cases. Record actual outcomes, platform gaps, bounds/disposal and ledger
updates using the execution-guide template. The task stays open if its acceptance is unproven.

<a id="r28"></a>
## R28: Plugins, OAuth and skills

**Milestone / prerequisites:** M3; R22. **Status:** planned.

**Allowed edits:** native plugin/skill views; existing owner adapters/tests.

**Read first:** main/plugins/*, plugins-ipc.ts, plugin-refresh.ts and skill library owners.

**Implementation recipe:** Port catalog/install/config/enable/update/auth flows and cancellation; skills library/import/completion uses source semantics. Connector refresh remains distinct from local status.

**Positive acceptance:** Failed replacement preserves working install; stale OAuth/cancel/disable cannot re-enable; IME/stale completion cannot inject a different draft.

**Negative / stop condition:** Never execute packaged skill resources via UI; plugin OS authority is not approved-root sandboxing. Do not claim provider refreshed from local discovery.

**Validation and handoff:** Run the milestone validation set above and name the exact tests
for both acceptance cases. Record actual outcomes, platform gaps, bounds/disposal and ledger
updates using the execution-guide template. The task stays open if its acceptance is unproven.

<a id="r29"></a>
## R29: Usage, diagnostics, updates and pets

**Milestone / prerequisites:** M3; R21,R22,R23. **Status:** planned.

**Allowed edits:** native usage/diagnostic/update/pet views; existing owner adapters/tests.

**Read first:** current usage/diagnostics/update/pets/overlay owners and both preload surfaces.

**Implementation recipe:** Split into subcards/ledger rows before coding: estimates/provider limits, redacted logs, extension preferences, notices/updater, pet library and separate overlay. Reuse reviewed sprites/licenses and owned windows.

**Positive acceptance:** Estimate labels, failed update verification and overlay hit/focus/multi-monitor/idle behavior have independent native checks.

**Negative / stop condition:** No plaintext diagnostics or success-on-download; pet overlay operations must not disappear from coverage. Keep browser popup/injected UI retained explicitly.

**Validation and handoff:** Run the milestone validation set above and name the exact tests
for both acceptance cases. Record actual outcomes, platform gaps, bounds/disposal and ledger
updates using the execution-guide template. The task stays open if its acceptance is unproven.

<a id="r30"></a>
## R30: Full frontend parity audit

**Milestone / prerequisites:** M3; R21–R29. **Status:** planned.

**Allowed edits:** rust-port/docs/ and parity fixtures.

**Read first:** Both live preload inventories, renderer files, dynamic/static controls, preferences, native entry points.

**Implementation recipe:** Resolve every inventory row and independent action; adapt each Electron UI scenario into native checks. Run required TS/Rust/reference gates and native locale/a11y/input/platform matrix.

**Positive acceptance:** No unmapped modules/ops/events/dialogs/state or silent placeholders; every accepted row has evidence and reviewer.

**Negative / stop condition:** Electron verify:ui is a reference, not native acceptance. Any scope reduction needs explicit user-approved exception.

**Validation and handoff:** Run the milestone validation set above and name the exact tests
for both acceptance cases. Record actual outcomes, platform gaps, bounds/disposal and ledger
updates using the execution-guide template. The task stays open if its acceptance is unproven.

<a id="r31"></a>
## R31: Standalone host adapter design

**Milestone / prerequisites:** M4; R30. **Status:** planned.

**Allowed edits:** host migration specification and narrow adapter prototypes/tests.

**Read first:** main/index.ts/platform/services, all Electron imports, lifecycle/shutdown.

**Implementation recipe:** Inventory every Electron caller and service. Specify supervised pinned Node host, single-instance lock before shared data, paths/resources and narrow Rust OS adapter contracts. Preserve TS business owners.

**Positive acceptance:** Each dependency has a replacement/retained disposition, permission/process owner, failure test and ABI plan.

**Negative / stop condition:** Do not rewrite backend owners, introduce generic privileged RPC or remove Electron before the parity gate.

**Validation and handoff:** Run the milestone validation set above and name the exact tests
for both acceptance cases. Record actual outcomes, platform gaps, bounds/disposal and ledger
updates using the execution-guide template. The task stays open if its acceptance is unproven.

<a id="r32"></a>
## R32: Credential migration

**Milestone / prerequisites:** M4; R31. **Status:** planned.

**Allowed edits:** isolated migration adapters/tests and docs.

**Read first:** secrets.ts, plugin OAuth encrypted stores, current safeStorage policy.

**Implementation recipe:** Use old decryptor for bounded migration to reviewed OS storage. Stage/verify replacement before retirement, keep rollback ciphertext and cover interrupted migration. Never create plaintext transfer files.

**Positive acceptance:** Missing/locked keyring, Linux insecure fallback, wrong identity and interruption retain usable old store or explicit failure without widened access.

**Negative / stop condition:** New library cannot be assumed to decrypt secrets.bin; failed migration blocks cutover, not permission to drop credentials.

**Validation and handoff:** Run the milestone validation set above and name the exact tests
for both acceptance cases. Record actual outcomes, platform gaps, bounds/disposal and ledger
updates using the execution-guide template. The task stays open if its acceptance is unproven.

<a id="r33"></a>
## R33: Host lifecycle and native services

**Milestone / prerequisites:** M4; R31,R32. **Status:** planned.

**Allowed edits:** named standalone host/platform adapters and tests.

**Read first:** startup/connection/shutdown, clipboard/dialog/shell/tray/overlay/native helper owners.

**Implementation recipe:** Replace Electron services in bounded slices with explicit permissions, generations, OS parent windows and process custody. Rebuild native modules against pinned Node ABI. Keep accepted work drain/persistence ordering.

**Positive acceptance:** Crash/restart/second-instance/shutdown and consent failures do not orphan writers or tools; native clipboard/input/overlay flows work.

**Negative / stop condition:** Windows/macOS consent identity and helper behavior require installed-device proof; code compilation alone is insufficient.

**Validation and handoff:** Run the milestone validation set above and name the exact tests
for both acceptance cases. Record actual outcomes, platform gaps, bounds/disposal and ledger
updates using the execution-guide template. The task stays open if its acceptance is unproven.

<a id="r34"></a>
## R34: Packaging, upgrade and rollback

**Milestone / prerequisites:** M4; R33. **Status:** planned.

**Allowed edits:** target packaging/update/migration scripts/tests and docs.

**Read first:** packaging-targets/versions, notices/native-sources, extension-path.ts, updater and release contracts.

**Implementation recipe:** Build verified Node/native/tunnel/rg/extension payloads for every supported OS/arch; preserve extension mirror, signing/consent, license/source obligations and checksums. Test upgrade/rollback with isolated existing data.

**Positive acceptance:** Installed bytes run and retain history/outbox/project/worker/secret integrity; corrupt download and interrupted upgrade cannot replace verified payload.

**Negative / stop condition:** No installer success/version-label shortcut; do not publish or install into production without explicit authorization.

**Validation and handoff:** Run the milestone validation set above and name the exact tests
for both acceptance cases. Record actual outcomes, platform gaps, bounds/disposal and ledger
updates using the execution-guide template. The task stays open if its acceptance is unproven.

<a id="r35"></a>
## R35: Retirement and release gate

**Milestone / prerequisites:** M4; R34. **Status:** planned.

**Allowed edits:** obsolete Electron-only code removal after review; docs.

**Read first:** All M4 dependency dispositions, migration/device/package evidence.

**Implementation recipe:** Audit zero unexplained Electron dependencies and processes, target artifacts, installed browser/tool flows, rollback and release integrity. Remove obsolete plumbing only after its replacement evidence exists.

**Positive acceptance:** Every supported target has package/installed/live proof; existing-data migration and rollback are documented; release review authorizes shipping.

**Negative / stop condition:** A tag/build/PR does not authorize release or establish installed parity; leave incomplete target gates open.

**Validation and handoff:** Run the milestone validation set above and name the exact tests
for both acceptance cases. Record actual outcomes, platform gaps, bounds/disposal and ledger
updates using the execution-guide template. The task stays open if its acceptance is unproven.
