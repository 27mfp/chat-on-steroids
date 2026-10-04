# GPUI frontend port checklist

Branch: `feat/gpui-frontend-port`

This checklist tracks implementation evidence for [the GPUI frontend port plan](gpui-frontend-port-plan.md). A checked item means the named source/build/test evidence exists; it does not imply packaged or live-platform parity unless the item says so.

## Milestone 0 — framework feasibility

### Repository and dependency setup

- [x] Work in an isolated git worktree so the shared Electron tree stays untouched.
- [x] Confirm the local Rust toolchain is available (`rustc 1.98.1`, `cargo 1.98.1`).
- [x] Re-read current GPUI ownership, list, input, accessibility, application, and test guidance.
- [x] Pin the prototype to one immutable Zed revision for `gpui` and `gpui_platform`.
- [x] Generate and retain `Cargo.lock` after the selected revision builds successfully.
- [ ] Record Linux system build dependencies actually required by the selected pin.
- [ ] Validate the same pin on Windows and macOS before treating it as a cross-platform candidate.

### Synthetic native workspace

- [x] Create a standalone GPUI prototype under `rust-port/gpui-prototype` with no production backend access.
- [x] Add deterministic synthetic transcript fixtures with stable row identities.
- [x] Render 10,000 logical transcript rows through GPUI `ListState` without `measure_all()`.
- [x] Use content-driven row heights so the list exercises variable-height measurement.
- [x] Add a minimal native workspace shell around the transcript for realistic available width.
- [x] Exercise a GPUI `ListState` prepend with stable row IDs and preserved logical top-row offset in a native test. Visual scroll anchoring remains unverified.
- [ ] Exercise live tail appends while following the bottom and while scrolled away from it.
- [ ] Add delayed image-size changes and folded/unfolded code-block fixtures.
- [ ] Prove cross-row text selection or document the replacement strategy if virtualized rows cannot support it.
- [ ] Add a multiline composer with selection, undo/redo, clipboard, marked text/IME, drag/drop, and Enter-during-composition behavior.
- [ ] Add typed actions/key contexts for composer and workspace commands.
- [ ] Add accessible sidebar/session controls with stable AccessKit identities and keyboard traversal.
- [ ] Add resizable side/right/bottom docks.
- [ ] Add theme, text scaling, contrast, and reduced-motion toggles.
- [ ] Add file-drop handling using synthetic files only.

### Feasibility measurements

- [ ] Define an Electron fixture with the same 10,000-row synthetic workload.
- [ ] Measure cold/warm startup, idle CPU/wakes, memory, scroll frame latency, and input responsiveness on the same machine.
- [ ] Record Linux Wayland results.
- [ ] Record Linux X11 results.
- [ ] Record Windows x64/arm64 results.
- [ ] Record macOS x64/arm64 results.
- [ ] Set numerical budgets from the measurements instead of assuming GPU rendering is faster.

### Tests and evidence

- [x] `cargo check` succeeds against the pinned Zed revision on the host Linux machine.
- [x] Rust formatting is clean with the installed stable `rustfmt` matching Rust 1.98.1.
- [x] `cargo test --locked -j 1` passes (two fixture and two GPUI list-state tests, four total).
- [x] `cargo build -j 1` succeeds and the native binary remains alive through a 5-second Wayland launch smoke.
- [x] Add `#[gpui::test]` coverage for prepend row identity, logical offset and exhausted history with GPUI's pinned `test-support` feature.
- [ ] Add interaction tests for actions, focus, selection, and list updates.
- [ ] Run native keyboard/IME and screen-reader checks on supported OSes.
- [ ] Produce the Milestone 0 feasibility report with exact commands, pins, results, failures, and open component decisions.

## Later milestones

- [ ] M1: private versioned transport and read-only production projections.
- [ ] M2: complete task vertical slice through the existing outbox/session owners.
- [ ] M3: workspace feature parity and complete frontend coverage ledger.
- [ ] M4: Electron retirement after parity and platform adapter migration.

## Immediate TODO

1. Visually verify variable row heights and the same visible top row after clicking Prepend on the Linux display; list-state assertions alone do not prove painted anchoring.
2. Add tail-append fixtures and tests for following the bottom and preserving a scrolled-away reader.
3. Prototype the multiline composer using GPUI's native input handler path, including IME.
4. Add delayed-image and folded-code fixtures before taking transcript performance measurements.
