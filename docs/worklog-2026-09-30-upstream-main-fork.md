# Upstream main sync at 2.1.21 — 30 September 2026

## Source and integration

- Synced fork main from `dc6728c` with upstream main `5527ee2`. Upstream declares app and
  extension version `2.1.21`, bridge protocol `14`; main has five commits after the
  `v2.1.21` release tag, for release-check workflow and release-note follow-up.
- Used a merge so the upstream history and all 18 fork-only commits remain in the graph.
  The fork's local data identity, browser port 8769, editable handoff instructions and native
  composer/send custody remain in place.
- Resolved the composer overlap by accepting upstream's stable
  `data-composer-markdown` editor identity alongside the fork's visible Ask ChatGPT,
  pending-composer and unique visible candidate checks.
- Kept the fork's live composer draft reader and exact message/route/epoch receipt proof.
  Integrated upstream's one recovery retry only when the prior attempt had not reached
  authorization, native Send or a receipt, and the original editor lease can be rebound.
- Preserved the fork's GPT-5.5 composer exclusion, and updated this map with upstream's
  browser placement, recorder boundary and reload-row ownership behavior.
- Resume bootstraps still receive current Core and selected-project instructions without
  inferring Skills from generated handoff text. The saved brief budget reserves space for
  that bootstrap and its required framing.

## Validation

- App, package and extension versions agree at `2.1.21`; bridge protocol remains `14`.
- `git diff --check` and JavaScript syntax checks passed after conflict resolution.
- No unit suite, build or signed-in browser acceptance was run for this source sync.
- The original local development worktree and its existing `package.json` edit were left
  untouched; integration was performed in a separate worktree.
