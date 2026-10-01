# Chat On Steroids GPUI feasibility prototype

This crate is the isolated Milestone 0 frontend prototype from `../docs/alternative/gpui-frontend-port-plan.md`. It uses synthetic fixtures only and must not read or mutate Chat On Steroids user data, session state, MCP state, browser state, or credentials.

The initial slice tests GPUI's variable-height list behavior with 10,000 logical transcript rows. It intentionally does not call `ListState::measure_all()`: the production transcript needs bounded viewport/overdraw measurement rather than a full-history layout pass.

The GPUI dependencies are pinned to Zed revision `66432e4ca957383dcc9ec61d1353a4b4bd94c6bc`, the research snapshot used by the port plan. Revisit the pin only with an explicit compatibility/build result because GPUI is pre-1.0 and its standalone platform API changes frequently.

From this directory:

```sh
cargo check
cargo test
cargo run
```

Current scope is source/build feasibility on the host Linux machine. A successful build is not Windows/macOS, packaging, accessibility, IME, or performance evidence.
