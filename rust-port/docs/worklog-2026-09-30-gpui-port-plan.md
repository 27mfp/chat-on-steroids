# GPUI frontend port planning

## Work

Created [the frontend port plan](gpui-frontend-port-plan.md) from the official GPUI website and its linked README, contexts, key dispatch, ownership, accessibility, examples, and crate manifests. Recorded immutable source links at Zed revision `66432e4ca957383dcc9ec61d1353a4b4bd94c6bc` and distinguished framework facts from proposed app architecture.

The plan starts with a GPUI feasibility prototype, then connects a native frontend to shared application operations in the existing Electron-hosted backend. Electron retirement and credential/native-runtime migration follow frontend parity. The backend and extension keep their existing ownership contracts.

Expanded the plan with a complete frontend coverage matrix: every top-level renderer TypeScript module, assets/locales, main and overlay views, static and dynamic controls, native integration, and presentation-state migration. Added inventories of all main preload operations/subscriptions (123/14) and pet-overlay operations/subscriptions (8/4). Production parity now requires no unmapped or unimplemented child behaviors, including secondary windows, errors, dialogs and subscriptions. Browser extension frontends remain explicitly retained outside the native rewrite with integration checks.

## Validation

Fetched and read the cited official source material. Inspected repository architectural entry points and confirmed the package declares 2.1.21. Reviewed document references, headings, protocol boundaries, milestones, and evidence limits. No production source changed. No app tests, GPUI build, package, or live integration were run for this documentation task.

Coverage checks enumerate both preload API objects and compare their members with the saved plan, check every top-level renderer TypeScript filename is named, resolve local Markdown references, and check whitespace. These are documentation inventory checks, not proof of live feature correctness or GPUI implementation.

## Milestone 0 implementation start

Added `rust-port/gpui-feasibility` as an isolated Rust/GPUI application with no production backend transport or userData access. It pins Rust 1.98.1 and the same Zed revision used by the architecture review. The first slice creates 10,000 synthetic logical transcript rows while loading 320 variable-height rows at a time, plus keyboard-editable multiline draft state, accessible roles/labels for navigation and controls, theme and text-size controls, dock resizing controls, and native external file-drop handling. `Cargo.lock` is committed as part of the prototype so the tested transitive set remains reviewable.

Validation on this host: `cargo check --manifest-path rust-port/gpui-feasibility/Cargo.toml` passes; `cargo test --manifest-path rust-port/gpui-feasibility/Cargo.toml --no-run` builds; `cargo fmt` was applied; and `timeout 8s cargo run --manifest-path rust-port/gpui-feasibility/Cargo.toml` reached the running application and stayed alive until the timeout without an emitted startup error. Host evidence was Linux Wayland (`WAYLAND_DISPLAY=wayland-1`, `DISPLAY=:0`) with an NVIDIA GeForce RTX 3060.

Milestone 0 remains open. The current draft editor is a key-event probe, not an `EntityInputHandler` multiline implementation, so marked text/IME and full selection are unproven. Stable transcript anchoring across automatic prepend/eviction, screen-reader behavior, Windows/macOS and Linux X11 builds, controlled streaming/image completion, performance measurements, and the equivalent Electron baseline are still required before the plan permits production transport extraction.
