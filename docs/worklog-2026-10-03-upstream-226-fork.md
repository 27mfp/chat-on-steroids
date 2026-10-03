# Upstream 2.1.26 fork update — 3 October 2026

## Integration

- Merged the immutable upstream `v2.1.26` release into fork main `e72b9dc`, retaining upstream authorship through the merge.
- Resolved Send conflicts by retaining the fork pre-click notification, editor-remount and receipt-text handling alongside upstream native Send-request receipts and configurable Core mention.
- Kept isolated fork identity and userData initialization before the single-instance lock, alongside upstream window placement restoration. Adopted upstream app-path-based development tunnel lookup.
- The primary checkout's uncommitted native frontend and other work remains untouched. Updated source and runtime are in `.worktrees/upstream-226-fork`; the fork desktop entry points there.
- Disabled GitHub Actions on `27mfp/chat-on-steroids` through repository Actions permissions before publishing; readback confirms `enabled:false`.

## Validation

- JavaScript syntax, staged whitespace checks, typecheck, privacy and production notices passed. Post-merge privacy check passed (1196 commits, 25 tags).
- `npm run build` passed; isolated extension prepared at 2.1.26.
- Full local verification: 6744 tests passed, 133 skipped, 34 failed in `finish-active-input`, `finish-input-integration`, and `session-finish`. This is not a passing verify gate.
- Separate v2.1.25 baseline runs reproduce all 34 failures: seven in the first two suites and 27 in `session-finish`. No clean full-suite gate is claimed; these failures predate the update.
- Serial shutdown validation: six tests passed; twenty platform-specific computer tests skipped on Linux.
- Real Electron composer UI check passed. Full UI validation was attempted twice but its first appearance check did not complete and was stopped. Initial shared-dependency font allowlist warnings were avoided by copying dependencies into the isolated worktree; a complete UI pass is not claimed.
- No signed-in ChatGPT flow was run.

## Installed applications

- Installed the official Linux x64 v2.1.26 AppImage at `~/.local/bin/chat-on-steroids` using an atomic replacement. Installed SHA-256 `c5eaa28db2c77b2b14f95c2222ca3967aadddff0c111af33c550f984f5a66fee` matches the upstream `SHA256SUMS.txt`.
- Extracted package and extension metadata both report 2.1.26. Packaged runtime/native resource smoke exited successfully.
- Previous AppImage retained at `/tmp/cos-official-2.1.26/previous-installed.AppImage`. The official desktop entry is unchanged; existing app data was not opened or changed.
- Fork desktop launcher and generated companion now use the isolated v2.1.26 build. Browser extension reload remains necessary in an already-open browser profile.
