# GPUI prototype implementation

## Scope

Started the isolated Milestone 0 prototype from `docs/gpui-frontend-port-plan.md` on branch `feat/gpui-frontend-port`. This worktree does not connect to production user data, the Electron backend, MCP, the browser bridge, or the extension.

## Research decisions

- Rechecked current GPUI/Zed guidance for application startup, entities/contexts, variable-height lists, input, accessibility, and `#[gpui::test]` support.
- Kept the prototype on one immutable Zed revision (`66432e4ca957383dcc9ec61d1353a4b4bd94c6bc`) for both `gpui` and `gpui_platform`; the latter is not available as a matching crates.io `0.2.2` package.
- Avoided `ListState::measure_all()` for the 10,000-row fixture because GPUI documents that mode as measuring every item in the first layout phase. The transcript feasibility case needs bounded viewport/overdraw measurement.
- Kept the first slice read-only and synthetic so rendering feasibility cannot mutate or duplicate existing application business facts.

## First implementation slice

Added `rust-port/gpui-prototype` with deterministic transcript fixtures, stable row identities, a 10,000-row variable-height `ListState`, and a minimal native workspace shell. Added `docs/gpui-port-checklist.md` as the implementation tracker.

## Validation

- `cargo check` succeeded against the pinned Zed revision. Cargo resolved and locked 696 packages for the prototype dependency graph.
- The exact `1.98.1` rustup toolchain was auto-installed without its `rustfmt` component. The installed stable formatter reports `rustfmt 1.9.0-stable (48a229ceae 2026-09-01)`, matching the Rust 1.98.1 compiler revision; `cargo +stable fmt --check` passes after formatting.
- The first parallel `cargo test` attempt was killed by the host with exit 137 while compiling GPUI dependencies. Re-running with `cargo test -j 1` completed successfully: 2 tests passed, 0 failed.
- `cargo build -j 1` succeeded. On the active Wayland session (`DISPLAY=:0`, `WAYLAND_DISPLAY=wayland-1`), `timeout 5s ./target/debug/cos-gpui-prototype` reached the timeout with exit 124 and no process output, showing the native app stayed alive for the smoke window without an immediate GPUI/platform panic.
- The launch smoke is process evidence only. Scrolling, rendered row heights, selection, accessibility, IME behavior, frame latency, memory, and idle CPU have not yet been observed or measured.
