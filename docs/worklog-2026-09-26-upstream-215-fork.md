# Fork update to upstream 2.1.15, 26 September 2026

## Scope and ownership

- The pre-existing `sync/upstream-2026-09-26` index contained the upstream 2.1.15 source and post-release main through `6df2151`, adapted for the fork's separate app/extension identity, port 8769, userData and browser profile. Commit `8298ec4` preserved that work and closed 99 missing European Portuguese catalog entries. Its native-send receipt adjustment came from the fork's earlier live observation.
- Merge `origin/main` at `8c0381f` brought the later Project source-load budget fix with upstream commit history and authorship intact.
- Cherry-picked [upstream PR #410](https://github.com/totec448-spec/chat-on-steroids/pull/410) by @WanxTitanx. Conflict resolution retained the fork's already narrower Plugins route classifier and current composer draft reader while accepting election-based custody after ChatGPT strips URL markers.
- Cherry-picked [upstream PR #388](https://github.com/totec448-spec/chat-on-steroids/pull/388) by @lavalava45. The handoff content prompt is editable, but continuation identity, delivery and recovery framing stay code-owned. The fork retains its former detailed default rather than changing substantial handoffs to the PR's shorter 2k–6k target. The PR's config fixture now restores the exact prior config so approved roots survive the case.
- The original installed application, its extension source, connector and userData were not modified by source integration. The fork launcher and companion remain separately identified; the source launcher is not a self-contained fork package.

## Validation

- `npm run typecheck` and `npm run build` passed after integration.
- 920 focused desktop-input, content-script and plugin-refresh tests passed after PR #410.
- 27 Compact & Resume tests, 308 config/session/renderer/pt-PT tests, and 259 fork-isolation, extension-path, desktop-input and DOM tests passed after PR #388 and adaptations.
- `git diff --check` passed. The editable default is 4,988 characters, below its 20,000-character config limit.
- The full `npm run verify` was stopped after it exposed missing pt-PT keys (fixed) and many `session-finish.test.ts` failures. One representative finish failure was reproduced unchanged in a detached worktree at the prior fork `HEAD` (`374ec02`), so it is not evidence that this sync caused it. A later complete gate is still needed; targeted passing suites do not replace it.
- No new packaged payload or signed-in ChatGPT acceptance was claimed. The fork's rebuilt local bundle and prepared unpacked extension require reload in its separate browser profile before live behavior can be assessed.

## PR review

- [#410](https://github.com/totec448-spec/chat-on-steroids/pull/410): accepted for the exact elected-tab custody problem; it preserves one opening attempt and does not treat a user-closed tab as permission to open another.
- [#388](https://github.com/totec448-spec/chat-on-steroids/pull/388): accepted as a useful personalization control with the existing comprehensive default retained.
- [#391](https://github.com/totec448-spec/chat-on-steroids/pull/391) and [#417](https://github.com/totec448-spec/chat-on-steroids/pull/417): deferred. Both touch compaction or several native browser boundaries already modified in the fork and require separate live reproductions and validation.
- [#379](https://github.com/totec448-spec/chat-on-steroids/pull/379): deferred until its extension catalog includes the fork's Portuguese UI and isolated companion strings.
