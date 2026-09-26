"""Shared musical timeline for "Heaven Has a Pulse".

Both the score (audio.py) and the picture (render.py) read from here, so every
visual pulse lands exactly on the beat that caused it.
"""

BPM = 84
BEAT = 60.0 / BPM
BAR = 4 * BEAT
SWING = 0.60  # 0.5 = straight 16ths; higher = lazier, more swagger

# Sections, in bars
INTRO = (0, 4)     # void, breath, first light
HEART = (4, 8)     # heartbeat arrives
GROOVE = (8, 16)   # primal groove: toms, snaps, bass, embers
CLIMAX = (16, 20)  # heaven opens
OUTRO = (20, 22)   # supernova, afterglow, title

TAIL = 5.0
DURATION = OUTRO[1] * BAR + TAIL


def t_at(bar, beat=0, six=0):
    """Time in seconds of a swung 16th-note position."""
    s = SWING * 0.5
    sub = [0.0, s, 0.5, 0.5 + s][six]
    return bar * BAR + (beat + sub) * BEAT


def in_bars(bars):
    return range(bars[0], bars[1])


# Harmony: (bass midi root, pad chord midi notes)
DM9 = (38, [50, 53, 57, 60, 64])
BBMAJ9 = (34, [46, 50, 53, 57, 60])
GM9 = (31, [43, 46, 50, 53, 57])
A7B9 = (33, [45, 49, 52, 55, 58])


def chord_for_bar(bar):
    if bar < GROOVE[0]:
        return DM9
    if bar < CLIMAX[0]:
        return [DM9, BBMAJ9, GM9, A7B9][((bar - GROOVE[0]) // 2) % 4]
    if bar < OUTRO[0]:
        return [DM9, BBMAJ9, GM9, A7B9][(bar - CLIMAX[0]) % 4]
    return DM9


def heartbeats():
    """(time, velocity) lub-dub pairs on beats 1 and 3 during HEART."""
    ev = []
    for bar in in_bars(HEART):
        for beat in (0, 2):
            t = t_at(bar, beat)
            ev.append((t, 1.0))
            ev.append((t + 0.24, 0.6))
    return ev


def kicks():
    ev = []
    for bar in range(GROOVE[0], OUTRO[0]):
        pat = [(0, 0, 1.0), (1, 3, 0.7), (2, 2, 0.9)]
        if bar % 2 == 1:
            pat.append((3, 3, 0.6))
        if bar >= CLIMAX[0]:
            pat.append((2, 0, 0.8))
        ev += [(t_at(bar, b, s), v) for b, s, v in pat]
    return ev


def snaps():
    ev = []
    for bar in range(HEART[0] + 2, OUTRO[0]):
        for beat in (1, 3):
            ev.append((t_at(bar, beat), 1.0))
    return ev


def toms():
    """(time, velocity, pitch) — pitch 0 = low floor tom, 1 = mid."""
    ev = []
    for bar in in_bars(GROOVE):
        pat = [(0, 2, 0), (1, 2, 0)]
        if bar % 2 == 1:
            pat += [(2, 3, 1), (3, 0, 1), (3, 2, 0)]
        ev += [(t_at(bar, b, s), 0.8, p) for b, s, p in pat]
    for bar in in_bars(CLIMAX):
        for beat in range(4):
            for six in (0, 2):
                p = 1 if (beat + six // 2) % 2 else 0
                ev.append((t_at(bar, beat, six), 0.65 + 0.3 * (six == 0), p))
    return ev


def shakers():
    ev = []
    for bar in range(GROOVE[0], OUTRO[0]):
        for beat in range(4):
            for six in range(4):
                v = [0.45, 0.25, 0.8, 0.3][six]
                ev.append((t_at(bar, beat, six), v))
    return ev


def bass_notes():
    """(start, duration, midi, velocity)."""
    ev = []
    for bar in range(GROOVE[0], OUTRO[0]):
        root = chord_for_bar(bar)[0]
        pat = [(0, 0, 0.72, 0, 1.0), (1, 3, 0.25, 0, 0.7),
               (2, 2, 0.45, 12, 0.85), (3, 2, 0.4, 7, 0.75)]
        for b, s, dur, iv, v in pat:
            ev.append((t_at(bar, b, s), dur * BEAT, root + iv, v))
    return ev


IMPACT = OUTRO[0] * BAR  # the supernova


LYRICS = [
    # (start, end, text, style)
    (2.2, 8.4, "before the light", "italic"),
    (8.2, 14.5, "there was a rhythm", "italic"),
    (t_at(10), t_at(12), "heaven moves slow", "italic"),
    (t_at(12, 2), t_at(14, 2), "like it knows you're watching", "italic"),
    (IMPACT + 1.4, DURATION - 0.3, "HEAVEN HAS A PULSE", "title"),
]
