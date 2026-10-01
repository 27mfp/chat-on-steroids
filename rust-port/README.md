# Chat On Steroids — Rust/GPUI port

Implementation home: branch `feat/gpui-frontend-port`. This is a planned native frontend
port, followed by Electron host retirement; the TypeScript business owners and Chrome
extension remain authoritative. Neither synthetic prototype connects production state.

Start with [the execution guide](docs/execution-guide.md) and its ordered
[task cards](docs/task-cards.md). They give bounded assignments, dependencies, source
entry points, refusal/race cases, validation and handoff requirements.

- [Master plan](docs/full-gpui-port-plan-2026-10-01.md): architecture, M0–M4 gates and release.
- [Frontend plan](docs/gpui-frontend-port-plan.md): complete behavioral coverage.
- [Coverage ledger](docs/coverage-ledger.tsv): every current preload operation/subscription.
- [Source inventory](docs/source-inventory.tsv): renderer/assets and Electron UI references.
- [Immediate start plan](docs/implementation-start-plan-2026-10-01.md): M0 sequence.
- `docs/alternative/`: preserved research and historical prototype evidence.
- `gpui-prototype/`: selected variable-height transcript baseline and logical prepend tests.
- `gpui-feasibility/`: comparison shell/input/theme/file-drop experiment.

Run the selected experiment from its crate directory so its pinned toolchain applies:

```sh
cd rust-port/gpui-prototype
cargo run --locked
```

Each crate retains its lockfile; build caches are ignored. Native input/selection,
accessibility, performance, cross-platform support and production integration remain
open gates. No prototype build implies a shipped port.

From the repository root, validate docs and inventory drift with:

```sh
python3 rust-port/scripts/verify-docs.py
```

- [AdaL control room](orchestrator/README.md): full-screen dark dashboard, a
  dispatch-only GPT-6 Sol lead, GLM implementation/verification workers, required
  per-task docs/worklogs, automatic publication to PR #4, and live AdaL usage.
