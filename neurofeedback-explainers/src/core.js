/* Shared helpers: routing between sections, theme, canvases, and the simulated EEG used by every figure. */
(() => {
  'use strict';
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const root = document.documentElement;
  const NF = (window.NF = { $, $$, mods: {}, current: null });

  // ---- small utilities -------------------------------------------------
  NF.rng = seed => () => {
    seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
  NF.clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  NF.reduced = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  const store = {
    get(k) { try { return localStorage.getItem('nfg.' + k); } catch (e) { return null; } },
    set(k, v) { try { localStorage.setItem('nfg.' + k, v); } catch (e) { /* private window: fine */ } },
  };
  NF.store = store;
  { const th = store.get('theme'); if (th && !root.dataset.theme) root.dataset.theme = th; }
  // Web fonts load without holding up the page; offline, the fallback fonts are used.
  $$('link[data-async]').forEach(l => { const on = () => { l.media = 'all'; }; if (l.sheet) on(); else l.addEventListener('load', on); });
  // Source links open in a new tab so the guide stays put during a session.
  document.addEventListener('click', e => { const a = e.target.closest?.('a[href^="http"]'); if (a) { a.target = '_blank'; a.rel = 'noopener'; } });

  // ---- theme tokens for canvas drawing ----------------------------------
  let tokens = {};
  NF.css = name => (tokens[name] ??= getComputedStyle(root).getPropertyValue(name).trim());
  NF.font = (px, weight = 400) => `${weight} ${px}px ${NF.css('--font-body') || 'system-ui, sans-serif'}`;
  const themeChanged = () => { tokens = {}; NF.current?.redraw?.(); };
  new MutationObserver(themeChanged).observe(root, { attributes: true, attributeFilter: ['data-theme', 'class'] });
  if (window.matchMedia) matchMedia('(prefers-color-scheme: dark)').addEventListener?.('change', themeChanged);
  if (document.fonts?.ready) document.fonts.ready.then(themeChanged);

  // ---- canvas + animation ------------------------------------------------
  // draw(ctx, w, h) works in CSS pixels; the helper handles device pixel ratio and resizing.
  NF.canvas = (el, draw) => {
    const ctx = el.getContext('2d');
    let w = 0, h = 0, dpr = 1;
    const fit = () => {
      const r = el.getBoundingClientRect();
      if (!r.width || !r.height) return false;
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      w = r.width; h = r.height;
      el.width = Math.round(w * dpr); el.height = Math.round(h * dpr);
      return true;
    };
    const api = {
      el, ctx,
      render() {
        if (!w && !fit()) return;
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        ctx.clearRect(0, 0, w, h);
        draw(ctx, w, h);
      },
    };
    new ResizeObserver(() => { if (fit()) api.render(); }).observe(el);
    return api;
  };

  // A clock that only advances while playing, so "Pause" freezes every trace in place.
  NF.loop = tick => {
    let raf = 0, last = 0, t = 0, playing = !NF.reduced;
    const frame = now => {
      raf = requestAnimationFrame(frame);
      const dt = last ? Math.min(0.05, (now - last) / 1000) : 0;
      last = now;
      if (playing) t += dt;
      tick(playing ? dt : 0, t, dt);
    };
    return {
      start() { if (!raf) { last = 0; raf = requestAnimationFrame(frame); } },
      stop() { cancelAnimationFrame(raf); raf = 0; },
      get playing() { return playing; },
      set playing(v) { playing = v; },
      get t() { return t; },
    };
  };
  // Wire a Pause/Play button to a loop.
  NF.playButton = (btn, loop) => {
    const paint = () => { btn.textContent = loop.playing ? 'Pause' : 'Play'; btn.setAttribute('aria-pressed', String(!loop.playing)); };
    btn.addEventListener('click', () => { loop.playing = !loop.playing; paint(); });
    paint();
  };
  // Segmented single-choice buttons: container holds <button data-v="...">.
  NF.choice = (box, onPick, initial) => {
    const btns = $$('button[data-v]', box);
    const set = v => { btns.forEach(b => b.setAttribute('aria-pressed', String(b.dataset.v === String(v)))); };
    box.addEventListener('click', e => { const b = e.target.closest('button[data-v]'); if (!b) return; set(b.dataset.v); onPick(b.dataset.v, b); });
    if (initial !== undefined) set(initial);
    return { set };
  };

  // ---- the simulated EEG --------------------------------------------------
  // Six bands. Edges vary a little between labs and software; these are the common textbook ones.
  NF.BANDS = [
    { id: 'isf',   name: 'Infra-slow', hz: 'below 0.1 Hz', lo: 0.012, hi: 0.09, amp: 1.25, c: '--b-isf' },
    { id: 'delta', name: 'Delta',      hz: '1–4 Hz',       lo: 1,     hi: 4,    amp: 1.0,  c: '--b-delta' },
    { id: 'theta', name: 'Theta',      hz: '4–8 Hz',       lo: 4,     hi: 8,    amp: 0.72, c: '--b-theta' },
    { id: 'alpha', name: 'Alpha',      hz: '8–12 Hz',      lo: 8,     hi: 12,   amp: 0.9,  c: '--b-alpha' },
    { id: 'beta',  name: 'Beta',       hz: '12–30 Hz',     lo: 13,    hi: 28,   amp: 0.46, c: '--b-beta' },
    { id: 'gamma', name: 'Gamma',      hz: '30 Hz and up', lo: 32,    hi: 44,   amp: 0.24, c: '--b-gamma' },
  ];
  NF.band = id => NF.BANDS.find(b => b.id === id);
  // Each band is three nearby sine waves whose strength waxes and wanes, which gives the bursty look of real rhythms.
  NF.synth = (seed = 11) => {
    const r = NF.rng(seed);
    const comps = NF.BANDS.map(b => [0, 1, 2].map(i => ({
      f: b.lo + (b.hi - b.lo) * (0.15 + 0.33 * i + 0.08 * r()),
      p: r() * 6.283,
      ef: (0.07 + 0.2 * r()) * (b.id === 'isf' ? 0.04 : 1),
      ep: r() * 6.283,
    })));
    const val = (k, t) => { let s = 0; for (const c of comps[k]) s += (0.55 + 0.45 * Math.sin(6.283 * c.ef * t + c.ep)) * Math.sin(6.283 * c.f * t + c.p); return s / 2.1; };
    const env = (k, t) => { let s = 0; for (const c of comps[k]) s += 0.55 + 0.45 * Math.sin(6.283 * c.ef * t + c.ep); return s / 2.4; };
    return { val, env };
  };
  // Draw one band (index k) across a time window ending at t. Rhythms too fast to resolve at this
  // zoom are drawn as their envelope instead of a misleading jagged line.
  NF.drawBand = (ctx, w, h, syn, k, t, win, level, color, o = {}) => {
    const b = NF.BANDS[k], mid = h / 2, A = (o.scale ?? 0.42) * h * b.amp * level;
    const pxPerCycle = w / (win * b.hi);
    ctx.lineWidth = o.width ?? 2; ctx.lineJoin = 'round'; ctx.lineCap = 'round'; ctx.strokeStyle = color; ctx.fillStyle = color;
    if (pxPerCycle < 4) {
      const n = Math.max(2, Math.round(w / 3));
      ctx.beginPath();
      for (let i = 0; i <= n; i++) { const u = i / n, e = syn.env(k, t - win + win * u) * A; i ? ctx.lineTo(u * w, mid - e) : ctx.moveTo(u * w, mid - e); }
      for (let i = n; i >= 0; i--) { const u = i / n, e = syn.env(k, t - win + win * u) * A; ctx.lineTo(u * w, mid + e); }
      ctx.closePath(); ctx.globalAlpha = o.ghost ? 0.25 : 0.55; ctx.fill(); ctx.globalAlpha = 1;
      return;
    }
    const n = Math.round(w * 2);
    ctx.beginPath();
    for (let i = 0; i <= n; i++) { const u = i / n, y = mid - syn.val(k, t - win + win * u) * A; i ? ctx.lineTo(u * w, y) : ctx.moveTo(u * w, y); }
    ctx.stroke();
  };
  // The summed signal: what one sensor actually records.
  NF.drawSum = (ctx, w, h, syn, t, win, levels, color, o = {}) => {
    const mid = h / 2, sc = (o.scale ?? 0.2) * h, n = Math.round(w * 2);
    ctx.lineWidth = o.width ?? 1.6; ctx.lineJoin = 'round'; ctx.strokeStyle = color;
    ctx.beginPath();
    for (let i = 0; i <= n; i++) {
      const u = i / n, tt = t - win + win * u; let s = 0;
      for (let k = 0; k < NF.BANDS.length; k++) if (levels[k] > 0.001) s += levels[k] * NF.BANDS[k].amp * syn.val(k, tt);
      const y = mid - s * sc; i ? ctx.lineTo(u * w, y) : ctx.moveTo(u * w, y);
    }
    ctx.stroke();
  };

  // ---- sections and navigation ------------------------------------------
  NF.register = (id, mod) => { NF.mods[id] = mod; };
  const sections = () => $$('section.mod');
  const ids = () => sections().map(s => s.id);
  const show = id => {
    if (!ids().includes(id)) id = ids()[0];
    if (NF.current && NF.current.id !== id) NF.current.stop?.();
    sections().forEach(s => { s.hidden = s.id !== id; });
    $$('.rail a').forEach(a => a.getAttribute('href') === '#' + id ? a.setAttribute('aria-current', 'page') : a.removeAttribute('aria-current'));
    const sec = document.getElementById(id), mod = NF.mods[id] || {};
    if (!mod._ready) { mod.init?.(sec); mod._ready = true; }
    mod.id = id; NF.current = mod;
    mod.start?.();
    const i = ids().indexOf(id);
    $('#where').textContent = `${sec.dataset.group} · ${i + 1} of ${ids().length}`;
    $('#prev').disabled = i === 0; $('#next').disabled = i === ids().length - 1;
    window.scrollTo(0, 0);
  };
  const go = d => { const all = ids(), i = all.indexOf(NF.current?.id); const n = all[i + d]; if (n) location.hash = n; };
  NF.go = id => { location.hash = id; };

  const buildRail = () => {
    const nav = $('.rail nav'); let grp = null, box = null;
    sections().forEach(s => {
      if (s.dataset.group !== grp) { grp = s.dataset.group; box = document.createElement('div'); const g = document.createElement('div'); g.className = 'grp'; g.textContent = grp; box.append(g); nav.append(box); }
      const a = document.createElement('a'); a.href = '#' + s.id; a.textContent = s.dataset.nav; box.append(a);
    });
  };

  const boot = () => {
    buildRail();
    $('#prev').addEventListener('click', () => go(-1));
    $('#next').addEventListener('click', () => go(1));
    $('#menuBtn').addEventListener('click', () => { const off = root.classList.toggle('nomenu'); $('#menuBtn').setAttribute('aria-pressed', String(off)); store.set('nomenu', off ? '1' : ''); });
    $('#sizeBtn').addEventListener('click', () => { const on = root.classList.toggle('big'); $('#sizeBtn').setAttribute('aria-pressed', String(on)); store.set('big', on ? '1' : ''); });
    $('#themeBtn').addEventListener('click', () => {
      const dark = root.dataset.theme ? root.dataset.theme === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches;
      root.dataset.theme = dark ? 'light' : 'dark'; store.set('theme', root.dataset.theme);
    });
    $('#fullBtn').addEventListener('click', () => {
      const el = document.documentElement;
      if (document.fullscreenElement) document.exitFullscreen?.();
      else (el.requestFullscreen || el.webkitRequestFullscreen)?.call(el)?.catch?.(() => {});
    });
    if (store.get('big')) { root.classList.add('big'); $('#sizeBtn').setAttribute('aria-pressed', 'true'); }
    if (store.get('nomenu')) { root.classList.add('nomenu'); $('#menuBtn').setAttribute('aria-pressed', 'true'); }
    addEventListener('keydown', e => {
      if (e.target.closest('input, select, textarea') || e.metaKey || e.ctrlKey || e.altKey) return;
      if (e.key === 'ArrowRight') go(1); else if (e.key === 'ArrowLeft') go(-1);
    });
    addEventListener('hashchange', () => show(location.hash.slice(1)));
    document.addEventListener('visibilitychange', () => { if (document.hidden) NF.current?.stop?.(); else NF.current?.start?.(); });
    show(location.hash.slice(1));
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();
})();
