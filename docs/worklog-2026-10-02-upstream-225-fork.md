# Upstream 2.1.25 fork update — 2 October 2026

## Integration

- GitHub latest release confirms `v2.1.25` (`5fb6d75`), published 2026-10-02, neither draft nor prerelease. Upstream `main` has later unreleased commits that still report version 2.1.25; this update uses the immutable release tag.
- Merged that tag into fork main `66d59a7`. Upstream authorship and the fork's isolated identity, userData, port 8769, handoff policy and composer/send custody remain.
- Send now reports the release's diagnostic codes and captures mention-free receipt text, including a classic textarea's value. Editor remount and the pre-click send callback stay available to the callers that already own them.
- The primary checkout's uncommitted files, including the native frontend work, were left untouched. The merge was prepared in `.worktrees/upstream-225-fork`.

## Validation

- `npm run verify:privacy` passed (965 commits, 23 tags).
- DOM input, fork identity, user prompt, resume and extension-path tests passed: 188 tests.
- `test/content-script.test.ts` passed: 809 tests.
- `tsc --noEmit` passed.
- No signed-in ChatGPT flow, package rebuild or desktop reinstall is claimed.
