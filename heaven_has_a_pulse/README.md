# Heaven Has a Pulse

A ~68-second cosmic art film: a dark nebula, a point of light that becomes an
eclipse halo, a heartbeat, then a slow, swung, primal groove with tribal rings
and rising embers, a heavenly climax, a supernova, and one surviving star.

Everything — picture and score — is generated from code. No stock footage,
no samples, no API keys.

| File | What it does |
| --- | --- |
| `timeline.py` | The shared beat map (84 BPM, swung 16ths). Sections, drum hits, bassline, lyrics. Audio and picture both read it, so every flash lands on its beat. |
| `audio.py` | Synthesizes the score with numpy: detuned pads, formant "choir", heartbeat kick, tribal toms, reverb-soaked snaps, sultry D-minor bass, sidechain pump. |
| `render.py` | Draws every frame: domain-warped nebula, parallax stars, eclipse corona and god rays, tribal rings, embers, supernova, bloom, filmic tonemap, grain, camera sway, letterbox type. |
| `fonts/` | Cinzel and Cormorant Garamond Italic (SIL Open Font License, from Google Fonts). |

## Render

```bash
pip install numpy scipy pillow imageio-ffmpeg
cd heaven_has_a_pulse
python3 audio.py score.wav
python3 render.py score.wav ../heaven_has_a_pulse.mp4
```

Takes roughly 6–8 minutes on 4 cores at 1280×720, 24 fps.

## Tweaking

- Tempo / swing: `BPM` and `SWING` in `timeline.py`.
- Words on screen: `LYRICS` in `timeline.py`.
- Colours per section: `PALETTES` in `render.py`.
- Swagger (camera sway amount): `roll` in `render.frame`.
