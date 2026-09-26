# Compact & Resume delivery repair, 26 September 2026

## Result and ownership boundary

A signed-in live Compact & Resume completed end to end: the source sent the handoff, the replacement conversation sent its bootstrap message, and the durable local session committed from the source conversation to the replacement while keeping its linked project. ChatGPT began responding in the destination. This confirms the live happy path for the tested fork build and account.

The repeated-tab incident came from treating a proven pre-click failure as permission to reoffer the same brief. The bridge now durably aborts that exact continuation and reports failure, leaving the local session attached to its source. The extension releases only when its Send helper proves no native click occurred; after a click, missing receipt remains ambiguous and cannot be replayed.

The send boundary now follows native Send readiness. After each awaited authorization, the extension rechecks route, command, draft and native control. A resume send may adopt a remounted editor only when the complete normalized draft still matches and no trusted user input changed it. Source hydration waits for that exact marked draft and retains the authored user-message identity across Stop settling.

The replacement chat receives the current Core instructions and the durable session's linked project instructions inside `COS_CONTEXT`. The generated handoff does not select Skills. Handoff sizing reserves room for mandatory Core and project identity before saving the brief.

## Validation

- Live Compact & Resume sent the source handoff and destination bootstrap, then committed the same local session to the new conversation with its project binding intact.
- `test/content-script.test.ts`: 720 passed.
- Nine focused bridge, resume, prompt, identity, IPC, renderer and lifecycle suites: 695 passed. The focused bridge contract checks passed: 3 tests.
- `npm run typecheck` passed as part of the verification command. `npm run build` passed.
- `node --check` passed for `extension/content.js` and `extension/chatgpt-dom.js`; `git diff --check` passed.
- `node scripts/prepare-fork-extension.mjs` refreshed `outputs/fork-extension`; both prepared resume scripts match their source hashes. `node scripts/install-fork-desktop.mjs` refreshed the fork-only application menu entry.
- The full `npm run verify` gate remains red. It reached Vitest after privacy, notices and typecheck passed; `session-finish.test.ts` reported 25 failures, and `finish-active-input.test.ts` reported 3. Running `session-finish.test.ts` alone reproduced its failures, including missing authored Goal request evidence. These failures are outside the focused Compact & Resume suites and need a separate investigation.

The changed extension bytes are prepared for the fork's unpacked companion. Chrome still needs to load/reload that extension before the latest pre-click cleanup branch is active; a second live run of that exact failure branch was not performed. The successful live run above predates this final cleanup refinement.
