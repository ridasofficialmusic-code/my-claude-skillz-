"""Paper cut-out renderer: script.json + timing.json -> silent 1080x1920 video (or stills / thumbnails).

Usage:
  python3 render.py script.json WORK_DIR video  [jobs]   -> WORK_DIR/video_silent.mp4
  python3 render.py script.json WORK_DIR still  SECONDS OUT.png
  python3 render.py script.json WORK_DIR thumbs          -> WORK_DIR/thumbnail_16x9.png, thumbnail_9x16.png
See ../reference/scene-spec.md for the element schema.
"""
import json, math, os, random, re, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS, ANIM_FPS = 1080, 1920, 30, 12
HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = {"bold": os.path.join(HERE, "../assets/fonts/BowlbyOne-Regular.ttf"),
         "marker": os.path.join(HERE, "../assets/fonts/PermanentMarker-Regular.ttf")}
C = {"cream": (240, 228, 204), "paper": (250, 246, 236), "mustard": (234, 176, 52), "terra": (205, 92, 62),
     "teal": (38, 128, 128), "navy": (36, 48, 74), "sky": (132, 192, 214), "pink": (232, 150, 140),
     "ink": (30, 28, 30), "red": (200, 52, 48), "green": (70, 150, 90), "night": (28, 34, 58),
     "skin": (238, 190, 150), "blush": (230, 110, 110), "brainpink": (236, 150, 165), "white": (255, 255, 255)}
PAPER = C["paper"]


def col(v):
    if isinstance(v, str): return C[v]
    return tuple(v)


_f = {}
def F(name, size):
    k = (name, max(4, int(size)))
    if k not in _f: _f[k] = ImageFont.truetype(FONTS.get(name, name), k[1])
    return _f[k]


# ---------- paper textures ----------
_rng = np.random.default_rng(1)
_g = _rng.normal(0, 1, (H // 2, W // 2))
GRAIN_BG = np.array(Image.fromarray(((_g * 20) + 128).clip(0, 255).astype(np.uint8)).resize((W, H))
                    .filter(ImageFilter.GaussianBlur(1.2)), np.float32) - 128
_yy = np.linspace(-1, 1, H)[:, None]; _xx = np.linspace(-1, 1, W)[None, :]
VIGNETTE = (1 - 0.18 * (_xx ** 2 + _yy ** 2))[..., None]
GRAIN = Image.fromarray((128 + _rng.normal(0, 14, (H, W))).clip(0, 255).astype(np.uint8))
_bgc = {}


def background(name, size=(W, H)):
    key = (name, size)
    if key in _bgc: return _bgc[key]
    c = np.array(col(name), np.float32)
    g = GRAIN_BG if size == (W, H) else np.array(Image.fromarray((GRAIN_BG + 128).clip(0, 255).astype(np.uint8)).resize(size), np.float32) - 128
    v = VIGNETTE if size == (W, H) else (1 - 0.18 * (np.linspace(-1, 1, size[0])[None, :] ** 2 + np.linspace(-1, 1, size[1])[:, None] ** 2))[..., None]
    img = Image.fromarray((c[None, None, :] + g[..., None] * 0.35) .__mul__(v).clip(0, 255).astype(np.uint8))
    d = ImageDraw.Draw(img); r = random.Random(4)
    fib = tuple(int(x * 0.86) for x in col(name))
    for _ in range(int(400 * size[0] * size[1] / (W * H))):
        x, y = r.uniform(0, size[0]), r.uniform(0, size[1]); a = r.uniform(0, 6.28); L = r.uniform(8, 30)
        d.line([(x, y), (x + L * math.cos(a), y + L * math.sin(a))], fill=fib, width=1)
    _bgc[key] = img.convert("RGBA"); return _bgc[key]


# ---------- sprite primitives ----------
def torn_poly(w, h, seed, step=14, amp=4):
    r = random.Random(seed); p = []
    for x in range(0, int(w) + 1, step): p.append((x, r.uniform(-amp, amp)))
    for y in range(0, int(h) + 1, step): p.append((w + r.uniform(-amp, amp), y))
    for x in range(int(w), -1, -step): p.append((x, h + r.uniform(-amp, amp)))
    for y in range(int(h), -1, -step): p.append((r.uniform(-amp, amp), y))
    return p


def blob_poly(r, seed, n=60, amp=0.035, sx=1.0, sy=1.0):
    rr = random.Random(seed)
    return [(r * sx * (1 + rr.uniform(-amp, amp)) * math.cos(2 * math.pi * i / n),
             r * sy * (1 + rr.uniform(-amp, amp)) * math.sin(2 * math.pi * i / n)) for i in range(n)]


def star_poly(r, points=5, inner=0.45):
    return [((r if i % 2 == 0 else r * inner) * math.cos(math.pi * i / points - math.pi / 2),
             (r if i % 2 == 0 else r * inner) * math.sin(math.pi * i / points - math.pi / 2)) for i in range(points * 2)]


class Canvas:
    """A transparent sprite canvas centred on (0,0) in local coords."""
    def __init__(s, w, h):
        s.w, s.h = int(w), int(h); s.im = Image.new("RGBA", (s.w, s.h), (0, 0, 0, 0)); s.d = ImageDraw.Draw(s.im)
        s.ox, s.oy = s.w / 2, s.h / 2

    def P(s, pts): return [(x + s.ox, y + s.oy) for x, y in pts]

    def poly(s, pts, color, fringe=True):
        pts = s.P(pts)
        if fringe:
            cx = sum(p[0] for p in pts) / len(pts); cy = sum(p[1] for p in pts) / len(pts)
            s.d.polygon([(x + (3 if x > cx else -3), y + (3 if y > cy else -3)) for x, y in pts], fill=PAPER)
        s.d.polygon(pts, fill=col(color))

    def blob(s, cx, cy, r, color, seed=0, fringe=True, sx=1.0, sy=1.0, n=60, amp=0.035):
        s.poly([(cx + x, cy + y) for x, y in blob_poly(r, seed, n, amp, sx, sy)], color, fringe)

    def rect(s, x0, y0, w, h, color, seed=0, fringe=True, step=14, amp=4):
        s.poly([(x0 + x, y0 + y) for x, y in torn_poly(w, h, seed, step, amp)], color, fringe)

    def text(s, x, y, txt, font, size, color, anchor="mm"):
        s.d.text((x + s.ox, y + s.oy), txt, font=F(font, size), fill=col(color), anchor=anchor)

    def line(s, pts, color, width):
        s.d.line(s.P(pts), fill=col(color), width=int(width), joint="curve")

    def erase_circle(s, cx, cy, r):
        s.d.ellipse([cx - r + s.ox, cy - r + s.oy, cx + r + s.ox, cy + r + s.oy], fill=(0, 0, 0, 0))


def texturize(im):
    a = im.split()[3]; g = GRAIN.crop((0, 0, min(im.width, W), min(im.height, H))).resize(im.size)
    rgb = Image.blend(im.convert("RGB"), Image.merge("RGB", (g, g, g)), 0.08)
    out = rgb.convert("RGBA"); out.putalpha(a); return out


def label_sprite(text, font="bold", size=90, color="paper", fg="navy", seed=0, padx=None, pady=None):
    f = F(font, size); b = f.getbbox(text); tw, th = b[2] - b[0], b[3] - b[1]
    padx = size * 0.38 if padx is None else padx; pady = size * 0.25 if pady is None else pady
    cv = Canvas(tw + 2 * padx + 30, th + 2 * pady + 30)
    if color != "none": cv.rect(-(tw / 2 + padx), -(th / 2 + pady), tw + 2 * padx, th + 2 * pady, color, seed)
    cv.d.text((cv.ox - tw / 2 - b[0], cv.oy - th / 2 - b[1]), text, font=f, fill=col(fg))
    return cv.im


def wrap(text, font, size, maxw):
    words = text.split(); lines = [""]
    for w in words:
        t = (lines[-1] + " " + w).strip()
        if F(font, size).getlength(t) <= maxw or not lines[-1]: lines[-1] = t
        else: lines.append(w)
    return lines


# ---------- prefabs: fn(el, local_t) -> RGBA sprite.  dynamic=True means redrawn each frame ----------
PREFABS = {}
def prefab(name, dynamic=False):
    def deco(fn): PREFABS[name] = (fn, dynamic); return fn
    return deco


@prefab("label")
def _label(e, t):
    return label_sprite(e["text"], e.get("font", "bold"), e.get("size", 90), e.get("color", "paper"), e.get("fg", "navy"), e.get("seed", hash(e["text"]) % 997))


@prefab("panel")
def _panel(e, t):
    w, h = e.get("w", 800), e.get("h", 800); cv = Canvas(w + 40, h + 40)
    cv.rect(-w / 2, -h / 2, w, h, e.get("color", "sky"), e.get("seed", 5), step=22, amp=7); return cv.im


@prefab("circle")
def _circle(e, t):
    r = e.get("r", 150); cv = Canvas(2 * r + 40, 2 * r + 40)
    cv.blob(0, 0, r, e.get("color", "mustard"), e.get("seed", 2), n=e.get("n", 60), amp=e.get("amp", 0.035)); return cv.im


@prefab("star")
def _star(e, t):
    r = e.get("r", 60); cv = Canvas(2 * r + 30, 2 * r + 30); cv.poly(star_poly(r), e.get("color", "mustard")); return cv.im


@prefab("stars")
def _stars(e, t):
    w, h = e.get("w", 900), e.get("h", 400); cv = Canvas(w + 60, h + 60); r = random.Random(e.get("seed", 3))
    for _ in range(e.get("count", 9)):
        rr = r.uniform(14, 34); x, y = r.uniform(-w / 2, w / 2), r.uniform(-h / 2, h / 2)
        cv.poly([(x + a, y + b) for a, b in star_poly(rr, 4, 0.35)], e.get("color", "paper"), False)
    return cv.im


@prefab("moon")
def _moon(e, t):
    r = e.get("r", 130); cv = Canvas(2 * r + 40, 2 * r + 40); cv.blob(0, 0, r, e.get("color", "paper"), 7)
    cv.erase_circle(r * 0.45, -r * 0.25, r * 0.85); return cv.im


@prefab("sun")
def _sun(e, t):
    r = e.get("r", 150); cv = Canvas(4 * r, 4 * r); ang = t * 40
    for k in range(10):
        a = math.radians(ang + k * 36); cx, cy = 1.45 * r * math.cos(a), 1.45 * r * math.sin(a); n = (math.cos(a), math.sin(a)); p = (-n[1], n[0])
        cv.poly([(cx - n[0] * 0.3 * r + p[0] * 0.17 * r, cy - n[1] * 0.3 * r + p[1] * 0.17 * r), (cx + n[0] * 0.3 * r, cy + n[1] * 0.3 * r),
                 (cx - n[0] * 0.3 * r - p[0] * 0.17 * r, cy - n[1] * 0.3 * r - p[1] * 0.17 * r)], e.get("color", "mustard"), False)
    cv.blob(0, 0, r, e.get("color", "mustard"), 2); return cv.im
PREFABS["sun"] = (_sun, True)


@prefab("clock", dynamic=True)
def _clock(e, t):
    r = e.get("r", 260); cv = Canvas(2 * r + 60, 2 * r + 60)
    cv.blob(0, 0, r * 1.2, e.get("color", "teal"), 9); cv.blob(0, 0, r, "paper", 10, False)
    for k in range(12):
        a = math.radians(k * 30); cv.line([(0.8 * r * math.sin(a), -0.8 * r * math.cos(a)), (0.92 * r * math.sin(a), -0.92 * r * math.cos(a))], "navy", r * 0.05)
    base = e.get("time", 2.0); spd = e.get("speed", 0.0)
    m = (base % 1) * 360 + t * spd * 360; hh = (base / 12) * 360 + t * spd * 30
    for ang, L, w, c in ((hh, 0.5, 0.11, "navy"), (m, 0.75, 0.07, "navy")):
        a = math.radians(ang); cv.line([(0, 0), (L * r * math.sin(a), -L * r * math.cos(a))], c, w * r)
    cv.blob(0, 0, r * 0.09, "terra", 4, False); return cv.im


@prefab("brain")
def _brain(e, t):
    r = e.get("r", 230); cv = Canvas(3 * r, 2.4 * r); c = e.get("color", "brainpink")
    cv.blob(-0.45 * r, 0, 0.75 * r, c, 11, sx=1.0, sy=0.85); cv.blob(0.45 * r, 0, 0.75 * r, c, 12, sx=1.0, sy=0.85)
    cv.blob(0, -0.2 * r, 0.7 * r, c, 13, fringe=False, sx=1.2, sy=0.8)
    dark = tuple(int(x * 0.75) for x in col(c)); rr = random.Random(5)
    for k in range(7):
        x0, y0 = rr.uniform(-0.9, 0.7) * r, rr.uniform(-0.5, 0.4) * r
        cv.line([(x0 + i * 0.07 * r, y0 + 0.08 * r * math.sin(i * 1.3 + k)) for i in range(6)], dark, r * 0.05)
    cv.line([(0, -0.6 * r), (0, 0.55 * r)], dark, r * 0.05)
    cv.rect(-0.12 * r, 0.5 * r, 0.24 * r, 0.45 * r, c, 3, False, 8, 2); return cv.im


@prefab("person", dynamic=True)
def _person(e, t):
    r = e.get("r", 120); mood = e.get("mood", "neutral"); cv = Canvas(3 * r, 5.2 * r)
    body = e.get("color", "teal"); oy = -0.9 * r
    cv.blob(0, oy + 2.1 * r, 1.2 * r, body, 21, sx=0.95, sy=1.05)
    cv.rect(-1.25 * r, oy + 2.3 * r, 2.5 * r, 1.4 * r, body, 22, False)
    cv.blob(0, oy, r, "skin", 23)
    cv.blob(0, oy - 0.55 * r, 0.82 * r, e.get("hair", "navy"), 24, fringe=False, sx=1.15, sy=0.55)
    ey = oy + 0.05 * r
    if mood in ("cringe", "shock"):
        for sx in (-1, 1): cv.blob(sx * 0.38 * r, ey, 0.17 * r, "paper", 25 + sx, False); cv.blob(sx * 0.38 * r, ey, 0.08 * r, "ink", 27, False)
    else:
        for sx in (-1, 1): cv.blob(sx * 0.38 * r, ey, 0.1 * r, "ink", 25 + sx, False)
    my = oy + 0.5 * r
    if mood == "happy": cv.line([(-0.35 * r + i * 0.07 * r, my + 0.12 * r * math.sin(i / 10 * math.pi)) for i in range(11)], "ink", 0.08 * r)
    elif mood == "sad": cv.line([(-0.3 * r + i * 0.06 * r, my + 0.12 * r - 0.12 * r * math.sin(i / 10 * math.pi)) for i in range(11)], "ink", 0.08 * r)
    elif mood == "cringe":
        cv.line([(-0.35 * r + i * 0.07 * r, my + 0.05 * r * math.sin(i * 1.6)) for i in range(11)], "ink", 0.07 * r)
        for sx in (-1, 1): cv.blob(sx * 0.62 * r, oy + 0.3 * r, 0.2 * r, "blush", 30 + sx, False, sy=0.6)
        cv.poly([(0.95 * r, oy - 0.45 * r), (1.08 * r, oy - 0.15 * r), (0.95 * r, oy - 0.08 * r), (0.83 * r, oy - 0.15 * r)], "sky", False)
    elif mood == "shock": cv.blob(0, my + 0.05 * r, 0.16 * r, "ink", 33, False, sy=1.3)
    else: cv.line([(-0.25 * r, my), (0.25 * r, my)], "ink", 0.07 * r)
    if e.get("shirt"): cv.text(0, oy + 2.4 * r, e["shirt"], "bold", e.get("shirt_size", 0.42 * r), e.get("shirt_fg", "paper"))
    return cv.im


@prefab("bed", dynamic=True)
def _bed(e, t):
    r = e.get("r", 110); cv = Canvas(8 * r, 4.2 * r); x0 = -3.6 * r
    cv.rect(x0, -0.2 * r, 7.2 * r, 1.4 * r, e.get("frame", "terra"), 41)
    cv.rect(x0 - 0.2 * r, -1.6 * r, 0.6 * r, 2.8 * r, e.get("frame", "terra"), 42)
    cv.rect(x0 + 0.4 * r, -1.0 * r, 1.9 * r, 0.9 * r, "paper", 43)
    cv.blob(x0 + 1.5 * r, -1.0 * r, r * 0.75, "skin", 44)
    cv.blob(x0 + 1.25 * r, -1.25 * r, r * 0.6, "navy", 45, False, sx=0.7, sy=1.1)
    awake = e.get("awake", True); ex = x0 + 1.75 * r
    for dy in (-0.22, 0.22):
        if awake: cv.blob(ex, -1.0 * r + dy * r, 0.13 * r, "paper", 46, False); cv.blob(ex + 0.03 * r, -1.0 * r + dy * r, 0.06 * r, "ink", 47, False)
        else: cv.line([(ex - 0.08 * r, -1.0 * r + dy * r), (ex + 0.08 * r, -1.0 * r + dy * r)], "ink", 0.05 * r)
    cv.rect(x0 + 2.2 * r, -1.0 * r, 5.0 * r, 1.0 * r, e.get("blanket", "sky"), 48, step=20, amp=6)
    return cv.im


@prefab("bubble")
def _bubble(e, t):
    font, size = e.get("font", "marker"), e.get("size", 70); lines = wrap(e["text"], font, size, e.get("maxw", 620))
    lh = size * 1.25; tw = max(F(font, size).getlength(l) for l in lines); th = lh * len(lines)
    w, h = tw + size * 1.2, th + size * 0.9; cv = Canvas(w + 260, h + 300); c = e.get("color", "paper"); tail = e.get("tail", "left")
    if e.get("style", "speech") == "thought":
        cv.blob(0, 0, max(w, h) / 2, c, 51, sx=w / max(w, h) * 1.05, sy=h / max(w, h) * 1.15)
        sgn = -1 if tail == "left" else 1
        for k, rr in enumerate((0.16, 0.1, 0.06)): cv.blob(sgn * w * (0.3 + 0.12 * k), h / 2 + size * (0.5 + 0.6 * k), size * rr * 3, c, 52 + k)
    else:
        sgn = -1 if tail == "left" else 1
        cv.poly([(sgn * w * 0.15, h / 2 - 10), (sgn * w * 0.38, h / 2 + size * 1.3), (sgn * w * 0.02, h / 2 - 10)], c)
        cv.rect(-w / 2, -h / 2, w, h, c, 53)
    for i, l in enumerate(lines): cv.text(0, -th / 2 + lh * (i + 0.5), l, font, size, e.get("fg", "navy"))
    return cv.im


@prefab("alarm", dynamic=True)
def _alarm(e, t):
    r = e.get("r", 120); cv = Canvas(4 * r, 3.4 * r); on = int(t * 6) % 2 == 0
    if on:
        for k in range(7):
            a = math.radians(-160 + k * 23.3); cv.line([(1.25 * r * math.cos(a), -0.2 * r + 1.25 * r * math.sin(a)), (1.75 * r * math.cos(a), -0.2 * r + 1.75 * r * math.sin(a))], "mustard", 0.16 * r)
    cv.poly([(-r, 0.6 * r)] + [(r * math.cos(math.radians(a)), -0.2 * r + r * math.sin(math.radians(a))) for a in range(180, 361, 10)] + [(r, 0.6 * r)], e.get("color", "red"))
    cv.rect(-1.3 * r, 0.55 * r, 2.6 * r, 0.5 * r, "navy", 61)
    cv.blob(-0.4 * r, -0.4 * r, 0.18 * r, "paper", 62, False, sx=0.7, sy=1.3); return cv.im


@prefab("bookmark")
def _bookmark(e, t):
    w, h = e.get("w", 170), e.get("h", 300); cv = Canvas(w + 40, h + 40); c = e.get("color", "terra")
    cv.poly([(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (0, h / 2 - w * 0.45), (-w / 2, h / 2)], c)
    if e.get("text"): cv.text(0, -h * 0.12, e["text"], "bold", e.get("size", w * 0.55), e.get("fg", "paper"))
    return cv.im


@prefab("replay")
def _replay(e, t):
    r = e.get("r", 230); cv = Canvas(2 * r + 120, 2 * r + 120); c = e.get("color", "mustard")
    for a0 in (0, 180):
        pts = [(r * math.cos(math.radians(a)), r * math.sin(math.radians(a))) for a in range(a0 + 15, a0 + 150, 5)]
        cv.line(pts, c, r * 0.13)
        a = math.radians(a0 + 150); tip = (r * math.cos(a), r * math.sin(a)); d = (-math.sin(a), math.cos(a)); n = (math.cos(a), math.sin(a))
        cv.poly([(tip[0] + d[0] * r * 0.22, tip[1] + d[1] * r * 0.22), (tip[0] + n[0] * r * 0.2, tip[1] + n[1] * r * 0.2), (tip[0] - n[0] * r * 0.2, tip[1] - n[1] * r * 0.2)], c, False)
    return cv.im


@prefab("play_card")
def _play_card(e, t):
    w, h = e.get("w", 460), e.get("h", 300); tw = F("marker", e.get("size", 56)).getlength(e.get("text", "")); cv = Canvas(max(w, tw) + 60, h + 160)
    cv.rect(-w / 2, -h / 2, w, h, e.get("color", "navy"), 71)
    cv.poly([(-h * 0.17, -h * 0.25), (h * 0.27, 0), (-h * 0.17, h * 0.25)], "paper", False)
    if e.get("text"): cv.text(0, h / 2 + 50, e["text"], "marker", e.get("size", 56), e.get("fg", "navy"))
    return cv.im


@prefab("counter", dynamic=True)
def _counter(e, t):
    a, b, dur = e.get("from", 1), e.get("to", 999), e.get("dur", 2.0)
    v = int(a + (b - a) * min(1, max(0, t / dur)) ** 2)
    txt = e.get("prefix", "") + f"{v:,}" + e.get("suffix", "")
    return label_sprite(txt, e.get("font", "bold"), e.get("size", 90), e.get("color", "paper"), e.get("fg", "navy"), 81)


@prefab("bars", dynamic=True)
def _bars(e, t):
    items = e["items"]; bw, gap, hmax = e.get("bar_w", 220), e.get("gap", 90), e.get("h", 520)
    n = len(items); totw = n * bw + (n - 1) * gap; cv = Canvas(totw + 80, hmax + 300); base = hmax / 2 + 20
    cv.rect(-totw / 2 - 30, base, totw + 60, 16, "navy", 90, False, 20, 2)
    for i, it in enumerate(items):
        p = min(1, max(0, (t - i * e.get("stagger", 0.9)) / 0.7)); p = 1 - (1 - p) ** 3; hh = hmax * it["value"] / 100 * p
        x = -totw / 2 + i * (bw + gap)
        if hh > 4: cv.rect(x, base - hh, bw, hh, it.get("color", "teal"), 91 + i, step=16, amp=3)
        if p > 0.05: cv.text(x + bw / 2, base - hh - 60, it.get("value_text", f"{it['value']}%"), "bold", 74, "navy")
        cv.text(x + bw / 2, base + 70, it["label"], "bold", 46, "navy")
    return cv.im


@prefab("spotlight")
def _spotlight(e, t):
    w, h = e.get("w", 700), e.get("h", 1100); im = Image.new("RGBA", (int(w) + 40, int(h) + 40), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    cx = im.width / 2; c = col(e.get("color", "mustard"))
    d.polygon([(cx - 50, 20), (cx + 50, 20), (cx + w / 2, h - 60), (cx - w / 2, h - 60)], fill=c + (90,))
    d.ellipse([cx - w / 2, h - 130, cx + w / 2, h + 10], fill=c + (120,))
    return im


@prefab("tshirt")
def _tshirt(e, t):
    s = e.get("s", 1.0); cv = Canvas(560 * s, 520 * s); c = e.get("color", "mustard")
    cv.poly([(x * s, y * s) for x, y in [(-120, -200), (-60, -200), (0, -170), (60, -200), (120, -200), (250, -100), (190, -10), (130, -60), (130, 220), (-130, 220), (-130, -60), (-190, -10), (-250, -100)]], c)
    if e.get("text"):
        for i, l in enumerate(e["text"].split("\n")): cv.text(0, (-10 + i * 70) * s, l, "bold", e.get("size", 60) * s, e.get("fg", "navy"))
    return cv.im


@prefab("badge")
def _badge(e, t):
    r = e.get("r", 90); cv = Canvas(2 * r + 40, 2 * r + 40); kind = e.get("kind", "check")
    cv.blob(0, 0, r, e.get("color", "green" if kind == "check" else "red"), 101)
    if kind == "check": cv.line([(-0.45 * r, 0), (-0.1 * r, 0.35 * r), (0.5 * r, -0.4 * r)], "paper", 0.2 * r)
    else: cv.line([(-0.4 * r, -0.4 * r), (0.4 * r, 0.4 * r)], "paper", 0.2 * r); cv.line([(0.4 * r, -0.4 * r), (-0.4 * r, 0.4 * r)], "paper", 0.2 * r)
    return cv.im


@prefab("arrow")
def _arrow(e, t):
    L, w = e.get("len", 300), e.get("w", 70); cv = Canvas(L + 80, w * 2.6 + 40)
    cv.poly([(-L / 2, -w / 2), (L / 2 - w, -w / 2), (L / 2 - w, -w * 1.1), (L / 2, 0), (L / 2 - w, w * 1.1), (L / 2 - w, w / 2), (-L / 2, w / 2)], e.get("color", "terra"))
    return cv.im


@prefab("heart")
def _heart(e, t):
    r = e.get("r", 90); cv = Canvas(2.6 * r, 2.6 * r)
    cv.poly([(r * 16 * math.sin(a) ** 3 / 16, -r * (13 * math.cos(a) - 5 * math.cos(2 * a) - 2 * math.cos(3 * a) - math.cos(4 * a)) / 16) for a in np.linspace(0, 2 * math.pi, 60)], e.get("color", "red"))
    return cv.im


@prefab("follow", dynamic=True)
def _follow(e, t):
    s = e.get("size", 100); txt = e.get("text", "FOLLOW"); f = F("bold", s); tw = f.getlength(txt)
    w, h = tw + s * 2.0, s * 1.8; cv = Canvas(w + 60, h + 60)
    cv.blob(0, 0, w / 2, e.get("color", "red"), 111, sx=1.0, sy=h / w)
    cv.text(-tw / 2 - s * 0.35, 0, "+", "bold", s * 1.1, "paper"); cv.text(s * 0.35, 0, txt, "bold", s, "paper")
    return cv.im


@prefab("comment")
def _comment(e, t):
    w = e.get("w", 820); cv = Canvas(w + 60, 330)
    cv.rect(-w / 2, -130, w, 240, e.get("color", "paper"), 121)
    cv.blob(-w / 2 + 95, -10, 55, e.get("avatar", "mustard"), 122, False)
    cv.text(-w / 2 + 180, -55, e.get("user", "@you"), "bold", 44, "navy", anchor="lm")
    cv.text(-w / 2 + 180, 25, e.get("text", "my cringe memory is..."), "marker", e.get("size", 52), "ink", anchor="lm")
    return cv.im


@prefab("calendar")
def _calendar(e, t):
    w, h = e.get("w", 520), e.get("h", 560); cv = Canvas(w + 40, h + 40)
    cv.rect(-w / 2, -h / 2, w, h, "paper", e.get("seed", 131)); cv.rect(-w / 2, -h / 2, w, h * 0.22, e.get("color", "terra"), 132, False)
    cv.text(0, -h / 2 + h * 0.11, e.get("top", ""), "marker", h * 0.08, "paper")
    cv.text(0, h * 0.12, e.get("text", "JAN"), "bold", e.get("size", h * 0.3), "navy"); return cv.im


# ---------- timeline ----------
def norm(w): return re.sub(r"[^a-z0-9%#]", "", w.lower())


class Timeline:
    def __init__(s, spec, timing):
        s.spec, s.lines = spec, timing["lines"]; s.dur = spec.get("duration", 60.0)
        n = len(spec["scenes"]); starts = []
        for i in range(n):
            ls = [l for l in s.lines if l["scene"] == i]
            starts.append(0.0 if i == 0 else ls[0]["start"] - 0.25)
        s.starts = starts + [s.dur]
        s.words = [dict(w, line=li, scene=l["scene"]) for li, l in enumerate(s.lines) for w in l["words"]]

    def scene_at(s, t):
        for i in range(len(s.starts) - 1):
            if t < s.starts[i + 1]: return i
        return len(s.starts) - 2

    def resolve(s, si, v, default=0.0):
        """Scene-relative time. v: number | 'word' | 'word#2' | 'word+0.3' | 'line2' | 'end-0.5'."""
        if v is None: return default
        if isinstance(v, (int, float)): return float(v)
        m = re.match(r"^(.*?)([+-]\d*\.?\d+)?$", v.strip()); key, off = m.group(1), float(m.group(2) or 0)
        base = s.starts[si]
        if key == "end": return s.starts[si + 1] - base + off
        if key == "start": return off
        lm = re.match(r"^line(\d+)$", key)
        sl = [l for l in s.lines if l["scene"] == si]
        if lm: return sl[int(lm.group(1))]["start"] - base + off
        km = re.match(r"^(.*?)(?:#(\d+))?$", key); target, nth = norm(km.group(1)), int(km.group(2) or 1)
        hits = [w for w in s.words if w["scene"] == si and norm(w["w"]).startswith(target)]
        if len(hits) < nth: raise ValueError(f"scene {si}: word anchor '{v}' not found")
        return hits[nth - 1]["s"] - base + off


# ---------- composition ----------
_cache = {}
def sprite_for(e, lt):
    fn, dyn = PREFABS[e["type"]]
    if dyn: return texturize(fn(e, lt)) if e["type"] != "spotlight" else fn(e, lt)
    k = json.dumps(e, sort_keys=True)
    if k not in _cache: _cache[k] = fn(e, lt) if e["type"] == "spotlight" else texturize(fn(e, lt))
    return _cache[k]


def stepped_pop(x):
    if x <= 0: return 0
    if x >= 1: return 1
    return [0.35, 1.15, 0.92, 1.0][min(int(x * 4), 3)]


def place(canvas, shadow, im, cx, cy, rot, sc, cast=True):
    if sc <= 0.01: return
    if abs(sc - 1) > 0.01: im = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.BICUBIC)
    if abs(rot) > 0.05: im = im.rotate(rot, expand=True, resample=Image.BICUBIC)
    x, y = int(cx - im.width / 2), int(cy - im.height / 2)
    if cast: shadow.paste((0, 0, 0, 255), (x + 9, y + 13), im.split()[3].point(lambda v: v * 0.45))
    canvas.alpha_composite(im, (x, y)) if 0 <= x and 0 <= y and x + im.width <= W and y + im.height <= H else _paste_clip(canvas, im, x, y)


def _paste_clip(canvas, im, x, y):
    tmp = Image.new("RGBA", canvas.size, (0, 0, 0, 0)); tmp.paste(im, (x, y), im); canvas.alpha_composite(tmp)


def draw_elements(tl, si, lt, canvas, shadow, fi, first_scene_instant=True):
    r = random.Random(fi * 7 + si)
    sc_spec = tl.spec["scenes"][si]
    for k, e in enumerate(sc_spec.get("elements", [])):
        st = tl.resolve(si, e.get("at"), 0.0)
        if si == 0 and st <= 0 and first_scene_instant: st = -10  # hook frame: visible from frame 1
        en = tl.resolve(si, e.get("out"), 1e9)
        x = lt - st
        if x < 0 or lt > en + 0.3: continue
        anim = e.get("anim", "pop"); s = e.get("scale", 1.0); cx, cy = e.get("x", 540), e.get("y", 760); rot = e.get("rot", 0)
        if anim == "pop": s *= stepped_pop(x / 0.35)
        elif anim.startswith("slide"):
            p = 1 - (1 - min(1, x / 0.45)) ** 3; dx, dy = {"slide_left": (-1100, 0), "slide_right": (1100, 0), "slide_up": (0, 1400), "slide_down": (0, -1400)}[anim]
            cx += dx * (1 - p); cy += dy * (1 - p)
        if lt > en: s *= max(0, 1 - (lt - en) / 0.3)
        loop = e.get("loop")
        if loop == "bob": cy += 10 * math.sin(lt * 3 + k)
        elif loop == "spin": rot += e.get("spin_speed", -90) * lt
        elif loop == "shake": rot += (6 if (fi % 2) else -6) * (1 if x < e.get("shake_for", 0.8) else 0)
        elif loop == "pulse": s *= 1 + 0.06 * math.sin(lt * 7)
        elif loop == "wiggle": rot += r.uniform(-3, 3)
        if e.get("jitter", True): cx += r.uniform(-3, 3); cy += r.uniform(-3, 3); rot += r.uniform(-1.2, 1.2)
        place(canvas, shadow, sprite_for(e, max(0, x)), cx, cy, rot, s, e["type"] != "spotlight")


def draw_captions(tl, t, canvas, shadow, y=1400):
    words = tl.words; act = None; chunks = getattr(tl, "_chunks", None)
    if chunks is None:
        chunks = []; cur = []
        for i, w in enumerate(words):
            if cur and (words[cur[-1]]["line"] != w["line"] or len(cur) >= 3): chunks.append(cur); cur = []
            cur.append(i)
            if w["w"][-1] in ",.?:!": chunks.append(cur); cur = []
        if cur: chunks.append(cur)
        tl._chunks = chunks
    for c in chunks:
        if words[c[0]]["s"] - 0.05 <= t < words[c[-1]]["e"] + 0.15: act = c
    if not act: return
    toks = [(i, words[i]["w"].upper().strip(",.?:!")) for i in act if words[i]["s"] <= t + 0.02]
    shades = ["paper", (250, 240, 215), (236, 226, 206)]; ims = []
    for i, w in toks:
        on = t < words[i]["e"] + 0.1 and i == toks[-1][0]
        key = ("cap", i, on)
        if key not in _cache: _cache[key] = texturize(label_sprite(w, "bold", 78, "mustard" if on else shades[i % 3], "navy", 100 + i, 22, 14))
        ims.append((_cache[key], i * 37 % 7 - 3))
    tot = sum(im.width for im, _ in ims) + 4 * (len(ims) - 1)
    if tot > 1000:
        k = 1000 / tot; ims = [(im.resize((int(im.width * k), int(im.height * k))), r) for im, r in ims]; tot = 1000
    x = 540 - tot / 2
    for im, rot in ims:
        rim = im.rotate(rot, expand=True, resample=Image.BICUBIC); yy = y - rim.height / 2 + rot * 2
        shadow.paste((0, 0, 0, 255), (int(x) + 7, int(yy) + 10), rim.split()[3].point(lambda v: v * 0.45))
        canvas.alpha_composite(rim, (int(x), int(yy))); x += im.width + 4


def scene_layers(tl, si, lt, fi):
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0)); shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_elements(tl, si, lt, canvas, shadow, fi); return canvas, shadow


def frame(tl, t):
    fi = int(t * ANIM_FPS); t = fi / ANIM_FPS
    si = tl.scene_at(t); lt = t - tl.starts[si]; spec = tl.spec["scenes"][si]
    out = background(spec.get("bg", "cream")).copy()
    canvas, shadow = scene_layers(tl, si, lt, fi)
    TR = 0.33
    if si > 0 and lt < TR:  # paper sheet slides up over the previous scene
        prev = tl.spec["scenes"][si - 1]; plt = tl.starts[si] - tl.starts[si - 1]
        pc, ps = scene_layers(tl, si - 1, plt, fi)
        base = background(prev.get("bg", "cream")).copy(); base.alpha_composite(ps.filter(ImageFilter.GaussianBlur(7))); base.alpha_composite(pc)
        p = 1 - (1 - lt / TR) ** 2; top = int(H * (1 - p)) - 30
        sheet = Image.new("L", (W, H), 0); d = ImageDraw.Draw(sheet); rr = random.Random(si)
        d.polygon([(x, top + rr.uniform(-12, 12)) for x in range(0, W + 1, 30)] + [(W, H), (0, H)], fill=255)
        out = base; sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sh.paste((0, 0, 0, 110), (0, -14), sheet)
        out.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
        out.paste(background(spec.get("bg", "cream")), (0, 0), sheet)
        canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0)); shadow = canvas.copy()
    draw_captions(tl, t, canvas, shadow)
    # progress strip
    pw = int(W * min(1, t / tl.dur)); pd = ImageDraw.Draw(canvas)
    if pw > 0: pd.polygon([(0, 0), (pw, 0), (pw, 14 + 3 * math.sin(pw)), (0, 16)], fill=C["mustard"])
    out.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(7))); out.alpha_composite(canvas)
    return out.convert("RGB")


def render_range(spec_path, work, a, b, out):
    spec = json.load(open(spec_path)); tl = Timeline(spec, json.load(open(os.path.join(work, "timing.json"))))
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    last, lk = None, None; step = FPS // ANIM_FPS if FPS % ANIM_FPS == 0 else 1
    for i in range(a, b):
        k = int(i / FPS * ANIM_FPS)
        if k != lk: last = frame(tl, i / FPS).tobytes(); lk = k
        p.stdin.write(last)
    p.stdin.close(); p.wait()


def render_video(spec_path, work, jobs=4):
    spec = json.load(open(spec_path)); n = int(spec.get("duration", 60.0) * FPS); per = -(-n // jobs); procs = []
    for j in range(jobs):
        procs.append(subprocess.Popen([sys.executable, __file__, spec_path, work, "range", str(j * per), str(min(n, (j + 1) * per)), os.path.join(work, f"part{j}.mp4")]))
    for p in procs:
        if p.wait(): raise SystemExit("render failed")
    with open(os.path.join(work, "parts.txt"), "w") as f:
        for j in range(jobs): f.write(f"file part{j}.mp4\n")
    subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-i", os.path.join(work, "parts.txt"), "-c", "copy", os.path.join(work, "video_silent.mp4")])
    for j in range(jobs): os.remove(os.path.join(work, f"part{j}.mp4"))


def render_thumbs(spec_path, work):
    spec = json.load(open(spec_path)); th = spec["thumbnail"]
    for name, size, key in (("thumbnail_9x16.png", (W, H), "vertical"), ("thumbnail_16x9.png", (1280, 720), "horizontal")):
        els = th[key]; out = background(th.get("bg", "cream"), size).copy()
        canvas = Image.new("RGBA", size, (0, 0, 0, 0)); shadow = canvas.copy()
        for e in els:
            place(canvas, shadow, sprite_for(e, e.get("t", 0.0)), e.get("x", size[0] / 2), e.get("y", size[1] / 2), e.get("rot", 0), e.get("scale", 1.0), e["type"] != "spotlight")
        out.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(7))); out.alpha_composite(canvas)
        out.convert("RGB").save(os.path.join(work, name))


if __name__ == "__main__":
    spec_path, work, mode = sys.argv[1], sys.argv[2], sys.argv[3]
    if mode == "video": render_video(spec_path, work, int(sys.argv[4]) if len(sys.argv) > 4 else os.cpu_count() or 4)
    elif mode == "range": render_range(spec_path, work, int(sys.argv[4]), int(sys.argv[5]), sys.argv[6])
    elif mode == "still":
        spec = json.load(open(spec_path)); tl = Timeline(spec, json.load(open(os.path.join(work, "timing.json"))))
        frame(tl, float(sys.argv[4])).save(sys.argv[5])
    elif mode == "thumbs": render_thumbs(spec_path, work)
