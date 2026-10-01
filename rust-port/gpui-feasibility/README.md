# GPUI feasibility prototype

This is the isolated Milestone 0 prototype from `../docs/gpui-frontend-port-plan.md`.
It uses synthetic fixtures only and does not read or mutate Chat On Steroids user data.

The dependency is pinned to the GPUI source revision reviewed in the plan:
`66432e4ca957383dcc9ec61d1353a4b4bd94c6bc`.

On Linux, run:

```sh
cargo run --manifest-path rust-port/gpui-feasibility/Cargo.toml
```

The first slice exercises a bounded window over 10,000 logical transcript rows,
variable row heights, keyboard-editable multiline draft state, accessible controls,
dock resizing controls, theme/text scaling, and native file-drop paths. It is a
framework probe, not a production frontend and has no backend transport.

The composer intentionally uses GPUI key events in this slice so basic multiline
editing can be exercised immediately. Production acceptance still requires replacing
or extending it with an `EntityInputHandler`-based multiline implementation and proving
IME/marked-text behavior on the supported platforms.
