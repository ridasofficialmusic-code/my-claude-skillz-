"""Three profile-logo directions for stillwaters.daily (TikTok + Instagram, circle-cropped)."""
import math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

OUT = sys.argv[1]; FD = sys.argv[2]; os.makedirs(OUT, exist_ok=True)
S = 2160  # draw at 2x, downsample to 1080 for smooth edges
CREAM = (239, 230, 210)


def font(name, size, wght):
    f = ImageFont.truetype(os.path.join(FD, name), int(size)); f.set_variation_by_axes([wght]); return f


def grad(c1, c2, radial=False, cy=0.45):
    y, x = np.mgrid[0:S, 0:S] / S
    t = np.clip(np.hypot(x - 0.5, y - cy) / 0.72, 0, 1) if radial else y
    a = np.array(c1)[None, None] * (1 - t[..., None]) + np.array(c2)[None, None] * t[..., None]
    return a


def grain(a, amt=5):
    return np.clip(a + np.random.default_rng(1).normal(0, amt, a.shape[:2])[..., None], 0, 255)


def finish(img, name):
    img = img.resize((1080, 1080), Image.LANCZOS).convert("RGB"); img.save(os.path.join(OUT, name)); return img


def spaced(d, cx, y, text, f, fill, track):
    w = sum(f.getlength(c) for c in text) + track * (len(text) - 1); x = cx - w / 2
    for c in text: d.text((x, y), c, font=f, fill=fill, anchor="lm"); x += f.getlength(c) + track


def cross(d, cx, top, h, w, th, fill):
    d.rectangle([cx - th / 2, top, cx + th / 2, top + h], fill=fill)
    d.rectangle([cx - w / 2, top + h * 0.28 - th / 2, cx + w / 2, top + h * 0.28 + th / 2], fill=fill)


# 1) STILL WATER: a cross reflected in still water, minimal
def logo_reflection():
    img = Image.fromarray(grain(grad((38, 66, 72), (12, 26, 30), True, 0.42), 4).astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(img); cx, hz = S / 2, S * 0.57
    cross(d, cx, S * 0.25, S * 0.32, S * 0.17, S * 0.022, CREAM)
    d.line([(cx - S * 0.25, hz), (cx + S * 0.25, hz)], fill=CREAM + (210,), width=int(S * 0.004))
    refl = Image.new("RGBA", (S, S), (0, 0, 0, 0)); rd = ImageDraw.Draw(refl)
    cross(rd, cx, hz + S * 0.012, S * 0.32 * 0.6, S * 0.17 * 0.9, S * 0.022, CREAM + (70,))
    for k in range(7):  # ripple breaks across the reflection
        y = hz + S * (0.03 + k * 0.026); rd.rectangle([cx - S * 0.1, y, cx + S * 0.1, y + S * 0.0035], fill=(0, 0, 0, 0))
    refl = refl.transform(refl.size, Image.AFFINE, (1, 0, 0, 0, 1, 0)).filter(ImageFilter.GaussianBlur(S * 0.003))
    img.alpha_composite(refl)
    for k, (rx, al) in enumerate(((0.12, 55), (0.19, 34), (0.27, 18))):
        ry = rx * 0.16; y0 = hz + S * 0.2
        d.ellipse([cx - S * rx, y0 - S * ry, cx + S * rx, y0 + S * ry], outline=CREAM + (al,), width=int(S * 0.003))
    spaced(d, cx, S * 0.86, "STILL WATERS", font("Montserrat%5Bwght%5D.ttf", S * 0.042, 400), CREAM + (230,), S * 0.014)
    return finish(img, "logo1_still-water.png")


# 2) MONOGRAM: classic serif SW inside a ring with arc lettering
def arc_text(img, text, cx, cy, r, f, fill, start_deg, track_deg, outward=True):
    for i, ch in enumerate(text):
        a = math.radians(start_deg + i * track_deg)
        x, y = cx + r * math.cos(a), cy + r * math.sin(a)
        tile = Image.new("RGBA", (int(f.size * 2), int(f.size * 2)), (0, 0, 0, 0)); ImageDraw.Draw(tile).text((tile.width / 2, tile.height / 2), ch, font=f, fill=fill, anchor="mm")
        rot = -(math.degrees(a) + 90) if outward else -(math.degrees(a) - 90)
        tile = tile.rotate(rot, resample=Image.BICUBIC); img.alpha_composite(tile, (int(x - tile.width / 2), int(y - tile.height / 2)))


def logo_monogram():
    img = Image.fromarray(grain(grad((52, 66, 54), (30, 40, 32), True, 0.5), 5).astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(img); cx = cy = S / 2
    for rr, w in ((0.405, 0.004), (0.385, 0.0018)): d.ellipse([cx - S * rr, cy - S * rr, cx + S * rr, cy + S * rr], outline=CREAM, width=int(S * w))
    d.text((cx, cy + S * 0.02), "SW", font=font("CormorantGaramond%5Bwght%5D.ttf", S * 0.36, 500), fill=CREAM, anchor="mm")
    cross(d, cx, S * 0.205, S * 0.07, S * 0.04, S * 0.007, CREAM)
    d.line([(cx - S * 0.11, S * 0.665), (cx + S * 0.11, S * 0.665)], fill=CREAM, width=int(S * 0.003))
    f = font("Montserrat%5Bwght%5D.ttf", S * 0.034, 500); txt = "DAILY"; step = 6.0
    arc_text(img, txt, cx, cy, S * 0.33, f, CREAM, 90 + step * (len(txt) - 1) / 2, -step, outward=False)
    for x in (-1, 1): d.ellipse([cx + x * S * 0.11 - S * 0.006, cy + S * 0.33 - S * 0.006, cx + x * S * 0.11 + S * 0.006, cy + S * 0.33 + S * 0.006], fill=CREAM)
    return finish(img, "logo2_monogram.png")


# 3) DAWN: sunrise over still water with a cross in the sun (matches the page's nature backgrounds)
def logo_dawn():
    y = np.linspace(0, 1, S)[:, None]; hz = 0.6
    sky = np.array((222, 196, 178)) * (1 - y / hz)[..., None] + np.array((176, 160, 170)) * (y / hz)[..., None]
    wy = np.clip((y - hz) / (1 - hz), 0, 1)
    water = np.array((118, 128, 140)) * (1 - wy)[..., None] + np.array((58, 68, 82)) * wy[..., None]
    a = np.where((y < hz)[..., None], sky, water); a = np.broadcast_to(a, (S, S, 3)).copy()
    cx, hy, r = S / 2, S * hz, S * 0.2
    yy, xx = np.mgrid[0:S, 0:S]; dist = np.hypot(xx - cx, yy - hy) / (r * 2.4)
    a += (np.exp(-dist ** 2 * 2.2) * 38)[..., None] * np.array((1.0, 0.9, 0.75))[None, None]  # smooth float glow, no banding
    img = Image.fromarray(grain(a, 4).astype(np.uint8)).convert("RGBA")
    sun = Image.new("RGBA", (S, S), (0, 0, 0, 0)); sd = ImageDraw.Draw(sun); sd.ellipse([cx - r, hy - r, cx + r, hy + r], fill=(250, 236, 214, 255))
    sd.rectangle([0, hy, S, S], fill=(0, 0, 0, 0)); img.alpha_composite(sun)
    d = ImageDraw.Draw(img)
    for k in range(9):  # broken sun reflection on the water
        yy = hy + S * (0.022 + k * 0.03); w = r * (0.85 - k * 0.075) * (0.82 + 0.18 * math.sin(k * 2.3)); off = r * 0.05 * math.sin(k * 1.7)
        d.rounded_rectangle([cx - w + off, yy, cx + w + off, yy + S * (0.009 - k * 0.0006)], radius=int(S * 0.004), fill=(250, 236, 214, int(210 - k * 20)))
    cross(d, cx, hy - r * 1.18, r * 1.18, r * 0.62, S * 0.02, (52, 52, 66))
    d.line([(0, hy), (S, hy)], fill=(70, 72, 88), width=int(S * 0.003))
    return finish(img, "logo3_dawn.png")


imgs = [logo_reflection(), logo_monogram(), logo_dawn()]
# preview: each as a circle at full size and at real profile size (~110 px)
mask = Image.new("L", (1080, 1080), 0); ImageDraw.Draw(mask).ellipse((0, 0, 1080, 1080), fill=255)
sheet = Image.new("RGB", (3 * 560 + 40, 700), (18, 18, 18)); sd = ImageDraw.Draw(sheet)
labels = ["1  Still Water", "2  Monogram", "3  Dawn"]
for i, im in enumerate(imgs):
    c = Image.new("RGB", (1080, 1080), (18, 18, 18)); c.paste(im, (0, 0), mask)
    sheet.paste(c.resize((500, 500), Image.LANCZOS), (40 + i * 560, 40)); m = mask.resize((110, 110), Image.LANCZOS)
    sheet.paste(im.resize((110, 110), Image.LANCZOS), (40 + i * 560, 560), m)
    sd.text((170 + i * 560, 615), labels[i], fill=(235, 235, 235), font=font("Montserrat%5Bwght%5D.ttf", 30, 500), anchor="lm")
sheet.save(os.path.join(OUT, "preview_circles.png"))
