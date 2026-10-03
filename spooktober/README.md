# Spooktober

A 46-second Halloween horror short, rendered by a single GLSL fragment shader, with a soundtrack synthesized on the fly by the Web Audio API.

One HTML file. No models, no textures, no audio samples, no libraries.

- `index.html` is the whole thing. Open it in a browser and click *enter the graveyard*.
- `spooktober.mp4` is the headless render of the same file (1280x720, 30 fps, H.264 + AAC), ready to upload.
- `poster.png` is the title card, for use as the video cover.
- `render.cjs` renders the film frame by frame with headless Chromium and muxes it with ffmpeg.

## What is in the scene

Everything is a signed distance field raymarched in the fragment shader:

- rolling ground with a dirt path, a wrought-iron fence and a stone gate
- a field of procedurally placed tombstones (slabs, crosses, obelisks), each with its own lean
- two dead trees, a haunted house on the hill whose windows light up one by one
- a carved jack-o'-lantern with a flickering candle inside; the lantern light is shadow-traced through the carved holes, so the face is projected onto the ground
- a volumetric ghost with hollow eyes, drifting between the stones
- height fog with animated density, lit by the moon, the lantern, the ghost and the lightning
- a moon with craters, drifting clouds, stars, bats, will-o'-the-wisps, and lightning bolts drawn into the sky

The timeline (camera moves, lightning schedule, ghost path, the pumpkin's scream) lives in JavaScript and drives the shader through uniforms. The same lightning schedule times the thunder in the soundtrack.

## Soundtrack

All synthesized from oscillators and a noise buffer: wind (band-passed noise with wandering filters), a detuned low drone, a church bell made of inharmonic partials, a music-box waltz in E minor that slows and sours, thunder (low-passed noise bursts with a crack for near strikes), an owl, an accelerating heartbeat, and the scream at the cut. The interactive page plays it live; the renderer runs the same graph through an `OfflineAudioContext` and writes a WAV.

## Rendering

```
node render.cjs                 # 1280x720 @ 30 fps -> out/spooktober.mp4
node render.cjs --w 1920 --h 1080
node render.cjs --stills 2,10,30 --out stills
```

The renderer needs Node, Playwright (Chromium), and ffmpeg. It works without a GPU: Chromium falls back to SwiftShader, at a few seconds per 720p frame. Frames already on disk are skipped, so an interrupted render can be resumed.

Add `?t=12.5` to the page URL to render a single still at that time, and `?debug=1` to see a raymarching step-count heatmap.

## Tweet draft

> It's Spooktober, so I asked Claude Code to build something scary.
>
> It wrote a 46-second horror short as ONE fragment shader: fog, moonlight, a haunted house, a ghost, lightning, and a jack-o'-lantern that screams.
>
> Soundtrack synthesized from scratch with Web Audio. One HTML file. Zero assets.

Follow-up for the thread:

> Every tombstone, bat and moon crater is a signed distance field. The thunder is filtered noise timed to the same lightning schedule the shader reads. The whole thing is ~1000 lines in a single index.html, and you can run it live in your browser.
