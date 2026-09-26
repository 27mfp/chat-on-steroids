#!/usr/bin/env bash
set -euo pipefail

browser=''
for candidate in google-chrome-stable google-chrome chromium brave-browser; do
  if command -v "$candidate" >/dev/null 2>&1; then browser="$candidate"; break; fi
done
if [[ -z "$browser" ]]; then
  echo 'Chrome, Chromium or Brave is required for the fork companion.' >&2
  exit 1
fi

profile="${XDG_CONFIG_HOME:-$HOME/.config}/chat-on-steroids-fork-browser"
exec "$browser" --user-data-dir="$profile" --no-first-run --new-window 'https://chatgpt.com/'
