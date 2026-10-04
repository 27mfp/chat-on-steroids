# Dedicated Rust port folder — 1 October 2026

Moved both existing Rust/GPUI prototypes, their lockfiles, pinned toolchains and build caches
into the user-selected repository folder `rust-port/`. Main-checkout planning documents live
in `rust-port/docs`; the independent GPUI worktree's documents live in `docs/alternative`.
The two implementations remain separate. Updated documentation paths and ignored both build
cache directories. No Electron production source, app data or Rust implementation changed.

Validation: Cargo metadata checked for both crates with their pinned toolchains, existing
lockfiles and offline dependencies; Git ignore rules checked for both target directories;
whitespace checked. No compilation or GUI acceptance is claimed for this file relocation.
