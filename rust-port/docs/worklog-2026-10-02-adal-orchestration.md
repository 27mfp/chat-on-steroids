# AdaL GPUI control room — 2026-10-02

## Scope and branch

Implementation home is [PR #4](https://github.com/27mfp/chat-on-steroids/pull/4),
`feat/gpui-frontend-port` in `27mfp/chat-on-steroids`. Added the local controller,
lead-only custom tools, role prompts, full-screen dark dashboard, usage adapter,
regressions and setup docs under `rust-port/orchestrator/`. Updated the Rust-port
README and execution guide. The unrelated main checkout's existing dirty/untracked
prototype work is preserved. No GPUI, Electron/extension production code, userData,
account settings, installed app or product release was changed by this setup.

## Required workflow

The user only starts/stops and checks status. GPT-6 Sol dispatches and reviews;
its runtime exposes Read/Search and custom tools, with Edit/Bash disabled. GLM-5.3
Flash workers do all implementation, independent verification, research artifacts,
tests, documentation and worklogs. Defects are delegated again, not fixed by Sol.

Every assignment includes an exact card ID and detailed Context, Steps, Acceptance,
Negative cases, Documentation and Handoff sections. Exact source paths, owner,
dependencies, API references, checks/cwd and expected evidence are required. Vague
briefs fail. Every task must update its unique report and dated worklog;
implementation/verification also update task-cards.md and assigned evidence rows.
Missing required docs fail completion. Two workers maximum; overlapping files stay
reserved through execution and review; nested delegation is prohibited.

The controller owns the durable inbox, scheduling and subprocess lifetime.
Completion resumes the same lead session automatically; mid-turn results wait.
Implementations are reviewed/integrated into a private PR-lineage staging tree,
then independently checked by another GLM worker from a base containing the change.
Verification workers can edit only docs and must explicitly report
`VERIFICATION: PASS` after their assigned checks pass. Corrected task state gets
verified again; failed evidence cannot certify implementation.

The controller checks docs, branch/remote ownership and source epoch before
committing/pushing reviewed verified progress automatically to PR #4's branch.
There is no user patch-application/commit/push step. No force push, reset, PR merge
or release. A failed push retains the owned local commit and retry state; retries
cannot duplicate commits. External dirty/advanced source refuses publication.

Start follows R00–R35 and M0–M4 gates, resumes stopped/paused/blocked work explicitly,
and does not convert unavailable native/platform evidence into acceptance. Independent
work is exhausted before an external gate is reported blocked. Failed/cancelled
assignments retain local logs and require a delegated documentation audit.

## Dashboard and actual usage

Dark layout fills the viewport. Only Start and Stop are primary controls; agent
selection shows detailed assignments, reports and streamed logs. It displays the
fixed PR/branch, individual status, waiting inbox, reviewed progress and run counts.

The usage adapter invokes installed AdaL's own read-only backend `getUsage()` path,
authenticated through the existing AdaL login, and refreshes every 30 seconds.
The actual Pro plan, weekly percentage/reset/limit and separate wallet balance were
observed in Chrome. No account identity/token reaches the UI, no balance is estimated,
and usage includes other AdaL sessions. Adapter failure shows unavailable. The
backend connection makes no model inference calls. No ChatGPT subscription model
or BYOAK key is selected/configured; inference uses AdaL credits.

## Actual checks

- Installed AdaL CLI 1.8.17 accepts the required headless/resume/model/tool flags.
- Live GPT-6 Sol called the custom status tool; live GLM returned its smoke marker.
- Revised `tests/live_smoke.py --live` passed with a tiny synthetic repo/local bare
  remote: real GLM wrote required docs/worklog, its result resumed the same Sol
  dispatcher on turn two, and Sol reviewed/integrated/finished with automatic local
  fixture publication. No real port task or smoke GitHub push was started. The lead
  performed no edit/shell calls.
- `python -m unittest discover -s rust-port/orchestrator/tests -v`: **22 passing**.
  Includes completion races/session continuity, pause/stop/cancel/restart, slot/file
  reservations, detailed brief/doc requirements, dispatcher tool restrictions,
  independent verification, actual local Git publication to the PR-named branch, Start renewal of exhausted
  turn/worker allowances,
  failed-push idempotence, external-source refusal, conflict refusal, review/finish
  gates, source isolation, process completion/timeout, single-controller ownership,
  path validation and HTTP token/Host/Origin boundaries.
- Python compile checks; JavaScript checks for `app.js` and `usage.js`: pass.
- `python3 rust-port/scripts/verify-docs.py`: passes with 35 task cards, 149 current
  API entries, 129 source/reference files. This is planning inventory, not parity.
- `git diff --check`: passes.
- Chrome painted verification: viewport-filling dark layout, idle Start/disabled
  Stop, fixed PR link, current AdaL account usage, agent/activity panes and clean
  token redirect. Real port execution remains idle for the user's Start action.

## Limits and remaining evidence

Runtime state is private local development data outside Electron userData. Token,
Host/Origin checks and CSP protect the loopback dashboard. Restarts pause interrupted
calls; ambiguous work is not silently replayed. Default process/turn/worker/output
bounds are execution limits, not monetary budgets. Worktrees isolate source changes,
not arbitrary OS/network access; workers run headless yolo and resulting patch paths
are checked after execution. The lead's tool restriction is enforced at runtime.

The usage adapter depends on installed AdaL backend APIs verified with 1.8.17 and
may show unavailable after an incompatible update. Controller/model/provider success
is not GPUI paint, input/IME, accessibility, cross-platform, installed or release
acceptance. Existing port cards and platform gates remain open until actual work
and evidence satisfy them. This setup does not mark R00–R35 implemented.

## Publication evidence

Setup commit `2b5da38` was pushed with
`git push fork HEAD:refs/heads/feat/gpui-frontend-port`. Both `git ls-remote fork`
and GitHub PR #4's head confirmed that commit. The branch worktree was clean;
main retained its pre-existing `.gitignore` modification and untracked Rust-port
sources. The follow-up removes the obsolete manual patch-export path and checks
that Start renews exhausted execution allowances without terminal intervention.
No PR merge or product release was performed.
