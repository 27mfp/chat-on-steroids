# GPUI frontend port planning

## Work

Created [the frontend port plan](gpui-frontend-port-plan.md) from the official GPUI website and its linked README, contexts, key dispatch, ownership, accessibility, examples, and crate manifests. Recorded immutable source links at Zed revision `66432e4ca957383dcc9ec61d1353a4b4bd94c6bc` and distinguished framework facts from proposed app architecture.

The plan starts with a GPUI feasibility prototype, then connects a native frontend to shared application operations in the existing Electron-hosted backend. Electron retirement and credential/native-runtime migration follow frontend parity. The backend and extension keep their existing ownership contracts.

Expanded the plan with a complete frontend coverage matrix: every top-level renderer TypeScript module, assets/locales, main and overlay views, static and dynamic controls, native integration, and presentation-state migration. Added inventories of all main preload operations/subscriptions (123/14) and pet-overlay operations/subscriptions (8/4). Production parity now requires no unmapped or unimplemented child behaviors, including secondary windows, errors, dialogs and subscriptions. Browser extension frontends remain explicitly retained outside the native rewrite with integration checks.

## Validation

Fetched and read the cited official source material. Inspected repository architectural entry points and confirmed the package declares 2.1.21. Reviewed document references, headings, protocol boundaries, milestones, and evidence limits. No production source changed. No app tests, GPUI build, package, or live integration were run for this documentation task.

Coverage checks enumerate both preload API objects and compare their members with the saved plan, check every top-level renderer TypeScript filename is named, resolve local Markdown references, and check whitespace. These are documentation inventory checks, not proof of live feature correctness or GPUI implementation.
