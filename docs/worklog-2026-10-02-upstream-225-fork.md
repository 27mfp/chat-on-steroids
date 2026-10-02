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
- No signed-in ChatGPT flow was run.

## Installed apps

- The latest non-prerelease remained `v2.1.25`. Upstream `main` was left ahead of that tag and was not merged.
- Replaced `~/.local/bin/chat-on-steroids` with the official Linux x64 AppImage. Its SHA-256 is `12d8e149dcb7adcd33ef97ee5fd23607c46d18209a1a5845a2a3d97a578160db`, matching `SHA256SUMS.txt` and the release asset. Extracted package and extension metadata both report 2.1.25. The previous installed file is `/tmp/cos-official-2.1.25/previous-installed.AppImage`. The desktop entry path is unchanged. Real user data was not opened.
- Fast-forwarded this checkout to the published fork commit, built it, and refreshed `outputs/fork-extension` at 2.1.25 with port 8769 and the fork Core name. `node scripts/install-fork-desktop.mjs` refreshed only the fork desktop entry. Uncommitted local work was stashed for the build and restored afterwards.
