"""Channel art in the paper cut-out style: YouTube banner (2560x1440) + logo (800x800, circle-safe).
Usage: python3 branding.py OUT_DIR ["Channel Name"] ["tagline"]
"""
import os, sys
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render import background, sprite_for, place

BW, BH = 2560, 1440
SAFE = (BW // 2 - 773, BH // 2 - 211, BW // 2 + 773, BH // 2 + 211)  # visible on every device


def compose(size, bg, els):
    out = background(bg, size).copy(); cv = Image.new("RGBA", size, (0, 0, 0, 0)); sh = cv.copy()
    for e in els:
        place(cv, sh, sprite_for(e, e.get("t", 0.0)), e["x"], e["y"], e.get("rot", 0), e.get("scale", 1.0), e["type"] != "spotlight")
    out.alpha_composite(sh.filter(ImageFilter.GaussianBlur(9))); out.alpha_composite(cv); return out


def eye_brain(x, y, r, look=(0.25, 0.1)):
    return [{"type": "brain", "x": x, "y": y, "r": r},
            {"type": "circle", "r": int(r * 0.42), "color": "paper", "x": x, "y": y - r * 0.12, "seed": 201},
            {"type": "circle", "r": int(r * 0.2), "color": "ink", "x": x + r * 0.42 * look[0], "y": y - r * 0.12 + r * 0.42 * look[1], "seed": 202},
            {"type": "circle", "r": int(r * 0.06), "color": "paper", "x": x + r * 0.42 * look[0] + r * 0.06, "y": y - r * 0.12 + r * 0.42 * look[1] - r * 0.07, "seed": 203}]


def banner(out, name, tagline):
    words = name.upper().split()
    styles = [("terra", "paper", -4), ("navy", "paper", 3), ("mustard", "navy", -2), ("teal", "paper", 4)]
    cx, cy = BW / 2, BH / 2 - 40
    els = [
        # decoration outside the safe area (visible on desktop / TV)
        {"type": "stars", "x": 420, "y": 360, "w": 600, "h": 300, "color": "mustard", "count": 7, "seed": 8},
        {"type": "moon", "x": 250, "y": 470, "r": 100, "color": "navy"},
        {"type": "person", "mood": "cringe", "x": 330, "y": 1120, "r": 120, "color": "teal"},
        {"type": "bubble", "style": "thought", "text": "\"you too!\"", "size": 52, "x": 680, "y": 1050, "tail": "left"},
        {"type": "clock", "r": 120, "time": 2.0, "x": 2260, "y": 360, "color": "terra"},
        {"type": "replay", "r": 105, "x": 2330, "y": 980, "color": "teal", "rot": 20},
        {"type": "alarm", "r": 70, "x": 2120, "y": 1020, "t": 0.0},
        {"type": "heart", "r": 60, "x": 2420, "y": 720, "color": "pink", "rot": -12},
        {"type": "star", "r": 46, "x": 820, "y": 460, "color": "terra", "rot": 10},
        {"type": "badge", "kind": "check", "r": 55, "x": 1760, "y": 1110},
    ] + eye_brain(cx - 600, cy, 120, (0.35, 0.05))
    x = cx - 400 + 30; gap = 22; sizes = [170] * len(words)
    from render import label_sprite
    sprites = [label_sprite(w, "bold", s, c, f, 300 + i) for i, (w, s, (c, f, r)) in enumerate(zip(words, sizes, styles))]
    total = sum(s.width for s in sprites) + gap * (len(sprites) - 1); maxw = 1080
    k = min(1.0, maxw / total); x = cx - 460 + (1150 - total * k) / 2 + 40
    for i, (sp, (c, f, r)) in enumerate(zip(sprites, styles)):
        w = sp.width * k
        els.append({"type": "label", "text": words[i], "size": int(170 * k), "color": c, "fg": f, "seed": 300 + i, "x": x + w / 2 + 70, "y": cy - 25 + (i % 2) * 18, "rot": r})
        x += w + gap * k
    els.append({"type": "label", "text": tagline, "font": "marker", "size": 54, "color": "paper", "fg": "navy", "x": cx + 70, "y": cy + 135, "rot": -1, "seed": 330})
    img = compose((BW, BH), "cream", els)
    img.convert("RGB").save(os.path.join(out, "banner_2560x1440.png"))
    guide = img.copy(); d = ImageDraw.Draw(guide)
    d.rectangle(SAFE, outline=(255, 0, 0, 255), width=6); d.rectangle((BW // 2 - 1235, BH // 2 - 211, BW // 2 + 1235, BH // 2 + 211), outline=(0, 120, 255, 255), width=4)
    guide.convert("RGB").resize((1280, 720)).save(os.path.join(out, "banner_safe-area-check.png"))


def logo(out, name):
    # Full-bleed teal so any crop (circle, rounded square, small avatar) is clean;
    # all artwork stays inside a ~300px radius so YouTube's circle mask never touches it.
    S = 800; initials = "".join(w[0] for w in name.upper().split())
    els = [{"type": "circle", "r": 330, "color": "navy", "x": 400, "y": 400, "seed": 211, "n": 240, "amp": 0.006}]
    els += eye_brain(400, 360, 165, (0.3, 0.1))
    els.append({"type": "label", "text": initials, "size": 82, "color": "mustard", "fg": "navy", "x": 400, "y": 590, "rot": -4, "seed": 220})
    img = compose((S, S), "teal", els); img.convert("RGB").save(os.path.join(out, "logo_800x800.png"))
    m = Image.new("L", (S, S), 0); ImageDraw.Draw(m).ellipse((0, 0, S, S), fill=255)
    prev = Image.new("RGBA", (S, S), (255, 255, 255, 0)); prev.paste(img, (0, 0), m)
    sm = prev.resize((98, 98), Image.LANCZOS); row = Image.new("RGBA", (S + 140, S), (255, 255, 255, 255))
    row.alpha_composite(prev); row.alpha_composite(sm, (S + 20, 40))
    row.convert("RGB").save(os.path.join(out, "logo_circle-preview.png"))


if __name__ == "__main__":
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    name = sys.argv[2] if len(sys.argv) > 2 else "Weird Being Human"
    tag = sys.argv[3] if len(sys.argv) > 3 else "the weird science of why you do what you do"
    banner(out, name, tag); logo(out, name)
