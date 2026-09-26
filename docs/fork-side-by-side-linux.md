# Run the fork beside the installed app on Linux

This local test launcher keeps the installed Chat On Steroids AppImage and its desktop entry
unchanged. It runs the built checkout through Electron, setting a separate name and data
path before requesting the single-instance lock. It separates Chromium data, app settings,
sessions, secrets and extension pairing. It does not
use the upstream release updater.

From this checkout:

```sh
npm run build
node scripts/prepare-fork-extension.mjs
node scripts/install-fork-desktop.mjs
```

The source launcher also needs `resources/tunnel/tunnel-client` and its matching
`cloudflared`. A packaged app includes these files. For a checkout, run `npm run
tunnel` to fetch the pinned, checksum-verified release. If downloads are unavailable
and the installed AppImage has the same pinned version, its `resources/tunnel`
directory can be copied into this checkout without changing the AppImage.

The new application-menu entry is **Chat On Steroids Fork**. It launches
`scripts/run-fork-local.sh`; the checkout and its `node_modules` must remain at this path.
The fork stores its own state in `$XDG_CONFIG_HOME/chat-on-steroids-fork` (or
`~/.config/chat-on-steroids-fork`). The installed app keeps its existing data directory.
The fork bridge is fixed to port **8769**; it will refuse that port if another process
owns it. The fork bridge and companion also check a distinct app identity, so each
companion ignores the other app even if that app uses port 8769.

For browser testing, run `scripts/run-fork-browser.sh`. This opens a separate Chromium
profile under `$XDG_CONFIG_HOME/chat-on-steroids-fork-browser` (or
`~/.config/chat-on-steroids-fork-browser`). In that profile, open `chrome://extensions`,
enable Developer mode, choose **Load unpacked**, and select this checkout's
`outputs/fork-extension` directory. The companion's name is **Chat On Steroids Fork
companion** and it scans only port 8769. Pair it after starting the fork app. The fork
starts with fresh settings, so approve its folders and set up its connectors there.
Keep the original companion in the original browser profile.

Create a separate custom **Tunnel** app in ChatGPT named **Chat On Steroids Fork Core**.
Use the fork's Core tunnel from **Settings → Setup**. The existing **Chat On Steroids
Core** app remains attached to the original installation's different tunnel ID;
it will report that its client is absent while the original app is closed. Choose
the fork connector explicitly when testing tools in the fork's chat. A green tunnel
status in the desktop app proves the fork's client is online, not that ChatGPT's
existing connector points at it.

After pulling or editing the fork, rebuild the app and prepare the extension copy again
while the fork browser profile is closed, then reopen that profile and reload its unpacked
extension. `node scripts/install-fork-desktop.mjs` updates only the fork desktop entry.

The source launcher is a local test installation, not a self-contained release. A later
fork AppImage should use its own package ID, executable name and verified release feed.
