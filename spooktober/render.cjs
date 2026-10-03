#!/usr/bin/env node
/*
 * Headless renderer for spooktober/index.html.
 * Renders every frame of the timeline with Chromium (SwiftShader, no GPU needed),
 * renders the soundtrack offline through the same Web Audio graph, then muxes
 * both with ffmpeg into a Twitter-ready H.264/AAC MP4.
 *
 *   node render.cjs                        # full 1280x720 @ 30fps render
 *   node render.cjs --w 1920 --h 1080      # 1080p
 *   node render.cjs --stills 2,10,18,30    # just a few PNG stills (seconds)
 *   node render.cjs --workers 2            # parallel browser pages
 *   node render.cjs --start 0 --end 300    # frame range (resumable: existing PNGs are skipped)
 */
const path = require('path');
const fs = require('fs');
const { spawnSync } = require('child_process');

let chromium;
try { ({ chromium } = require('playwright')); }
catch { ({ chromium } = require('/opt/node-tools/node_modules/playwright')); }

const args = process.argv.slice(2);
const opt = (name, def) => { const i = args.indexOf('--' + name); return i >= 0 ? args[i + 1] : def; };
const W = parseInt(opt('w', '1280'), 10), H = parseInt(opt('h', '720'), 10), FPS = parseInt(opt('fps', '30'), 10);
const WORKERS = parseInt(opt('workers', '2'), 10);
const OUT = path.resolve(opt('out', path.join(__dirname, 'out')));
const STILLS = opt('stills', null);
const HTML = 'file://' + path.join(__dirname, 'index.html') + `?render=1&w=${W}&h=${H}`;
const CHROME_ARGS = ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--enable-webgl', '--autoplay-policy=no-user-gesture-required'];

fs.mkdirSync(OUT, { recursive: true });
const framesDir = path.join(OUT, 'frames'); fs.mkdirSync(framesDir, { recursive: true });

async function openPage(browser) {
  const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
  page.on('console', m => { if (m.type() === 'error' || /error/i.test(m.text())) console.log('[page]', m.text()); });
  page.on('pageerror', e => console.log('[pageerror]', e.message));
  await page.goto(HTML);
  const info = await page.evaluate(([w, h]) => window.__spook.setup(w, h), [W, H]);
  const err = await page.evaluate(() => document.getElementById('err').textContent);
  if (err) throw new Error(err);
  return { page, info };
}

async function renderFrames(browser, list, label) {
  const { page, info } = await openPage(browser);
  if (label === 0) console.log('renderer:', info);
  const t0 = Date.now(); let done = 0;
  for (const { idx, t, file } of list) {
    if (fs.existsSync(file)) { done++; continue; }
    await page.evaluate(t => window.__spook.frame(t), t);
    await page.screenshot({ path: file, type: 'png', clip: { x: 0, y: 0, width: W, height: H } });
    done++;
    if (done % 25 === 0 || done === list.length) {
      const el = (Date.now() - t0) / 1000;
      console.log(`[w${label}] ${done}/${list.length} frames, ${(el / done).toFixed(2)} s/frame, eta ${((list.length - done) * el / done / 60).toFixed(1)} min`);
    }
  }
  await page.close();
}

(async () => {
  const browser = await chromium.launch({ headless: true, args: CHROME_ARGS });
  const DUR = await (async () => { const { page } = await openPage(browser); const d = await page.evaluate(() => window.__spook.DUR); await page.close(); return d; })();

  if (STILLS) {
    const times = STILLS.split(',').map(Number);
    const list = times.map(t => ({ idx: 0, t, file: path.join(OUT, `still_${t.toFixed(2).replace('.', '_')}.png`) }));
    for (const l of list) { try { fs.unlinkSync(l.file); } catch {} }
    await renderFrames(browser, list, 0);
    console.log('stills written to', OUT);
    await browser.close();
    return;
  }

  const total = Math.ceil(DUR * FPS);
  const start = parseInt(opt('start', '0'), 10), end = Math.min(total, parseInt(opt('end', String(total)), 10));
  const all = [];
  for (let i = start; i < end; i++) all.push({ idx: i, t: i / FPS, file: path.join(framesDir, `f_${String(i).padStart(5, '0')}.png`) });
  console.log(`rendering ${all.length} frames at ${W}x${H} @ ${FPS}fps with ${WORKERS} workers -> ${framesDir}`);
  const buckets = Array.from({ length: WORKERS }, () => []);
  all.forEach((f, i) => buckets[i % WORKERS].push(f));
  await Promise.all(buckets.map((b, i) => renderFrames(browser, b, i)));

  // soundtrack
  const wav = path.join(OUT, 'soundtrack.wav');
  if (!fs.existsSync(wav)) {
    console.log('rendering soundtrack...');
    const { page } = await openPage(browser);
    const b64 = await page.evaluate(() => window.__spook.audio(44100));
    fs.writeFileSync(wav, Buffer.from(b64, 'base64'));
    await page.close();
    console.log('soundtrack written:', (fs.statSync(wav).size / 1e6).toFixed(1), 'MB');
  }
  await browser.close();

  if (end === total && start === 0) {
    const mp4 = path.join(OUT, 'spooktober.mp4');
    console.log('encoding', mp4);
    const r = spawnSync('ffmpeg', ['-y', '-framerate', String(FPS), '-i', path.join(framesDir, 'f_%05d.png'), '-i', wav,
      '-c:v', 'libx264', '-preset', 'slow', '-crf', '17', '-pix_fmt', 'yuv420p', '-profile:v', 'high', '-level', '4.1',
      '-c:a', 'aac', '-b:a', '192k', '-ar', '44100', '-movflags', '+faststart', '-shortest', mp4], { stdio: 'inherit' });
    if (r.status !== 0) process.exit(r.status);
    console.log('done:', mp4);
  }
})().catch(e => { console.error(e); process.exit(1); });
