# Full GPUI port planning review

Date: 2026-10-01
POC: Planning and research only; no production code or platform runtime was changed.
TL;DR: Added `full-gpui-port-plan-2026-10-01.md` to make the frontend-first roadmap, host migration and release gates executable and testable.

## Scope and decision

Reviewed the current frontend and start plans, the repository product map, and official GPUI documentation at the revision pinned by the two synthetic prototypes. The master plan uses M0 feasibility, M1 read-only integration, M2 task interaction and M3 full frontend parity before M4's Electron host retirement. The TypeScript owners and Chrome extension remain authoritative. A Rust backend rewrite is outside the plan.

The existing frontend inventory remains the feature checklist; the master plan supplies stage order, protocol and identity rules, negative/race cases, platform/package evidence, upgrade and rollback gates. Research covered the official GPUI README, contexts, key dispatch, ownership, input, variable-height list, accessibility and test-support documentation. It distinguishes framework APIs from behavior the app must prove itself.

## Validation and limits

Read back the master plan after writing it and checked whitespace with `git diff --check` and `git diff --no-index --check`. The checkout still has an independently modified `.gitignore` and an untracked `rust-port/` tree; neither was staged or committed. No Cargo, npm, native UI, packaging, signed-in browser or installed-app check was run for this documentation change. Existing prototype test results are prior evidence, not a new validation claim.

Before implementing each slice, re-enumerate current renderer/preload surfaces and confirm the pinned GPUI APIs. Platform acceptance, performance budgets, security migration, and live provider behavior remain future gates rather than completed findings.
