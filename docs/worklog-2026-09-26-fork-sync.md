# Fork sync and compatibility review, 26 September 2026

## Scope and source state

The working tree started clean at `93573d8`, two commits behind upstream `main`.
It was fast-forwarded to reviewed French support at `750fad9`. The local fork `main`
then merged the authored commits from upstream PRs
[#414](https://github.com/totec448-spec/chat-on-steroids/pull/414),
[#401](https://github.com/totec448-spec/chat-on-steroids/pull/401),
[#405](https://github.com/totec448-spec/chat-on-steroids/pull/405), and
[#418](https://github.com/totec448-spec/chat-on-steroids/pull/418), and fork PRs
[#1](https://github.com/27mfp/chat-on-steroids/pull/1) and
[#3](https://github.com/27mfp/chat-on-steroids/pull/3). The existing European Portuguese
branch from [upstream #385](https://github.com/totec448-spec/chat-on-steroids/pull/385)
was merged separately. Original commits remain in the merge history.

These changes address the current composer field and its Send/Stop controls, stream
request attribution, escaped prompt-frame display, the unseen-completion marker, and
European Portuguese UI. The combined branches lacked the new sidebar label in the
French and Portuguese catalogs; both translations were added after the locale coverage
tests exposed the omission.

The `dev/project-icons-mock` worktree is an experimental project-icon and mock-runtime
branch with its own 32-file diff; it was left intact for separate product review. The
older `feature/sidebar-unseen-completion` ref contains an earlier form of the change
already carried by fork PR #3. The older model-discovery and release snapshot refs
diverge from the current line and were not merged wholesale.
No release tag, installer, extension installation, or signed-in browser acceptance was
performed by this integration.

## Validation

- TypeScript passed after the browser merges and again after the renderer merges.
- Eight browser/bridge suites passed: 1,531 tests.
- Four focused sidebar and locale suites passed: 58 tests after the catalog repair.
- Three focused renderer timeline cases for unseen completion and spinner continuity
  passed; the rest of that large suite was excluded from this focused run.
- The Electron production build passed. `git diff --check` passed.
- An initial full `npm run verify` reached ordinary Vitest after ripgrep, privacy,
  notices, Electron resolution and typecheck passed, but a session change interrupted it.
  A second run under a restricted filesystem/network profile failed broadly in tests
  that need subprocesses or loopback listeners. Isolated reproductions reported
  `spawnSync git EPERM` in `public-history-privacy.test.ts` and
  `listen EPERM ... 127.0.0.1` in `mcp-inflight.test.ts`; the run was stopped rather than
  interpreting these environment refusals as product regressions. The same four
  focused sidebar/locale suites passed again: 58 tests.

These checks demonstrate source, focused test and build behavior only. The complete
verification gate still needs an environment that allows its child processes and
loopback listeners. The extension scripts
ship unpacked, and a signed-in ChatGPT acceptance run still needs the changed extension
and app installed together.

## Follow-up review

Upstream has many open PRs, including several that touch the same changing browser
surface. The next compatibility review should assess
[#410](https://github.com/totec448-spec/chat-on-steroids/pull/410) (SPA strips the elected
input URL marker) and the stacked
[#422](https://github.com/totec448-spec/chat-on-steroids/pull/422) →
[#423](https://github.com/totec448-spec/chat-on-steroids/pull/423) (stale running state and
positional turn identity). These were not folded into the current browser merge. The
broader [#417](https://github.com/totec448-spec/chat-on-steroids/pull/417) changes native
rich content, file preview and several other subsystems and needs a separate review.
[#408](https://github.com/totec448-spec/chat-on-steroids/pull/408) addresses lost browser
receipts in the durable outbox and also remains separate.

The fork currently has no GitHub release. `src/main/update.ts`, `src/main/version.ts` and
the README still refer to upstream releases. Redirecting those URLs before the fork
publishes verified native artifacts would leave downloads and updates broken. A fork
release needs its own version, package/install checks, release assets and then a
deliberate update-source switch.

## Side-by-side local test launcher

The [Linux fork guide](fork-side-by-side-linux.md) describes a separate menu launcher and
Chromium profile. The launch marker moves Electron's data and session storage before
the single-instance lock, gives the window and tray a fork title, and skips upstream
update checks. The fork companion copy is named separately, scans only the fork's
fixed port 8769, and accepts only the fork's distinct `/hello` app identity. The
original companion accepts only the original app identity, including when the original
app happens to use port 8769. The original extension source remains unchanged. This local launcher
depends on the checkout and its installed dependencies. It does not claim a packaged
or installed runtime smoke result.

The new fork identity and extension-path tests passed six cases; TypeScript and the
production build passed. Preparing the isolated extension and generating the desktop
entry in a workspace-local test directory succeeded. The actual menu-entry install
was refused by this session's read-only home directory (`EROFS`), and a live Electron
launch was refused by its Linux sandbox host (`Operation not permitted`). No original
application or browser profile was changed.

## Fork tunnel startup repair

The source launcher lacked `resources/tunnel`, while the installed AppImage bundled
the pinned `v0.0.14` client and its `cloudflared` companion. `npm run tunnel` could
not fetch the release in this session (`fetch failed`), so the AppImage's existing
`resources/tunnel` directory was extracted and copied into this checkout's ignored
development resources. The installed AppImage was read only. The fork's saved
connection settings select the OpenAI tunnel and have no explicit binary path.

The locator also assumed the source file's directory depth. The Electron build
flattens it into `out/main/index.js`, so the dev resource path was one directory
too high. The locator now checks the compiled layout and retains the source layout
for tests. TypeScript, the production build, and 37 tunnel locator/behavior tests
passed. A compiled-directory probe resolved both binaries and read `v0.0.14`.
Tunnel startup itself still needs a live app session with network access.

## First-message receipt from live fork test

The live fork sent an opening `hi` and recorded ChatGPT's user message and final
answer, but the outbox retained its authorized browser claim without an ACK. The
provider's canonical user text escaped punctuation and 153 hard line breaks inside
the opening `COS_CONTEXT` frame; punctuation and hard-line unescaping restored the
exact 19,559-character frozen send. The desktop input path had used the strict
unescaped comparison, while the separate resume path already allowed escaped
Markdown. Desktop opening receipts now use the same frame-aware comparison for
native Send proof. The local turn receipt uses it for framed text as well, so a
fast reply can belong to its opening message. The comparison still requires the
same message id, route and send lifetime.

One focused regression reproduces the escaped opening and proves one ACK and one
turn start. All 718 content-script tests, TypeScript and the production build pass.
The staged unpacked fork extension was refreshed from this source. The old `hi`
claim was authorized under the previous extension and has no ACK; it remains
pending until the user withdraws that row. Do not replay it.

## Live tool-call routing diagnosis

The fork client stayed running and `/readyz` returned 200. Its OpenAI control-plane
poll was 24 seconds old during inspection. The failed ChatGPT tool call did not
reach the fork MCP server. The fork and original app have different Core tunnel IDs,
while ChatGPT's only installed Chat On Steroids Core app was connected on September
19, before this fork was set up. Its 300-second missing-client error is for the
older connector. The fork now projects **Chat On Steroids Fork Core** as its setup
name and in first-message instructions, leaving the underlying surface/tool contract
intact. A separate ChatGPT custom Tunnel app must be created for the fork tunnel;
the original connector remains available for the original installation.

The new fork-name test and existing MCP suite passed (165 tests, 15 skipped), as
did TypeScript and the Electron build. The user created the separate custom Tunnel
app in ChatGPT, then explicitly approved connecting it. ChatGPT showed both
**Chat On Steroids Fork Core** and the original **Chat On Steroids Core** in its
installed list. A live `exec_command` call through the fork connector ran `pwd`
in `/barraco-show`: the fork's MCP log recorded one successful tool invocation,
and ChatGPT displayed `/home/miguel/Code/barraco-show` with exit code 0. The
original ChatGPT connector and original desktop installation were not changed.
The user-requested disposable-file cycle also passed through the fork connector:
`apply_patch` created, edited and deleted
`/barraco-show/.chat-on-steroids-fork-tool-test.tmp`; `read` verified both
contents; `exec_command` confirmed the final path was absent. The fork MCP log
recorded the successful calls, ChatGPT displayed the full result, and an
independent filesystem check confirmed the file is absent.

## Model switcher review

The running fork saved a successful four-model account catalog: GPT-5.6 and
GPT-5.5 Instant/Thinking variants. A signed-in ChatGPT page showed the native
model picker and a composer picker trigger. Source inspection found that the
desktop power slider excluded labels beginning with `GPT-5.5`, but the live
catalog labels the older entries simply `5.5`. Consequently the older Thinking
entry could appear after the GPT-5.6 choices. The slider filter now excludes
both observed label forms; a regression fixture uses the short live label.

The four focused model suites passed (100 tests), as did TypeScript and the
production build. The live page was inspected without changing its model or
sending a message. This source build has not been reloaded into the running
fork desktop process, and an end-to-end desktop model-change/send remains
unverified.

The first full `npm run verify` run reached 216 passing test files and three
window-lifecycle test failures: its isolated BrowserWindow constructor fixture
omitted the fork's `appTitle` binding. Adding that binding to the fixture made
all 15 window-lifecycle tests pass. The subsequent full `npm run verify` passed:
217 test files / 5,787 tests in the main run, followed by 1 file / 6 tests in
the serial run; its other test files/cases were skipped by their existing gates.

## Opening context displayed after native Markdown serialization

A signed-in ChatGPT page and the fork's recorded opening showed the full
`COS_CONTEXT` frame instead of only the short authored message. Comparing the
saved frozen outbox text with the exact recorded user text found three indented
spaces serialized as literal `&#x20;` entities, in addition to the already
handled punctuation and hard-line escapes. Each entity added five characters,
so the frame's length proof failed. The shared display reader and extension DOM
reader now try that narrow entity decoding only after exact and ordinary escaped
frame reads fail. The desktop opening receipt compares the same transformed
source against its frozen send while retaining exact message and route ownership.

Regression tests cover the display readers, preservation of a literal entity in
an exact frame, and desktop opening ACKs with and without entity spaces. The four
focused suites passed (829 tests), and the production build passed. The running
fork app and installed browser extension have not been reloaded with these bytes.
Full `npm run verify` also passed: 217 files / 5,789 tests in the main run and
1 file / 6 tests in the serial run, with the remaining tests skipped by their
existing gates. Browser control blocked the Chrome extension-management page,
so this session did not stage/reload the active companion or repeat the live flow.
Reading the previously recorded opening with the updated shared parser returned
the exact authored `test`, matching its frozen outbox message.
