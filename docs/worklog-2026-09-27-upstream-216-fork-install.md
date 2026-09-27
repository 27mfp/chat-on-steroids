# Upstream 2.1.16, fork and local app update — 27 September 2026

## Scope

- Merged the immutable upstream `v2.1.16` tag into the isolated fork, retaining its separate data directory, browser port 8769, companion identity, editable long Compact & Resume default and exact pre-Send custody checks. The merge preserves upstream commit authorship.
- Resolved five merge conflicts in the product map, browser bootstrap, Portuguese catalog and two tests. The browser resolution also takes upstream's worker `dispatching` transition at the existing native Send authorization boundary. Removed a duplicate Portuguese key exposed by catalog coverage.
- Adapted two input test mocks to provide the recorder's `evidenceWindow` when the 2.1.16 import path loads the MCP kernel.
- Built the fork and refreshed `outputs/fork-extension` from source for the separate browser profile.
- Replaced the original local AppImage at `~/.local/bin/chat-on-steroids` with the official Linux x64 2.1.16 release asset. The old AppImage was copied to `/tmp/cos-upstream-2.1.16/chat-on-steroids-previous.AppImage` before replacement. The desktop entry continues to point to the same path; its original userData is separate from the fork.

## Evidence and validation

- Official release `v2.1.16` is published, neither draft nor prerelease. The downloaded Linux x64 AppImage and installed file both hash to `669ebb0a1818d386cc8363c0d438d43d74134da1ee142c2048e6ad849ffa47f4`, matching `SHA256SUMS.txt` and the release asset digest. The extracted package metadata reports 2.1.16; the previous installed payload reported 2.1.15.
- `npm run typecheck`, `npm run build`, and `git diff --check` passed. Focused content, config, compaction, extension and fork-isolation suites passed: 1,098 tests. Input suites passed: 199 tests. Bridge, plugin refresh, Goal control, model, locale and extension-path suites passed: 716 tests.
- The fork launcher and original installed AppImage each remained running during a bounded 20-second desktop startup smoke, then were stopped. Both printed Electron Linux/Wayland warnings; this is startup evidence only. The original app mirrored extension version 2.1.16 into its stable userData path, and its `content.js` hash matches the official AppImage's packaged extension. The fork desktop entry was refreshed and still points to this checkout.
- The full `npm run verify` reached privacy and notices checks (both passed), typecheck and Vitest. It was stopped after repeat failures in `session-finish.test.ts` (26 of 41), `finish-active-input.test.ts` and `finish-input-integration.test.ts`. The finish suite also fails in isolation because its Goal decision cannot find a recorded user request; the prior 2.1.15 fork worklog reported this pre-existing finish-suite problem. Two input suites initially failed to import because of an incomplete recorder mock and passed after that test repair. The Portuguese duplicate initially failed locale coverage and passed after removal. A clean full gate is not claimed.
- The fork build and companion preparation are source/build evidence. The original installed payload is hash-verified package evidence. Browser extension reload, signed-in ChatGPT flow and live tool delivery have not been rechecked in this update.
