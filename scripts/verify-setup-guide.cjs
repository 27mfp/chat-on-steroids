// Real Chromium layout for the setup guide, using the production modules and styles.
// Serves a UI-only fixture; no app backend, credentials, browser pairing or tunnel is started.
const { app, BrowserWindow } = require('electron');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
app.setPath('userData', path.resolve(__dirname, '../outputs/setup-guide-runtime'));

app.whenReady().then(async () => {
  const { createServer } = await import('vite');
  const root = path.resolve(__dirname, '..');
  const output = path.join(root, 'outputs/setup-guide');
  fs.mkdirSync(output, { recursive: true });
  const server = await createServer({ configFile: false, root: path.join(root, 'src/renderer'),
    server: { host: '127.0.0.1', port: 0 }, plugins: [{ name: 'setup-fixture', configureServer(vite) {
      vite.middlewares.use('/setup-preview.html', async (_request, response) => {
        const source = fs.readFileSync(path.join(root, 'src/renderer/index.html'), 'utf8')
          .replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi, '')
          .replace('</body>', `<script type="module">
            import { initSetupGuide } from '/setup-guide.ts';
            import { initLanguage, setLanguage } from '/i18n.ts';
            initLanguage(); initSetupGuide(); window.setLanguage = setLanguage;
            document.querySelector('.app').dataset.screen = 'settings';
            for (const p of document.querySelectorAll('.panel')) p.classList.toggle('is-active', p.dataset.panel === 'setup');
            document.getElementById('tabs').hidden = false;
            document.getElementById('desktopTunnelField').hidden = false;
            window.fixtureReady = true;
          </script></body>`);
        response.setHeader('Content-Type', 'text/html');
        response.end(await vite.transformIndexHtml('/setup-preview.html', source));
      });
    } }] });
  let win;
  try {
    await server.listen();
    win = new BrowserWindow({ show: false, width: 1100, height: 900,
      webPreferences: { sandbox: true, backgroundThrottling: false } });
    await win.loadURL(server.resolvedUrls.local[0] + 'setup-preview.html');
    const ready = await win.webContents.executeJavaScript('window.fixtureReady');
    assert.equal(ready, true);
    const results = [];
    for (const [width, height, zoom, language] of [[1100, 900, 1, 'en'], [800, 650, 1, 'en'], [1100, 900, 1.5, 'zh-CN']]) {
      win.setSize(width, height);
      win.webContents.setZoomFactor(zoom);
      await win.webContents.executeJavaScript(`window.setLanguage('${language}')`);
      for (const [group, count] of [['tunnel', 2], ['key', 1], ['developer', 2], ['plugin', 2]]) {
        for (let index = 0; index < count; index++) {
          const selector = `[data-setup-guide="${group}"]`;
          const measured = await win.webContents.executeJavaScript(`(async () => {
            const host = document.querySelector('${selector}');
            const buttons = host.querySelectorAll('button');
            if (${index} === 0 && ${count} > 1) buttons[0].click();
            else if (${index} > 0) buttons[1].click();
            const img = host.querySelector('img'); await img.decode();
            host.scrollIntoView({block:'center'});
            await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
            const panel = host.closest('.panel'); const frame = host.querySelector('.setup-shot').getBoundingClientRect();
            return { imageLoaded: img.naturalWidth > 0, overflow: panel.scrollWidth > panel.clientWidth,
              labelsFit: [...host.querySelectorAll('.setup-callout')].every(n => {
                const r=n.getBoundingClientRect(); return r.left >= frame.left - 1 && r.right <= frame.right + 1 && r.bottom <= frame.bottom + 1;
              }) };
          })()`);
          assert.deepEqual(measured, { imageLoaded: true, overflow: false, labelsFit: true }, JSON.stringify({ group, index, width, zoom, measured }));
          results.push({ group, index, width, zoom, language, ...measured });
          // Image decoding/layout can finish before the offscreen compositor publishes its tile.
          await new Promise(resolve => setTimeout(resolve, 100));
          fs.writeFileSync(path.join(output, `${language}-${width}-${zoom}-${group}-${index}.png`), (await win.webContents.capturePage()).toPNG());
          if (width === 1100 && zoom === 1) {
            const rect = await win.webContents.executeJavaScript(`(() => {
              const r=document.querySelector('${selector} .setup-shot').getBoundingClientRect();
              return r.top >= 0 && r.bottom <= innerHeight ? { x:Math.round(r.x), y:Math.round(r.y), width:Math.round(r.width), height:Math.round(r.height) } : null;
            })()`);
            if (rect) fs.writeFileSync(path.join(output, `overlay-${group}-${index}.png`), (await win.webContents.capturePage(rect)).toPNG());
          }
        }
      }
    }
    // Native modal, Escape dismissal and focus restoration must work without opening a browser.
    await win.webContents.executeJavaScript(`(() => {
      const button=document.querySelector('[data-setup-guide="plugin"] .setup-guide-controls button:last-child');
      button.focus(); button.click();
    })()`);
    assert.equal(await win.webContents.executeJavaScript('document.querySelector(".setup-image-dialog").open'), true);
    fs.writeFileSync(path.join(output, 'enlarged.png'), (await win.webContents.capturePage()).toPNG());
    win.webContents.sendInputEvent({ type: 'keyDown', keyCode: 'ESCAPE' });
    win.webContents.sendInputEvent({ type: 'keyUp', keyCode: 'ESCAPE' });
    await win.webContents.executeJavaScript('new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))');
    assert.equal(await win.webContents.executeJavaScript('document.querySelector(".setup-image-dialog").open'), false);
    assert.equal(await win.webContents.executeJavaScript('document.activeElement.textContent'), '放大图片');
    const details = await win.webContents.executeJavaScript(`(() => {
      const d=document.getElementById('desktopTunnelField'); const initial=d.open;
      d.querySelector('summary').click(); return { initial, opened:d.open };
    })()`);
    assert.deepEqual(details, { initial: false, opened: true });
    fs.writeFileSync(path.join(output, 'results.json'), JSON.stringify(results, null, 2));
    console.log(`PASS: ${results.length} screenshot layouts; native modal/Escape/focus and optional disclosure.`);
  } finally {
    win?.destroy();
    await server.close();
  }
  app.exit(0);
}).catch(error => { console.error(error); app.exit(1); });
