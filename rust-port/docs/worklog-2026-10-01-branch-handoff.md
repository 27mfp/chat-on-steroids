# Rust port branch and implementation handoff — 2026-10-01

## Change

Fast-forwarded the clean `feat/gpui-frontend-port` worktree to fork main `66d59a7`
(app 2.1.24). Transferred the existing Rust documentation and both referenced synthetic
prototype source trees, lockfiles and toolchain pins; omitted their build caches.
The shared main checkout's untracked originals and independently modified ignore file
were preserved. The port branch carries the matching `target/` ignore rule.

Added a single entry-point execution guide and 35 dependency-ordered task cards. Each
card names allowed scope, source entry points, recipe, acceptance, neighboring refusal
or race case, stop condition and validation/handoff. Enumerated 149 current preload
operations/events and 129 renderer/preload/UI-reference files. API rows have proposed
task/owner/view/fence mappings; all remain planned with no acceptance evidence. Source
rows intentionally require behavioral/asset review before implementation.

Added a stdlib documentation/inventory verifier and fixed repository links broken by
the previous alternative-document relocation. Updated the current master/start plans
to link the handoff and distinguish the branch baseline from historical untracked state.
No existing Rust implementation, production TypeScript or extension code was changed.

## Actual validation

On the current Linux development host:

- `python3 rust-port/scripts/verify-docs.py`: passed; local documentation paths,
  trailing whitespace, API/source drift, duplicate identities, task/status references,
  required accepted-row evidence and prototype pin/lockfile presence checked.
- `cargo metadata --locked --offline --no-deps --format-version 1` in both transferred
  crates: passed. Metadata outputs were temporary and are not repository artifacts.
- `cargo +stable fmt --check` in both transferred crates: passed.
- `cargo test --locked --offline -j 1` in `gpui-prototype`, reusing that crate's existing
  local target cache through `CARGO_TARGET_DIR`: passed, four tests. These establish
  deterministic fixtures and logical prepend/oldest-history behavior only.
- Byte comparison against the originals: both complete prototype source/lockfile/toolchain
  trees match; no implementation edits were mixed into the transfer.
- `git diff --check` and staged whitespace checks: passed.
- Both target directory spellings match the branch ignore rule; no target cache staged.

No new native visual, input/IME, accessibility, benchmark, cross-platform, full npm,
package, installed-app or signed-in browser check was run. M0 remains open. This PR is
an implementation handoff and reproducible synthetic baseline, not a production port.

## Review limitation

The destination fork has issues disabled. Its inherited PR checklist requires an issue
reference, so that requirement cannot be fulfilled by opening a fork tracking issue.
The PR description records the mismatch; no unrelated repository setting/policy was
changed and no fabricated issue reference is supplied. Other checklist requirements
remain applicable at their actual evidence level.
