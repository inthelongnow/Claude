"""Picture for "Heaven Has a Pulse" — every frame drawn procedurally with numpy.

Layers, back to front: domain-warped nebula smoke, a parallax starfield,
an eclipse halo with corona and god rays, tribal rings that flash on the
snaps, rising embers, the supernova, then bloom, filmic tonemap, grain,
a swaggering camera and letterboxed type.
"""

import math
import os
import subprocess
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy.ndimage import gaussian_filter, map_coordinates

import timeline as T

W, H = 1280, 720
FPS = 24
NW, NH = 480, 270
LETTERBOX = 92
CX, CY = W / 2, H / 2 - 8
HERE = os.path.dirname(os.path.abspath(__file__))

rng = np.random.default_rng(1618)


# ---------------------------------------------------------------- helpers

def smooth(a, b, x):
    x = np.clip((x - a) / (b - a), 0, 1)
    return x * x * (3 - 2 * x)


def sec(bar):
    return bar * T.BAR


def pulse(t, events, decay):
    p = 0.0
    for te, v, *_ in events:
        if te <= t < te + decay * 6:
            p = max(p, v * math.exp(-(t - te) / decay))
    return p


def tileable_noise(size, seed):
    r = np.random.default_rng(seed)
    out = np.zeros((size, size))
    amp, total = 1.0, 0.0
    for sigma in (48, 24, 12, 6, 3):
        layer = gaussian_filter(r.standard_normal((size, size)), sigma, mode="wrap")
        out += amp * layer / layer.std()
        total += amp
        amp *= 0.55
    out /= total
    return (out - out.min()) / (out.max() - out.min())


TEX = [tileable_noise(512, s) for s in (11, 22, 33)]


def sample(tex, u, v):
    return map_coordinates(tex, [v * 200 + 256, u * 200 + 256], order=1, mode="grid-wrap")


# ---------------------------------------------------------------- grids

ny, nx = np.mgrid[0:NH, 0:NW].astype(np.float32)
NU = (nx - NW / 2) / NH
NV = (ny - (NH / 2 - 8 * NH / H)) / NH

gy, gx = np.mgrid[0:H, 0:W].astype(np.float32)
DX, DY = gx - CX, gy - CY
R = np.sqrt(DX * DX + DY * DY)
THETA = np.arctan2(DY, DX)
VIGNETTE = 1 - 0.42 * ((gx - W / 2) ** 2 / (W / 2) ** 2 + (gy - H / 2) ** 2 / (H / 2) ** 2) * 0.55


# ---------------------------------------------------------------- look / palette

def col(*c):
    return np.array(c, dtype=np.float32)


PALETTES = [
    # time, cold, mid, hot
    (0.0, col(.02, .03, .12), col(.20, .08, .42), col(.95, .65, .40)),
    (sec(T.HEART[0]), col(.03, .02, .10), col(.42, .06, .38), col(1.0, .50, .32)),
    (sec(T.GROOVE[0]), col(.06, .01, .03), col(.58, .08, .14), col(1.0, .58, .18)),
    (sec(T.CLIMAX[0]), col(.07, .05, .15), col(.55, .32, .58), col(1.0, .90, .70)),
    (T.IMPACT, col(.02, .02, .07), col(.22, .12, .36), col(.95, .78, .55)),
]


def palette(t):
    for i in range(len(PALETTES) - 1, -1, -1):
        if t >= PALETTES[i][0]:
            break
    if i == len(PALETTES) - 1:
        return PALETTES[i][1:]
    a, b = PALETTES[i], PALETTES[i + 1]
    k = float(smooth(b[0] - 2.5, b[0] + 0.5, t))
    return [a[j] * (1 - k) + b[j] * k for j in (1, 2, 3)]


# Precompute camera travel through the starfield (speed rises in the climax)
_ts = np.arange(0, T.DURATION + 1, 1 / 240)
_speed = (0.010 + 0.02 * smooth(sec(T.GROOVE[0]), sec(T.CLIMAX[0]), _ts)
          + 0.16 * smooth(sec(T.CLIMAX[0] + 2), T.IMPACT, _ts) * (_ts < T.IMPACT)
          + 0.20 * np.exp(-np.maximum(_ts - T.IMPACT, 0) * 1.4) * (_ts >= T.IMPACT))
_camz = np.cumsum(_speed) / 240


def cam_z(t):
    return float(np.interp(t, _ts, _camz))


# ---------------------------------------------------------------- starfield

NS = 3200
SX = rng.uniform(-1.8, 1.8, NS).astype(np.float32)
SY = rng.uniform(-1.1, 1.1, NS).astype(np.float32)
SZ = rng.uniform(0, 1, NS).astype(np.float32)
SMAG = (rng.pareto(2.2, NS) * 0.25 + 0.2).clip(0, 3).astype(np.float32)
STW = rng.uniform(1, 4, NS).astype(np.float32)
STP = rng.uniform(0, 6.28, NS).astype(np.float32)
STINT = np.where(rng.uniform(0, 1, NS) < 0.3, 0, 1)
SCOL = np.array([[0.75, 0.85, 1.0], [1.0, 0.85, 0.65]], dtype=np.float32)[STINT]


def splat(buf, x, y, w, colors):
    """Bilinear additive splat of points into an (H, W, 3) buffer."""
    ok = (x >= 0) & (x < W - 1) & (y >= 0) & (y < H - 1) & (w > 1e-4)
    x, y, w, colors = x[ok], y[ok], w[ok], colors[ok]
    x0, y0 = np.floor(x).astype(np.int64), np.floor(y).astype(np.int64)
    fx, fy = x - x0, y - y0
    for dx, dy, ww in ((0, 0, (1 - fx) * (1 - fy)), (1, 0, fx * (1 - fy)),
                       (0, 1, (1 - fx) * fy), (1, 1, fx * fy)):
        idx = (y0 + dy) * W + (x0 + dx)
        for c in range(3):
            buf[..., c] += np.bincount(idx, weights=w * ww * colors[:, c],
                                       minlength=H * W).reshape(H, W)


def stars(t, strength):
    buf = np.zeros((H, W, 3), np.float32)
    if strength <= 0:
        return buf
    speed = float(np.interp(t, _ts, _speed))
    trail = int(np.clip(speed * 60, 1, 14))
    f = H * 0.42
    for j in range(trail):
        tz = cam_z(t - j * 0.012)
        z = (SZ - tz) % 1.0 * 0.97 + 0.03
        x = CX + SX / z * f * 0.5
        y = CY + SY / z * f * 0.5
        fade = smooth(0.03, 0.12, z) * (1 - smooth(0.75, 1.0, z))
        tw = 0.65 + 0.35 * np.sin(t * STW + STP)
        b = SMAG * fade * tw * (1.15 - z) ** 2 * strength * (1 - j / trail) / trail ** 0.5
        splat(buf, x, y, b * 9.0, SCOL)
    return gaussian_filter(buf, (0.7, 0.7, 0))


# ---------------------------------------------------------------- embers

NE = 520
E_X = rng.uniform(-0.1, 1.1, NE) * W
E_RATE = rng.uniform(0.05, 0.16, NE)
E_PH = rng.uniform(0, 1, NE)
E_SW = rng.uniform(10, 60, NE)
E_WF = rng.uniform(0.3, 1.2, NE)
E_MAG = rng.uniform(0.3, 1.0, NE) ** 2
E_BOKEH = rng.uniform(0, 1, NE) < 0.08
E_COL = np.stack([np.ones(NE), rng.uniform(0.3, 0.6, NE), rng.uniform(0.05, 0.2, NE)], 1)


def embers(t, strength):
    buf = np.zeros((H, W, 3), np.float32)
    bok = np.zeros((H, W, 3), np.float32)
    if strength <= 0:
        return buf
    age = (t * E_RATE + E_PH) % 1.0
    y = H * (1.08 - age * 1.25)
    x = E_X + E_SW * np.sin(t * E_WF + E_PH * 20) + 30 * np.sin(age * 5 + E_PH * 9)
    flick = 0.6 + 0.4 * np.sin(t * 9 * E_WF + E_PH * 40)
    b = E_MAG * np.sin(np.pi * age) ** 1.5 * flick * strength
    splat(buf, x[~E_BOKEH], y[~E_BOKEH], b[~E_BOKEH] * 10.0, E_COL[~E_BOKEH])
    splat(bok, x[E_BOKEH], y[E_BOKEH], b[E_BOKEH] * 90.0, E_COL[E_BOKEH])
    return gaussian_filter(buf, (1.1, 1.1, 0)) + gaussian_filter(bok, (7, 7, 0))


# ---------------------------------------------------------------- nebula

def nebula(t, amount):
    if amount <= 0:
        return np.zeros((H, W, 3), np.float32)
    a = 0.015 * t
    zoom = 1.0 - 0.0045 * t
    u = (NU * math.cos(a) - NV * math.sin(a)) * zoom
    v = (NU * math.sin(a) + NV * math.cos(a)) * zoom
    wu = sample(TEX[1], u * 1.3 + 0.020 * t, v * 1.3 + 0.008 * t) - 0.5
    wv = sample(TEX[2], u * 1.3 - 0.012 * t, v * 1.3 + 0.017 * t) - 0.5
    d = sample(TEX[0], u + 0.9 * wu + 0.006 * t, v + 0.9 * wv - 0.004 * t)
    fil = sample(TEX[2], u * 3 + 1.7 * wu, v * 3 + 1.7 * wv)

    band = np.exp(-((NV * 0.93 - NU * 0.37) / 0.34) ** 2)
    core = np.exp(-(NU ** 2 + NV ** 2) / 0.10)
    shape = (0.25 + 0.75 * band + 0.9 * core) * np.exp(-(NU ** 2 + NV ** 2) / 1.6)

    dens = smooth(0.30, 0.85, d) ** 1.4 * shape
    hot = smooth(0.55, 0.95, d * 0.7 + fil * 0.45) * shape * (0.35 + 0.8 * core)
    cold, mid, hot_c = palette(t)
    img = (cold[None, None] * (0.6 + 0.4 * shape[..., None])
           + mid[None, None] * dens[..., None] * 0.75
           + hot_c[None, None] * hot[..., None] ** 2 * 0.8) * amount
    img = img.astype(np.float32)
    out = np.empty((H, W, 3), np.float32)
    for c in range(3):
        ch = np.ascontiguousarray(img[..., c])
        out[..., c] = np.asarray(Image.fromarray(ch, "F").resize((W, H), Image.BICUBIC))
    return out


# ---------------------------------------------------------------- halo, rings, supernova

def halo(t, heart_k, kick, snap, tomp):
    buf = np.zeros((H, W, 3), np.float32)
    occ = np.ones((H, W), np.float32)
    after = t - T.IMPACT

    # the first light: a single point being born
    birth = smooth(1.0, sec(T.HEART[0]), t) * (1 - smooth(0, 2.5, after) * 0.0)
    grow = smooth(sec(T.HEART[0]) - 1, sec(T.HEART[0]) + 3.5, t)
    R0 = (8 + 88 * grow + 36 * smooth(sec(T.CLIMAX[0]), T.IMPACT, t)) * (1 + 0.07 * kick)
    if after > 0:
        R0 *= math.exp(-after * 3.0)
    _, _, hot = palette(t)
    white = col(1.0, 0.95, 0.88)
    tint = (hot * 0.6 + white * 0.4)

    point = birth * (1 - grow) * (2.5 / (1 + (R / 5) ** 2) + 0.6 * np.exp(-R / 40))
    if after > 0:
        # the lone star that survives, breathing
        breath = 0.75 + 0.25 * math.sin(after * 1.9)
        point = smooth(0.6, 3.0, after) * breath * (3.0 / (1 + (R / 4) ** 2) + 0.5 * np.exp(-R / 35))
    buf += point[..., None] * tint

    if grow > 0 and after < 0.6:
        g = grow * (1 - smooth(0, 0.6, after))
        wob = (0.65 + 0.2 * np.sin(3 * THETA + 0.5 * t) + 0.15 * np.sin(7 * THETA - 0.33 * t)
               + 0.1 * np.sin(13 * THETA + 1.1 * t))
        out = np.maximum(R - R0, 0)
        ring = np.exp(-((R - R0) / (2.2 + 1.5 * kick)) ** 2) * 3.0
        corona = np.exp(-out / (26 + 30 * kick + 20 * heart_k)) * wob * 1.3 * (R > R0 - 1)
        rays = ((0.5 + 0.5 * np.sin(23 * THETA + 0.21 * t)) *
                (0.5 + 0.5 * np.sin(37 * THETA - 0.13 * t + 1.0)) *
                (0.5 + 0.5 * np.sin(11 * THETA + 0.07 * t + 2.0))) ** 3
        ray_len = 140 + 220 * kick + 200 * smooth(sec(T.CLIMAX[0]), T.IMPACT, t)
        rays = rays * np.exp(-out / ray_len) * (R > R0) * (0.9 + 1.4 * kick)
        light = (ring + corona + rays * 1.1) * g * (0.8 + 0.6 * kick)
        buf += light[..., None] * tint
        occ = smooth(R0 - 1.5, R0 + 1.0, R) * g + (1 - g)
        # the sultry ember glow held inside the dark disc
        inner = np.exp(-((R0 - R) / 10).clip(0) ) * (R < R0) * 0.12 * g
        buf += inner[..., None] * col(1.0, 0.25, 0.08)

    # tribal rings — primal markings orbiting the halo, flashing on snaps and toms
    tribe = smooth(sec(T.GROOVE[0]) - 1, sec(T.GROOVE[0]) + 2, t) * (1 - smooth(-0.3, 0.2, after))
    if tribe > 0:
        bp = (t / T.BEAT) % 2.0
        swing = 0.35 * math.sin(math.pi * bp / 2) ** 3
        specs = [  # radius mult, segments, speed, kind, width
            (1.5, 12, 0.10 + swing * 0.3, "dash", 1.3),
            (1.95, 36, -0.06 - swing * 0.2, "dot", 2.2),
            (2.6, 7, 0.04 + swing * 0.15, "dash", 1.0),
        ]
        for rm, n, spd, kind, wdt in specs:
            Ri = R0 * rm
            ang = THETA * n / (2 * math.pi) + spd * t * n / 6
            if kind == "dash":
                seg = smooth(0.15, 0.3, np.sin(2 * math.pi * ang) * 0.5 + 0.5)
                m = np.exp(-((R - Ri) / wdt) ** 2) * seg
            else:
                fr = (ang % 1.0) - 0.5
                arc = fr * 2 * math.pi * Ri / n
                m = np.exp(-(((R - Ri) ** 2) + arc ** 2) / wdt ** 2)
            glow = m * (0.45 + 1.8 * snap + 0.8 * tomp) * tribe
            buf += glow[..., None] * tint * 1.4

    # supernova: white-out, then a shockwave racing outward
    if -0.05 < after < 8:
        a = max(after, 0)
        flash = math.exp(-a / 0.22) * 6.0 + math.exp(-a / 1.2) * 0.35
        buf += flash * np.exp(-R / (300 + 900 * a))[..., None] * col(1.0, 0.95, 0.9)
        Rs = 40 + 1100 * (1 - math.exp(-a * 0.9))
        wave = np.exp(-((R - Rs) / (6 + 30 * a)) ** 2) * math.exp(-a / 1.6) * 2.2
        buf += wave[..., None] * hot
    return buf, occ


# ---------------------------------------------------------------- type

FONT_I = os.path.join(HERE, "fonts", "Cormorant-Italic.ttf")
FONT_T = os.path.join(HERE, "fonts", "Cinzel.ttf")
_fonts = {}


def font(kind):
    if kind not in _fonts:
        if kind == "italic":
            f = ImageFont.truetype(FONT_I, 50)
            f.set_variation_by_name("Light Italic")
        else:
            f = ImageFont.truetype(FONT_T, 50)
            f.set_variation_by_name("Regular")
        _fonts[kind] = f
    return _fonts[kind]


def draw_text(img, t):
    for start, end, text, style in T.LYRICS:
        if not (start <= t <= end):
            continue
        k = (t - start) / (end - start)
        alpha = float(smooth(0, 1.3, t - start) * (1 - smooth(end - 1.4, end, t)))
        f = font(style)
        if style == "title":
            track = 14 + 10 * k
            y = CY + 78
            color = (242, 212, 150)
        else:
            track = 2 + 6 * k
            y = H - LETTERBOX - 38
            color = (246, 232, 214)
        widths = [f.getlength(ch) for ch in text]
        total = sum(widths) + track * (len(text) - 1)
        layer = Image.new("L", (W, H), 0)
        d = ImageDraw.Draw(layer)
        x = W / 2 - total / 2
        for ch, wch in zip(text, widths):
            d.text((x, y), ch, font=f, fill=255, anchor="ls")
            x += wch + track
        glow = layer.filter(ImageFilter.GaussianBlur(9))
        shade = layer.filter(ImageFilter.GaussianBlur(22))
        img.paste((0, 0, 0), (0, 0), shade.point(lambda p: int(min(255, p * 2.2) * 0.55 * alpha)))
        solid = Image.new("RGB", (W, H), color)
        img.paste(solid, (0, 0), glow.point(lambda p: int(p * 0.55 * alpha)))
        img.paste(solid, (0, 0), layer.point(lambda p: int(p * alpha)))
    return img


# ---------------------------------------------------------------- frame

def aces(x):
    return np.clip((x * (2.51 * x + 0.03)) / (x * (2.43 * x + 0.59) + 0.14), 0, 1)


def frame(i):
    t = i / FPS
    after = t - T.IMPACT
    kick = max(pulse(t, T.heartbeats(), 0.18), pulse(t, T.kicks(), 0.16))
    snap = pulse(t, T.snaps(), 0.12)
    tomp = pulse(t, T.toms(), 0.2)
    heart_k = pulse(t, T.heartbeats(), 0.35)

    neb_amt = (smooth(0.5, 9.0, t) * 0.8 + 0.25 * smooth(sec(T.CLIMAX[0]), T.IMPACT, t)) \
        * (1 + 0.35 * kick) * (1 - 0.8 * smooth(0, 2.5, after) + 0.12 * smooth(3, 8, after))
    star_amt = smooth(0.0, 5.0, t)
    ember_amt = 0.35 * smooth(sec(T.HEART[0] + 2), sec(T.GROOVE[0]), t) \
        + 0.65 * smooth(sec(T.GROOVE[0]), sec(T.GROOVE[0]) + 3, t)
    ember_amt *= (1 + 0.5 * tomp) * (1 - smooth(0.5, 4, after))

    hdr = nebula(t, neb_amt) + stars(t, star_amt)
    light, occ = halo(t, heart_k, kick, snap, tomp)
    hdr = hdr * occ[..., None] + light + embers(t, ember_amt)
    hdr = hdr.astype(np.float32)

    # bloom
    small = np.maximum(hdr[::4, ::4] - 0.6, 0)
    small = gaussian_filter(small, (6, 6, 0))
    bloom = np.empty_like(hdr)
    for c in range(3):
        ch = np.ascontiguousarray(small[..., c])
        bloom[..., c] = np.asarray(Image.fromarray(ch, "F").resize((W, H), Image.BILINEAR))
    hdr += bloom * 0.9

    exposure = 1.25 + 0.35 * smooth(sec(T.CLIMAX[0]), T.IMPACT, t) * (1 - smooth(0, 2.0, after))
    ldr = aces(np.maximum(hdr, 0) * exposure * VIGNETTE[..., None]) ** (1 / 2.2)
    grain = np.random.default_rng(i).standard_normal((H, W, 1)).astype(np.float32) * 0.022
    ldr = np.clip(ldr + grain * (0.4 + ldr), 0, 1)
    img = Image.fromarray((ldr * 255).astype(np.uint8))

    # the camera: slow cosmic drift, then a swaggering sway on the groove
    sway_k = smooth(sec(T.GROOVE[0]) - 1, sec(T.GROOVE[0]) + 3, t) * (1 - smooth(-0.5, 2, after))
    ph = (t - sec(T.GROOVE[0])) / (2 * T.BAR) * 2 * math.pi
    roll = 0.6 * math.sin(t * 0.13) + sway_k * (2.2 * math.sin(ph) + 0.5 * math.sin(2 * ph + 0.6))
    scale = 1.08 + 0.018 * kick + 0.04 * max(0, 1 - abs(after) * 2)
    rad = math.radians(roll)
    ca, sa = math.cos(rad) / scale, math.sin(rad) / scale
    img = img.transform((W, H), Image.AFFINE,
                        (ca, -sa, W / 2 - ca * W / 2 + sa * H / 2,
                         sa, ca, H / 2 - sa * W / 2 - ca * H / 2), Image.BICUBIC)

    img = draw_text(img, t)
    arr = np.asarray(img).copy()
    arr[:LETTERBOX] = 0
    arr[H - LETTERBOX:] = 0
    fade_in = smooth(0, 2.0, t)
    fade_out = 1 - smooth(T.DURATION - 2.2, T.DURATION - 0.2, t)
    return (arr * (fade_in * fade_out)).astype(np.uint8).tobytes()


# ---------------------------------------------------------------- main

def main():
    import imageio_ffmpeg
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    audio, out = sys.argv[1], sys.argv[2]
    n = int(T.DURATION * FPS)
    cmd = [ff, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", audio,
           "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-tune", "grain",
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "256k", "-shortest",
           "-movflags", "+faststart", out]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(os.cpu_count()) as pool:
        for k, data in enumerate(pool.imap(frame, range(n), chunksize=4)):
            proc.stdin.write(data)
            if k % 96 == 0:
                print(f"frame {k}/{n}", flush=True)
    proc.stdin.close()
    proc.wait()
    print("wrote", out)


if __name__ == "__main__":
    main()
