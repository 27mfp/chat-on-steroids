# AdaL GPUI control room

Implementation always targets [PR #4](https://github.com/27mfp/chat-on-steroids/pull/4)
in `27mfp/chat-on-steroids`, branch **`feat/gpui-frontend-port`**. The controller must
run from that branch's worktree and publishes only through its `fork` remote.

**You only Start, Stop, and check status.** The full-screen dark dashboard shows
agent state, current assignments, reports/logs, PR progress, and your actual AdaL
plan, weekly usage/reset and separate credit-wallet balance.

```sh
# From the feat/gpui-frontend-port worktree:
./rust-port/orchestrator/run.sh
```

Open the printed dashboard URL. The server binds to `127.0.0.1`, sets an HttpOnly
local cookie, then redirects to a clean URL. No dependencies beyond Python 3.10+,
Git and installed AdaL are needed on Linux. Keep the terminal running for automatic
handoff. Starting the dashboard reads account usage but makes no model inference
request. **Start** begins the next eligible work from R00–R35, or resumes a stopped,
paused or blocked run. **Stop** cancels all owned model-process groups and preserves
work and logs. Clicking an agent shows its detailed brief, report and live log.

## Roles and automatic task flow

- **GPT-6 Sol (`openai-gpt-6-sol`) dispatches and reviews only.** Its runtime exposes
  Read/Search and custom orchestration tools; Edit and Bash are disabled. It never
  writes implementation, tests, docs or worklogs, and never fixes a worker's code.
- **GLM-5.3 Flash (`zai-glm-5.3-flash`) does all task work.** Implementation,
  verification and audit workers receive explicit roles and exact allowed files.
  No nested delegation. At most two workers; overlapping assigned files are refused.
- **The controller** owns durable completion delivery, process lifetime, Git staging,
  integration and publication. Deterministic controller Git actions are not model
  implementation. It never merges the PR or publishes/installs a product release.

Each brief must include a task-card ID plus detailed `Context:`, `Steps:`,
`Acceptance:`, `Negative cases:`, `Documentation:` and `Handoff:` sections, with
precise source/API references, invariant/owner, dependency evidence, bounded recipe,
positive and neighboring negative tests, commands/cwd and expected results. Vague
briefs are rejected. The lead must explain the assignment fully rather than just
name a card.

Each worker must change its unique task report in `rust-port/docs/tasks/` and dated
worklog in `rust-port/docs/`. Implementation/verification must also update
`task-cards.md` and any assigned checklist/ledger/guide rows. Missing required doc
updates make the task fail even if the CLI exits successfully. Reports and logs
preserve actual commands/results; native/platform evidence stays open until observed.

Worker completion automatically enters the persistent inbox and resumes the **same
lead session**. Results arriving during a lead turn wait for its end. The lead
reviews the actual patch and evidence, integrates or rejects it, then dispatches
the next task. It does not poll, sleep, or wait for the user to relay results.

An integrated implementation requires a **different verification worker**, from a
base containing that implementation's commit, with explicit independent checks.
Verification workers can modify docs only. Reviewed verification integration marks
the implementation verified. Defects go to a new implementation worker, then get
verified again; the lead never performs the fix itself. Audit-only documentation
cannot certify implementation.

After verified progress the lead calls `publish_progress`. The controller runs the
documentation verifier, checks local/remote branch ownership and source epoch,
applies the reviewed delta to the clean PR worktree, commits and pushes to
`fork/feat/gpui-frontend-port`. **No manual patch application, review, tests, commits
or push are required from you.** Source changes by another person/run cause refusal,
not an overwrite. There are no resets, force pushes, merges or branch substitutions.
A failed push preserves its local commit and retry state; it cannot create duplicate
commits just because the network response was lost.

The run automatically proceeds through eligible task-card dependencies and M0–M4
gates. An individual finished card is not a completed port. The lead exhausts
independent work before marking unavailable platform/native gates blocked. Start
can resume when appropriate. Runtime errors pause with evidence; no ambiguous work
is silently replayed. A missing device is never represented as a passing check.

## Actual AdaL usage

Both models use your AdaL login/subscription credits. The controller never selects
`chatgpt_web-*`, adds API keys, or changes account settings. Detected BYOAK/provider
key settings or OpenAI/Z.ai key environment variables prevent starting with an
unintended billing route.

`usage.js` uses the installed AdaL backend's own `getUsage()` / `/auth/usage` read
path, authenticated through your existing AdaL login. It performs no inference and
refreshes every 30 seconds. Only plan name, weekly percentage/reset/limit and wallet
balance reach the dashboard; tokens/account identifiers do not. This is **account
usage**, including other AdaL sessions, not an invented per-agent charge estimate.
A $0 credit wallet does not mean your weekly subscription allowance is exhausted.

The adapter is verified with AdaL CLI 1.8.17. It discovers the installed runtime
modules; an incompatible AdaL update/login/network failure shows `Unavailable`
rather than a fabricated zero or cached value presented as current.

## Isolation, durability and limits

Start requires a clean PR worktree. The current source is copied into a private
local Git repository; workers use separate task worktrees from that PR lineage.
Ignored caches, `node_modules`, `.adal` and original Git history are excluded;
symlinks are refused. Review/integration happens there before automatic PR
publication. The unrelated main checkout is never switched or edited.

State defaults to `~/.local/state/chat-on-steroids-adal/`, including run snapshots,
worker worktrees, patches, bounded logs and a durable inbox. It is outside Electron
userData. Only one controller may own a state directory. Ctrl+C cancels subprocesses
and pauses; restart marks previously active calls interrupted and opens paused.
Start is explicit continuation, not proof old calls survived.

Model processes run headless with `yolo` in their isolated workspace. **Worktrees
are not an OS sandbox**: allowed-file validation rejects invalid worker patches
after execution; it does not constrain every filesystem/network shell side effect.
The dispatcher's lack of Edit/Bash is an actual runtime tool restriction. Strong
worker isolation would need an additional container or OS policy.

Default limits: two workers concurrently, 60 workers per Start allowance, 30 lead turns
per Start allowance, 30-minute timeout per process, 8 MiB output/patch per process.
Start explicitly renews exhausted turn/worker allowances; no terminal action is needed.
These limits are not a monetary budget. Launch overrides:

```sh
./rust-port/orchestrator/run.sh --port 8788 --timeout 3600 --max-turns 40
```

## Verification

Offline regressions, without model calls:

```sh
python3 -m unittest discover -s rust-port/orchestrator/tests -v
python3 -m py_compile rust-port/orchestrator/server.py rust-port/orchestrator/tools.py
node --check rust-port/orchestrator/app.js
node --check rust-port/orchestrator/usage.js
python3 rust-port/scripts/verify-docs.py
```

Opt-in end-to-end provider test (**uses AdaL credits**):

```sh
python3 rust-port/orchestrator/tests/live_smoke.py --live
```

It uses a tiny synthetic repository and local bare Git remote. A real GLM worker
writes required evidence docs; the same read-only Sol dispatcher resumes, reviews,
integrates and automatically publishes to that local fixture. It never starts the
real port task or pushes smoke data to GitHub. Controller regressions cover actual
local Git publication and independent-verification gates. Native GPUI acceptance,
platform/runtime/release evidence remain separate from orchestration validation.
