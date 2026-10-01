# Rust/GPUI port execution guide

Baseline: fork `main` at `66d59a7` (app 2.1.24), reviewed 2026-10-01.
Branch: `feat/gpui-frontend-port`. All implementation tasks below are **planned**.
Historical prototype worklogs retain their original results; they are not new acceptance.

## Read this first

The goal is a complete native Rust/GPUI frontend, followed by retirement of Electron.
The existing TypeScript business backend and Chrome extension stay authoritative.
“Rust port” does **not** currently authorize rewriting sessions, outbox, Goal, agents,
permissions, MCP, or bridge in Rust. That requires a separate architectural decision.

Read in order:

1. [Product contracts and owners](../../AGENTS.md), including its remaining sections.
2. [This guide](execution-guide.md), for assignment and handoff rules.
3. [Task cards](task-cards.md), for the next bounded implementation task.
4. [Master plan](full-gpui-port-plan-2026-10-01.md), for milestone gates and release.
5. [Frontend inventory](gpui-frontend-port-plan.md#complete-frontend-coverage), for behavior.
6. [Coverage ledger](coverage-ledger.tsv) and [source inventory](source-inventory.tsv).
7. The current source files named by the selected card; do not implement from prose alone.

The two crates are experiments. `gpui-prototype` is the selected transcript baseline.
`gpui-feasibility` supplies comparison ideas for shell, theme, input and file drop.
Do not develop both as production implementations. The `alternative/` docs are historical
research/checklists; when they disagree with this guide, use current product contracts,
this guide's sequencing and the master plan. Retain historical evidence without rewriting
it into a claim about today's commit.

## Exact first assignment

Start with **R00**, then **R01** in [task-cards.md](task-cards.md). R01 adds synthetic
append and followed/off-tail tests to `gpui-prototype`; it does not connect production
state. Do not start M1 while M0 decisions lack evidence. Later cards are ordered tasks,
not permission to skip the gates. If a required device or component is unavailable,
finish independent tasks in the same milestone and leave the device gate open.

## What an implementer may decide

Resolve local naming, helper extraction, fixture wording and layout details within the
card's allowed files. Use one presentation owner and typed actions. Verify any GPUI API
against Zed revision `66432e4ca957383dcc9ec61d1353a4b4bd94c6bc` before using it.
The toolchain is Rust `1.98.1`; both crates retain separate lockfiles.

Do not independently choose a third-party editor/terminal/PDF dependency, upgrade the
GPUI pin, weaken a product contract, introduce a backend owner, broaden a transport
allowlist, remove a production feature, or migrate credentials. Record those choices
in a decision report with alternatives, API/license evidence and the affected gate.
A missing API is a research task, not a reason to invent a signature. An unavailable
platform is an open acceptance item, not permission to claim cross-platform support.

## Repeat this procedure for every task

1. Check `git status --short` and `git diff -- <allowed files>`. Use the port worktree.
   Preserve unrelated work; do not reset, clean, switch, or reformat the shared tree.
2. Check dependencies in the task table and acceptance evidence in the ledger. Read the
   current implementation and nearest tests. State the invariant and owner in your notes.
3. Write the smallest positive and neighboring negative/race scenario. Use deterministic
   scheduling, not sleeps, to release stale work after its replacement has completed.
4. Implement the owner change, removing the obsolete branch it replaces. UI rendering
   projects facts; it does not create send, permission, completion or worker authority.
5. Run the card's checks. If they fail, keep the item open and report the exact failure.
   Rerun after fixing it. Missing installed dependencies are distinct from test failures.
6. Inspect the diff, disposal paths and memory bounds. Run the documentation verifier.
7. Update the relevant ledger rows and a focused worklog with actual evidence. Submit
   the slice for review. Do not mark a milestone passed just because a task compiles.

## Required identity and state rules

| Data | Authority | Native view rule |
| --- | --- | --- |
| Session/project binding | `session/store.ts`, `projects.ts` | Key selection by local session UUID, not provider conversation ID. |
| Tool/call ownership | `session/correlation.ts`, MCP kernel | Display exact recorded owner; never attach by timing or selected chat. |
| Input/queue/receipts | `session/input.ts` | Reconcile by exact input identity; admitted, inserted, sent and uncertain remain distinct. |
| Goal/Loop/checkpoints | `goal.ts`, input owner | Project obligations; a UI countdown/plan does not send or finish work. |
| Worker family/inbox | `agents.ts` | Include family/run incarnation and conversation, not `worker-1` alone. |
| Permission/settings/secrets | `config.ts`, `secrets.ts` | Backend checks at use; UI settings are not grants or secret storage. |
| Terminal process | existing terminal/process owners | Close a tab through the process owner; hiding a dock does not close PTYs. |
| Focus/selection/viewport | GPUI entities | One scoped owner, stable IDs, cancellable work and bounded caches. |

A native load token should contain `(backend incarnation, selection generation,
local session or draft key, request ID)`. Recheck the whole token before publishing.
A -> B -> A changes generation twice; equality of the session ID alone is insufficient.
Drop subscriptions and pending image/PDF work when their owning view is retired.
Backend restart invalidates live actions even if old painted history remains readable.

History paging uses immutable origin/chronology (`origin`, with the current source's
fallback rules) independently from live revision `seq` and `nextFrom`. `position` in
older design prose describes chronology, not a new wire field. Use the exact current
`src/shared/session.ts` and `session/read-model.ts` types. Never use revision order to
move a revised message to a different historical page. Never advance a live cursor
from an older-history request. `readSessionList()` can repair retained input receipts
through `listInputs()`; “read-only client” means no exposed user mutation, not a promise
that existing backend read projections perform zero maintenance writes.

## Proposed transport boundary — settle before M1 code

This is a design checklist, not an existing protocol. R10 must freeze concrete schemas,
limits and fixtures before R11 implements them. Prefer private inherited pipes during
Electron-hosted development. No generic channel name, eval, shell, file read or secret
RPC may be provided by the transport. Rust uses named owner adapters only.

Specify these fields and semantics in the R10 contract:

- A fixed protocol version, backend incarnation and frontend instance in the handshake.
- Requests: unique request ID, fixed operation enum, typed bounded arguments, owner token.
- Replies: matching request/incarnation, tagged success/refusal/error, bounded typed body.
- Subscriptions: subscription ID, snapshot boundary, monotonic event sequence; a gap
  invalidates that subscription and triggers a fresh snapshot, without mutation replay.
- Frame length prefix: byte order and maximum length, checked before allocation. Explicit
  text, image/base64, decoded pixel, resident-row, pending-request and event-queue budgets.
- Deadline/cancellation: retiring a UI request suppresses publication, but cannot undo
  a backend mutation already accepted. Unknown outcome invokes owner readback, not resend.
- EOF/restart: disable actions, clear capabilities, reject outstanding requests, discard
  old incarnation events and acquire a fresh snapshot before re-enabling actions.
- Writer election: Electron or GPUI, never two independent interactive writers to userData.
  M1 keeps Electron as writer; M2 requires explicit election and disconnect semantics.

Do not reuse the optional local control API as a generic full frontend API. It has its
own opt-in/token/read/action contracts and is not the port transport owner.

## Coverage ledger rules

`coverage-ledger.tsv` initially enumerates every property in both preload `api` objects.
`source-inventory.tsv` enumerates renderer/preload files and current Electron UI scripts.
They deliberately start at `planned`/`unreviewed`. Enumeration is planning evidence,
not proof that each method, menu or dynamic control has been understood or implemented.

Before implementing a source group, fill its owner, GPUI view, transport disposition,
identity fence, success/refusal/uncertain states, tests and native evidence. Add subrows
for independent dialogs/controls; never hide missing behavior behind a checked parent.
For assets choose `reuse asset`, `replace plumbing`, `port behavior` or `retain outside GPUI`.
A retained row names its concrete owner. Preferences require key/schema, default, lifetime,
corruption rule and import/rollback tests; enumerate `localStorage` and transient state
rather than inferring persistence from UI appearance.

Allowed status progression: `planned` -> `implemented` -> `tested` -> `accepted`.
`blocked` must name a reproduction/dependency; `deferred` must link an approved scope
exception. `tested` has named passing checks. `accepted` has the required native/platform
and review evidence. Keep source, logical, painted, native, package, installed and provider
proof distinct. The verifier checks inventory drift and basic structure; a reviewer checks
that the claims are true. M3 cannot exit with unreviewed inventory rows or pending dispositions.

## Checks and evidence recording

Run Cargo from the selected crate so `rust-toolchain.toml` applies:

```sh
cd rust-port/gpui-prototype
cargo +stable fmt --check
cargo test --locked -j 1
cargo check --locked -j 1
cargo build --locked -j 1
```

The historical reports used stable rustfmt matching the pinned compiler. Recheck
`rustc --version` and `cargo +stable fmt --version`; if stable has moved, install/use
the formatter for the pinned toolchain rather than silently changing formatting policy.
Single-job compilation avoids the earlier exit-137 memory failure; it is not a UI budget.
To reuse an existing local cache, set `CARGO_TARGET_DIR` to that crate's existing cache;
never commit `target/` or imply that a reused cache proves another platform builds.

From the repository root, run `python3 rust-port/scripts/verify-docs.py` and
`git diff --check`. Production TypeScript/protocol edits also require nearest owner
suites, both protocol participants and `npm run verify`; renderer changes additionally
require `npm run build` and `npm run verify:ui`. Discover suite names using `rg --files test`
and `rg`, not guessed commands. Electron UI passes provide parity references only.
Do not run full npm/build/package gates for an unchanged-app documentation transfer.

Every handoff must supply:

```text
Task ID / commit or dirty diff:
Invariant and authoritative owner:
Files changed and obsolete behavior removed:
Positive and neighboring negative/race scenario:
Commands, exact exit/results and environment:
Native/painted/provider evidence (or explicitly not run):
Bounds and disposal checked:
Ledger rows updated:
Remaining failures / decisions / next eligible task:
```

Never check an item because a test target built, a process lived five seconds, an action
button was clicked, or a prior worklog says it passed. Those facts have narrower meanings.

## Milestone review reports

R08 (M0), R14 (M1), R20 (M2), R30 (M3) and R35 (M4) produce a report with the task table,
coverage gaps, exact artifacts, failures, measurements and reviewer decision. Required
platform rows are Linux Wayland/X11, Windows x64/arm64 and macOS x64/arm64, consistent
with the master release plan. Do not infer arm64 runtime from an x64 build or a target flag.
The next milestone stays closed until the current gate is met or a specific user-approved
scope exception is recorded. M4 credential/installer work uses isolated test data first;
production adoption and release require their own authorization and installed evidence.
