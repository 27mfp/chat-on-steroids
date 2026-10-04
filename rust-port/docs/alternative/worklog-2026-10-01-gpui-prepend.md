# GPUI prepend feasibility, 2026-10-01

POC: The synthetic GPUI transcript can prepend older rows without changing the row at the logical scroll top or its offset within that row.

TL;DR: The alternative prototype now has a Prepend 25 older rows control. It retains existing fixture IDs and uses `ListState::splice(0..0, 25)` to shift the logical scroll index. The test exercises that state and the exhausted-history boundary. Painted scroll anchoring has not been checked.

## Decision and scope

Continue Milestone 0 with the existing 10,000-row `gpui-prototype` list. The fixture starts at ID 10,001 to provide a bounded synthetic older history. `synthetic_transcript_from` generates older IDs without regenerating any resident row. The on-screen control and GPUI state test use the same `PrototypeApp::prepend_older` operation. Resetting a new list at the old index provides a negative control: it points at a different row. The GPUI test harness needs the pinned crate's `test-support` feature as a dev dependency; the lockfile was updated offline. Neither this experiment nor the other prototype connects to app data or changes the TypeScript backend.

## Checks on this checkout

From `rust-port/gpui-prototype`:

- `cargo update --offline -q` updated the lockfile for the test-only feature.
- `cargo test --locked -j 1 -q`: four passed, zero failed (two fixture tests, two GPUI state tests).
- `cargo +stable fmt --check`, `cargo check --locked -q -j 1`, `cargo build --locked -q -j 1`: passed.
- `timeout 5s ./target/debug/cos-gpui-prototype`: exited 124 (timeout) with output suppressed, so the process stayed alive for five seconds; no visual interaction was verified.

These tests check logical list state without drawing a window. A visual test must confirm that the same row remains at the same painted position during prepend. Tail-follow behavior, native multiline input and IME, selection, accessibility, performance comparison and cross-platform validation remain open. Do not extract production transport until the Milestone 0 feasibility decisions have evidence.
