import { el } from './dom.js';
import { t, ui } from './i18n.js';

type Callout = { text: string; at: [number, number]; box: [number, number, number, number] };
type Shot = { src: string; title: string; portrait?: boolean; notes: Callout[] };

// Only reviewed, redacted assets belong here. Overlays explain clicks; they never hide secrets.
const guides: Record<string, Shot[]> = {
  tunnel: [
    { src: new URL('./setup-images/create-tunnel.png', import.meta.url).href,
      title: 'Fill in a name and description, then find ChatGPT workspaces at the bottom.', notes: [
        { text: '1 · Name your tunnel', at: [54, 7], box: [7, 18, 88, 5] },
        { text: '2 · Add a description', at: [54, 25], box: [7, 31, 88, 12] },
        { text: '3 · Choose your ChatGPT workspace here', at: [48, 64], box: [7, 75, 88, 6] }
      ] },
    { src: new URL('./setup-images/workspace.png', import.meta.url).href,
      title: 'Select the workspace you use in ChatGPT, then create the tunnel and copy its ID.', notes: [
        { text: 'Your ChatGPT workspace goes here', at: [48, 65], box: [7, 74, 88, 7] },
        { text: 'Select the matching workspace', at: [49, 82], box: [7, 89, 88, 5] }
      ] }
  ],
  key: [
    { src: new URL('./setup-images/api-key.png', import.meta.url).href, portrait: true,
      title: 'Choose Restricted, then enable Read and Use under Tunnels. Leave other permissions at None.', notes: [
        { text: '1 · Select a project', at: [70, 20], box: [3, 26, 62, 3] },
        { text: '2 · Restricted', at: [70, 39], box: [10, 39, 14, 3] },
        { text: '3 · Tunnels: Read + Use', at: [70, 74], box: [52, 86, 46, 6] }
      ] }
  ],
  developer: [
    { src: new URL('./setup-images/developer-mode.png', import.meta.url).href,
      title: 'Settings → Security and login → Developer mode. Turn the switch on.', notes: [
        { text: '1 · Security and login', at: [3, 56], box: [2, 67, 26, 7] },
        { text: '2 · Turn Developer mode on', at: [52, 25], box: [86, 43, 7, 5] }
      ] },
    { src: new URL('./setup-images/plugins-settings.png', import.meta.url).href,
      title: 'You can also find a Developer mode shortcut at the bottom of Settings → Plugins.', notes: [
        { text: '1 · Open Plugins', at: [3, 23], box: [2, 33, 26, 7] },
        { text: '2 · Scroll down to Developer mode', at: [48, 71], box: [32, 84, 59, 9] }
      ] }
  ],
  plugin: [
    { src: new URL('./setup-images/plugins-page.png', import.meta.url).href,
      title: 'Open the ChatGPT Plugins page and click + at the top right.', notes: [
        { text: 'Click + to add your plugin', at: [48, 30], box: [91, 11, 6, 14] }
      ] },
    { src: new URL('./setup-images/new-plugin.png', import.meta.url).href, portrait: true,
      title: 'Copy the Core name and description below. Choose Tunnel, select your tunnel, choose No Auth, accept the notice and click Create.', notes: [
        { text: '1 · Choose Tunnel', at: [9, 33], box: [72, 39, 16, 4] },
        { text: '2 · Pick your tunnel', at: [44, 53], box: [12, 47, 77, 5] },
        { text: '3 · No Auth', at: [51, 66], box: [12, 61, 77, 5] },
        { text: '4 · Accept, then Create', at: [25, 86], box: [77, 90, 12, 5] }
      ] }
  ]
};

function screenshot(shot: Shot): HTMLElement {
  const figure = el('figure', 'setup-figure');
  const frame = el('div', `setup-shot${shot.portrait ? ' is-portrait' : ''}`);
  const img = document.createElement('img');
  img.src = shot.src;
  img.alt = ''; // The adjacent caption and text overlays describe the image in reading order.
  img.decoding = 'async';
  frame.append(img);
  for (const note of shot.notes) {
    const [x, y, width, height] = note.box;
    const box = el('span', 'setup-target');
    box.setAttribute('aria-hidden', 'true');
    Object.assign(box.style, { left: `${x}%`, top: `${y}%`, width: `${width}%`, height: `${height}%` });
    const label = el('span', 'setup-callout', () => t(note.text));
    Object.assign(label.style, { left: `${note.at[0]}%`, top: `${note.at[1]}%`, maxWidth: `${98 - note.at[0]}%` });
    const down = note.at[1] < y;
    const startY = note.at[1] + (down ? 5 : 0), endY = down ? y : y + height;
    if (Math.abs(endY - startY) > 2) {
      const startX = note.at[0] + 10, endX = Math.max(x + 2, Math.min(startX, x + width - 2));
      const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
      svg.setAttribute('class', 'setup-arrow');
      svg.setAttribute('viewBox', '0 0 100 100');
      svg.setAttribute('preserveAspectRatio', 'none');
      svg.setAttribute('aria-hidden', 'true');
      const line = document.createElementNS(svg.namespaceURI, 'path');
      const tipY = endY + (down ? -1.5 : 1.5);
      line.setAttribute('d', `M${startX} ${startY} L${endX} ${tipY} L${endX} ${endY} M${endX - 1} ${tipY} L${endX} ${endY} L${endX + 1} ${tipY}`);
      svg.append(line);
      frame.append(svg);
    }
    frame.append(box, label);
  }
  figure.append(frame, el('figcaption', '', () => t(shot.title)));
  return figure;
}

/** Presentation only: one screenshot at a time, with native keyboard controls and a larger view. */
export function initSetupGuide(): void {
  const dialog = document.createElement('dialog');
  dialog.className = 'setup-image-dialog';
  ui(dialog, 'aria-label', () => t('Setup screenshot'));
  const close = el('button', 'btn', () => t('Close'));
  close.setAttribute('type', 'button');
  close.addEventListener('click', () => dialog.close());
  const large = el('div');
  dialog.append(close, large);
  dialog.addEventListener('click', (event) => { if (event.target === dialog) dialog.close(); });
  dialog.addEventListener('close', () => large.replaceChildren());
  document.body.append(dialog);

  for (const host of document.querySelectorAll<HTMLElement>('[data-setup-guide]')) {
    const shots = guides[host.dataset.setupGuide!] ?? [];
    if (!shots.length) continue;
    let index = 0;
    const image = el('div');
    const controls = el('div', 'setup-guide-controls');
    const previous = el('button', 'btn', () => t('Previous image'));
    const next = el('button', 'btn', () => t('Next image'));
    const enlarge = el('button', 'btn', () => t('Enlarge image'));
    for (const button of [previous, next, enlarge]) button.setAttribute('type', 'button');
    const count = el('span', 'hint');
    count.setAttribute('aria-live', 'polite');
    function paint(): void {
      image.replaceChildren(screenshot(shots[index]!));
      previous.toggleAttribute('disabled', index === 0);
      next.toggleAttribute('disabled', index === shots.length - 1);
      ui(count, 'textContent', () => t('Image {0} of {1}', [index + 1, shots.length]));
    }
    previous.addEventListener('click', () => { if (index > 0) { index--; paint(); } });
    next.addEventListener('click', () => { if (index < shots.length - 1) { index++; paint(); } });
    enlarge.addEventListener('click', () => { large.replaceChildren(screenshot(shots[index]!)); dialog.showModal(); });
    if (shots.length > 1) controls.append(previous, count, next);
    controls.append(enlarge);
    host.append(image, controls);
    paint();
  }
}
