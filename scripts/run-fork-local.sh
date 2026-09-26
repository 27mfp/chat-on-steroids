#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ ! -f "$repo_root/out/main/index.js" ]]; then
  echo 'Build the fork first with npm run build.' >&2
  exit 1
fi
if [[ ! -x "$repo_root/node_modules/electron/dist/electron" ]]; then
  echo 'Electron is missing. Install the checked dependencies with npm ci.' >&2
  exit 1
fi
if [[ ! -f "$repo_root/outputs/fork-extension/manifest.json" ]]; then
  echo 'Prepare the isolated companion with node scripts/prepare-fork-extension.mjs.' >&2
  exit 1
fi

export COS_FORK_INSTANCE=1
export COS_FORK_EXTENSION_DIR="$repo_root/outputs/fork-extension"
export CLF_BRIDGE_PORTS=8769
unset ELECTRON_RUN_AS_NODE ELECTRON_RENDERER_URL
cd "$repo_root"
exec "$repo_root/node_modules/electron/dist/electron" "$repo_root" "$@"
