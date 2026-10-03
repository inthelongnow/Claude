#!/usr/bin/env node
// Renders the Hallowlight film (index.html?film) to an MP4 with its synthesized soundtrack.
//
//   npm i playwright && npx playwright install chromium
//   node record.mjs                      # 1080x1080, 30 fps, high quality -> hallowlight.mp4
//   node record.mjs --size 720 --quality 2 --jobs 2 --out preview.mp4
//
// Frames are rendered by headless Chromium (software WebGL is fine, just slow) and cached in --work,
// so an interrupted render picks up where it stopped. ffmpeg must be on PATH.
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath, pathToFileURL } from 'node:url';

const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || 'playwright');

const argv = process.argv.slice(2);
const opt = (name, def) => {
  const i = argv.indexOf('--' + name);
  return i >= 0 ? argv[i + 1] : def;
};
const here = path.dirname(fileURLToPath(import.meta.url));
const size = +opt('size', 1080);
const quality = +opt('quality', 3);
const jobs = +opt('jobs', 2);
const out = path.resolve(opt('out', path.join(here, 'hallowlight.mp4')));
const work = path.resolve(opt('work', path.join(os.tmpdir(), `hallowlight-${size}-q${quality}`)));
const only = opt('frames', '');            // e.g. "0-90" to render part of the film
fs.mkdirSync(work, { recursive: true });

const url = pathToFileURL(path.join(here, 'index.html')).href + `?film&w=${size}&h=${size}&q=${quality}`;
const launch = () => chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
async function open(browser) {
  const page = await browser.newPage({ viewport: { width: size, height: size } });
  page.on('pageerror', e => console.error('page error:', e.message));
  await page.goto(url);
  await page.waitForFunction(() => window.__hlReady === true, null, { timeout: 180000 });
  return page;
}

const browsers = await Promise.all(Array.from({ length: jobs }, launch));
const pages = await Promise.all(browsers.map(open));
const info = await pages[0].evaluate(() => ({ fps: window.__hl.fps, frames: window.__hl.frames, duration: window.__hl.duration }));
let [first, last] = [0, info.frames - 1];
if (only) [first, last] = only.split('-').map(Number);
console.log(`Hallowlight: ${info.frames} frames at ${info.fps} fps, ${size}x${size}, quality ${quality}, ${jobs} job(s)`);

const name = i => path.join(work, `f${String(i).padStart(5, '0')}.png`);
const todo = [];
for (let i = first; i <= last; i++) if (!fs.existsSync(name(i))) todo.push(i);
let done = 0;
const t0 = Date.now();
await Promise.all(pages.map(async (page, k) => {
  for (let j = k; j < todo.length; j += jobs) {
    const i = todo[j];
    const data = await page.evaluate(n => window.__hl.frame(n), i);
    fs.writeFileSync(name(i), Buffer.from(data.slice(data.indexOf(',') + 1), 'base64'));
    done++;
    if (done % 10 === 0 || done === todo.length) {
      const per = (Date.now() - t0) / done / 1000;
      console.log(`  ${done}/${todo.length} frames, ${per.toFixed(2)} s/frame, ~${Math.round(((todo.length - done) * per) / 60)} min left`);
    }
  }
}));

const wav = path.join(work, 'audio.wav');
if (!fs.existsSync(wav)) {
  const b64 = await pages[0].evaluate(() => window.__hl.audio());
  fs.writeFileSync(wav, Buffer.from(b64, 'base64'));
}
await Promise.all(browsers.map(b => b.close()));

if (only) { console.log(`Rendered frames ${first}-${last} into ${work}`); process.exit(0); }
const ff = spawnSync('ffmpeg', [
  '-y', '-hide_banner', '-loglevel', 'error',
  '-framerate', String(info.fps), '-i', path.join(work, 'f%05d.png'),
  '-i', wav,
  '-c:v', 'libx264', '-preset', 'slow', '-crf', '18', '-tune', 'film',
  '-pix_fmt', 'yuv420p', '-profile:v', 'high', '-level', '4.1',
  '-c:a', 'aac', '-b:a', '192k', '-ar', '48000',
  '-movflags', '+faststart', '-shortest', out,
], { stdio: 'inherit' });
if (ff.status !== 0) process.exit(ff.status || 1);
console.log(`Wrote ${out}`);
