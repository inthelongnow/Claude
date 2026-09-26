"""Score for "Heaven Has a Pulse" — synthesized from scratch with numpy.

Warm detuned pads, a formant "choir", a heartbeat kick, swung tribal toms,
finger snaps drowned in reverb, and a sultry D-minor bassline.
"""

import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve
import wave

import timeline as T

SR = 44100
N = int(T.DURATION * SR)
rng = np.random.default_rng(7)


def mtof(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def bus():
    return np.zeros((N, 2), dtype=np.float64)


def place(buf, sig, t, gain=1.0, pan=0.0):
    """Mix a mono or stereo signal into a stereo bus at time t."""
    i = int(t * SR)
    if i >= N:
        return
    if sig.ndim == 1:
        l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
        sig = np.stack([sig * l, sig * r], axis=1) * np.sqrt(2)
    n = min(len(sig), N - i)
    buf[i:i + n] += sig[:n] * gain


def filt(x, kind, freq, order=2):
    sos = butter(order, freq, btype=kind, fs=SR, output="sos")
    return sosfilt(sos, x, axis=0)


def ramp_env(n, attack, release):
    e = np.ones(n)
    a, r = int(attack * SR), int(release * SR)
    if a:
        e[:a] = np.linspace(0, 1, a) ** 2
    if r:
        e[-r:] *= np.linspace(1, 0, r) ** 1.5
    return e


def additive(freq, dur, cutoff, detune_cents=(0,), vibrato=0.0, formants=None):
    """Band-limited saw built from harmonics, with a soft low-pass tilt."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for d in detune_cents:
        f = freq * 2 ** (d / 1200)
        ph0 = rng.uniform(0, 2 * np.pi)
        vib = 1 + vibrato * np.sin(2 * np.pi * 5.1 * t + ph0)
        phase = 2 * np.pi * np.cumsum(f * vib) / SR
        k = 1
        while k * f < min(cutoff * 4, 9000):
            a = (1 / k) / (1 + (k * f / cutoff) ** 2)
            if formants:
                a *= sum(g / (1 + ((k * f - fc) / bw) ** 2) for fc, bw, g in formants) + 0.05
            out += a * np.sin(k * phase + ph0 * k)
            k += 1
    return out / len(detune_cents)


# ---------------------------------------------------------------- instruments

def pad_chord(notes, dur, cutoff):
    sig = np.zeros((int(dur * SR), 2))
    for j, m in enumerate(notes):
        pan = -0.6 + 1.2 * j / max(1, len(notes) - 1)
        v = additive(mtof(m), dur, cutoff, detune_cents=(-9, 0, 8))
        l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
        sig[:, 0] += v * l
        sig[:, 1] += v * r
    return sig / len(notes)


VOWEL_AH = [(800, 90, 1.0), (1150, 110, 0.6), (2900, 180, 0.25)]


def choir_chord(notes, dur):
    sig = np.zeros((int(dur * SR), 2))
    for j, m in enumerate(notes):
        for side in (0, 1):
            v = additive(mtof(m), dur, 3000, detune_cents=(-6, 5),
                         vibrato=0.006, formants=VOWEL_AH)
            sig[:, side] += v
    return sig / len(notes)


def kick(vel=1.0, heart=False):
    dur = 0.9 if heart else 0.6
    n = int(dur * SR)
    t = np.arange(n) / SR
    f0, f1 = (90, 38) if heart else (130, 44)
    f = f1 + (f0 - f1) * np.exp(-t * 28)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * (4.5 if heart else 6))
    click = filt(rng.standard_normal(n), "bandpass", [1500, 5000]) * np.exp(-t * 300) * 0.3
    return np.tanh((body + (0 if heart else click)) * 1.6) * vel


def tom(vel, pitch):
    n = int(0.7 * SR)
    t = np.arange(n) / SR
    base = [72, 108][pitch]
    f = base * (1 + 0.6 * np.exp(-t * 18))
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7)
    skin = filt(rng.standard_normal(n), "bandpass", [200, 1200]) * np.exp(-t * 40) * 0.35
    return np.tanh((body + skin) * 1.4) * vel


def snap(vel):
    n = int(0.25 * SR)
    t = np.arange(n) / SR
    noise = filt(rng.standard_normal(n), "bandpass", [1400, 7000])
    env = np.exp(-t * 55) + 0.6 * np.exp(-np.maximum(t - 0.008, 0) * 70) * (t > 0.008)
    return noise * env * vel * 0.9


def shaker(vel):
    n = int(0.09 * SR)
    t = np.arange(n) / SR
    noise = filt(rng.standard_normal(n), "highpass", 6500)
    env = (1 - np.exp(-t * 400)) * np.exp(-t * 60)
    return noise * env * vel * 0.4


def bass(dur, midi, vel):
    n = int((dur + 0.08) * SR)
    t = np.arange(n) / SR
    f = mtof(midi)
    ph = 2 * np.pi * f * t
    sig = np.sin(ph) + 0.35 * np.sin(2 * ph) + 0.12 * np.sin(3 * ph)
    env = ramp_env(n, 0.006, 0.09) * (0.75 + 0.25 * np.exp(-t * 6))
    return np.tanh(sig * env * 1.8) * vel * 0.55


def ping(midi):
    n = int(1.6 * SR)
    t = np.arange(n) / SR
    f = mtof(midi)
    sig = np.sin(2 * np.pi * f * t) + 0.25 * np.sin(2 * np.pi * f * 2.01 * t) * np.exp(-t * 4)
    return sig * np.exp(-t * 3.2) * (1 - np.exp(-t * 300)) * 0.12


def reverb_ir(seconds, damp, seed):
    r = np.random.default_rng(seed)
    n = int(seconds * SR)
    t = np.arange(n) / SR
    ir = r.standard_normal((n, 2)) * np.exp(-t * 6.9 / seconds)[:, None]
    ir = filt(ir, "lowpass", damp)
    ir[: int(0.012 * SR)] = 0  # predelay
    return ir / np.sqrt(np.sum(ir ** 2) / 2)


def reverb(x, ir, mix):
    wet = np.stack([fftconvolve(x[:, c], ir[:, c])[:N] for c in range(2)], axis=1)
    return x * (1 - mix) + wet * mix


# ---------------------------------------------------------------- arrangement

def render():
    pads, choir, drums, snaps_b, bass_b, sparkle, fx = (bus() for _ in range(7))

    # Pads: one chord per bar, cross-faded; brightness follows the arc
    for bar in range(T.OUTRO[1] + 1):
        _, notes = T.chord_for_bar(min(bar, T.OUTRO[1] - 1))
        cutoff = 500 if bar < T.HEART[0] else 900 if bar < T.GROOVE[0] else \
            1300 if bar < T.CLIMAX[0] else 2000 if bar < T.OUTRO[0] else 800
        dur = T.BAR + 1.2
        sig = pad_chord(notes, dur, cutoff) * ramp_env(int(dur * SR), 0.6, 1.2)[:, None]
        g = 0.55 if bar >= T.INTRO[0] else 0
        if bar < 2:
            g *= (bar + 1.5) / 3.5
        if bar < T.HEART[0]:
            g *= 1.5
        if bar >= T.OUTRO[1]:
            g *= 0.5
        place(pads, sig, bar * T.BAR - 0.6 if bar else 0, g)

    # Choir opens heaven in the climax and carries the outro
    for bar in range(T.CLIMAX[0], T.OUTRO[1] + 1):
        _, notes = T.chord_for_bar(min(bar, T.OUTRO[1] - 1))
        dur = T.BAR + 1.5
        sig = choir_chord([m + 12 for m in notes[1:]], dur)
        sig *= ramp_env(len(sig), 0.9, 1.5)[:, None]
        place(choir, sig, bar * T.BAR - 0.7, 0.9 if bar < T.OUTRO[0] else 0.7)

    # Breath: filtered noise swelling in the dark
    for k, t0 in enumerate([0.3, 3.3, 6.2, 9.0]):
        n = int(2.8 * SR)
        x = filt(rng.standard_normal((n, 2)), "bandpass", [180, 900])
        x *= np.sin(np.linspace(0, np.pi, n))[:, None] ** 2
        place(fx, x, t0, 0.18 + 0.03 * k)

    kick_env = np.zeros(N)
    for t, v in T.heartbeats():
        k = kick(v, heart=True)
        place(drums, k, t, 0.75)
        i = int(t * SR)
        m = min(int(0.35 * SR), N - i)
        kick_env[i:i + m] = np.maximum(kick_env[i:i + m], v * np.exp(-np.arange(m) / SR * 9))
    for t, v in T.kicks():
        place(drums, kick(v), t, 0.7)
        i = int(t * SR)
        m = min(int(0.35 * SR), N - i)
        kick_env[i:i + m] = np.maximum(kick_env[i:i + m], v * np.exp(-np.arange(m) / SR * 9))

    for t, v, p in T.toms():
        place(drums, tom(v, p), t, 0.55, pan=-0.35 if p == 0 else 0.35)
    for t, v in T.snaps():
        place(snaps_b, snap(v), t, 0.8, pan=0.15)
    for i, (t, v) in enumerate(T.shakers()):
        place(drums, shaker(v), t, 1.0, pan=0.45 if i % 2 else 0.3)
    for t, d, m, v in T.bass_notes():
        place(bass_b, bass(d, m, v), t, 1.0)

    # Star pings: D-minor pentatonic, sparse at first, denser in heaven
    scale = [74, 77, 79, 81, 84, 86, 89, 93]
    t = 0.8
    while t < T.DURATION - 3:
        place(sparkle, ping(rng.choice(scale)), t, 1.0, pan=rng.uniform(-0.8, 0.8))
        dense = 1.0 if t < T.GROOVE[0] * T.BAR else 0.6 if t < T.CLIMAX[0] * T.BAR else 0.35
        t += rng.uniform(0.5, 1.6) * dense * T.BEAT

    # Riser into the climax, and the supernova impact
    rs, re = T.t_at(T.CLIMAX[0] - 2), T.t_at(T.CLIMAX[0])
    n = int((re - rs) * SR)
    x = rng.standard_normal((n, 2))
    sweep = np.linspace(0, 1, n) ** 2
    x = filt(x, "highpass", 400) * sweep[:, None] ** 1.5
    place(fx, x, rs, 0.25)
    rs2 = T.IMPACT - 2 * T.BAR
    n = int(2 * T.BAR * SR)
    x = filt(rng.standard_normal((n, 2)), "highpass", 800) * (np.linspace(0, 1, n) ** 3)[:, None]
    place(fx, x, rs2, 0.3)

    n = int(6 * SR)
    t_ = np.arange(n) / SR
    boom = np.sin(2 * np.pi * np.cumsum(32 + 60 * np.exp(-t_ * 6)) / SR) * np.exp(-t_ * 0.9)
    boom = np.tanh(boom * 2.2)
    place(fx, boom, T.IMPACT, 0.9)
    place(fx, filt(rng.standard_normal((n, 2)), "lowpass", 2500) * np.exp(-t_ * 2.5)[:, None],
          T.IMPACT, 0.35)

    # Sidechain: pads and choir breathe around every kick — the swagger pump
    duck = 1 - 0.45 * kick_env
    pads *= duck[:, None]
    choir *= (1 - 0.25 * kick_env)[:, None]

    hall = reverb_ir(4.5, 5000, 1)
    room = reverb_ir(1.6, 7000, 2)
    mix = (
        reverb(pads, hall, 0.45) * 0.8
        + reverb(choir, hall, 0.6) * 0.55
        + reverb(sparkle, hall, 0.75) * 0.9
        + reverb(snaps_b, hall, 0.55) * 1.1
        + reverb(drums, room, 0.18) * 0.9
        + bass_b * 0.7
        + reverb(fx, hall, 0.4)
    )

    # Master: gentle glue, soft clip, fade tail
    mix = filt(mix, "highpass", 28)
    peak = np.max(np.abs(mix))
    mix = np.tanh(mix / peak * 1.4) / np.tanh(1.4)
    fade = int(3.0 * SR)
    mix[-fade:] *= np.linspace(1, 0, fade)[:, None] ** 2
    mix *= 0.89 / np.max(np.abs(mix))
    return mix


def write_wav(path, mix):
    data = (mix * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())


if __name__ == "__main__":
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else "score.wav"
    write_wav(out, render())
    print("wrote", out, f"{T.DURATION:.1f}s")
