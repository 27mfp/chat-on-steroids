# Current working-tree installation and PR — 2026-09-17

The user requested installation of the current dirty tree, followed by a commit and PR.

## Snapshot

Built the shared working directory as version 2.1.13 without editing product source. Captured SHA-256 hashes for 313 package inputs before building; comparisons after packaging and installation showed no drift. The existing shared branch and index were preserved.

Prepared an isolated branch from public main a4fe9726, with 598 current product/public files. Existing public documentation and all current source, extension, scripts, tests, native code and license inputs were retained. Private local history and 312 local-only notes/evidence entries were excluded using the established publication boundary. The snapshot manifest and detailed logs are retained locally outside the publication tree. Every captured file matched the shared checkout and publication worktree; staged privacy, whitespace and common-secret checks passed.

This snapshot incorporates the adapted work from PRs #267, #264, #242, #240, #260, #251, #243 and #252. CONTRIBUTORS.md preserves original PR links; the snapshot commit includes the six original contributors' public noreply co-author trailers.

## Installed evidence

- Windows x64 build and packaged native/runtime smoke passed.
- Silent NSIS installation exited 0; version remains 2.1.13.
- All 287 packaged payload files, 132 compiled output files and 16 stable userData extension files match the installed bytes.
- Installed app.asar SHA-256: 0e88cab5629233c6eb8a6addaadfceb01e8c919dc7f8b59916245744db89d0f9.
- Installed-root native/runtime smoke passed. The installed executable is running and owns the bridge listener at 127.0.0.1:8765.
- No Chrome extension reload or live provider feature acceptance is claimed.

## Validation

Full npm run verify passed: privacy, notices/native-source metadata, typecheck, 200 ordinary test suites (4,873 tests passed, 44 skipped) and the separate shutdown suite (2 tests passed). Total: 4,875 passing tests. PR CI and live provider behavior remain separate verification levels.
