"""Voiceover: script.json -> <out>/voice.wav + <out>/timing.json (per-line and per-word timings).

Uses Kokoro (offline neural TTS). Model files are downloaded once into ~/.cache/paper-shorts.
Usage: python3 tts.py script.json OUT_DIR
"""
import json, os, sys, subprocess, urllib.request
import numpy as np, soundfile as sf

CACHE = os.path.expanduser("~/.cache/paper-shorts")
BASE = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/"
SR = 24000


def ensure_model():
    os.makedirs(CACHE, exist_ok=True)
    for f in ("kokoro-v1.0.onnx", "voices-v1.0.bin"):
        p = os.path.join(CACHE, f)
        if not os.path.exists(p):
            print("downloading", f)
            subprocess.check_call(["curl", "-sSfL", "-o", p, BASE + f])
    return os.path.join(CACHE, "kokoro-v1.0.onnx"), os.path.join(CACHE, "voices-v1.0.bin")


def _spread(ws, start, end):
    wt = [len(w) + 2 for w in ws]; tot = sum(wt); t = start; out = []
    for w, x in zip(ws, wt):
        d = (end - start) * x / tot; out.append({"w": w, "s": round(t, 3), "e": round(t + d, 3)}); t += d
    return out


def word_times(text, start, end, audio=None):
    """Per-word timings. Phrases (split at punctuation) are pinned to the real pauses found in the audio,
    then words are spread by length inside each phrase, so captions stay in sync through dramatic pauses."""
    ws = text.split()
    groups, cur = [], []
    for w in ws:
        cur.append(w)
        if w[-1] in ",.?!:;" or w.endswith("..."): groups.append(cur); cur = []
    if cur: groups.append(cur)
    if audio is None or len(groups) < 2: return _spread(ws, start, end)
    hop = int(SR * 0.01); env = np.sqrt(np.convolve(audio ** 2, np.ones(hop) / hop, "same"))[::hop]
    quiet = env < max(0.012, 0.08 * np.percentile(env, 95)); gaps = []; i = 0
    while i < len(quiet):  # silent runs >= 90 ms, away from the edges
        if quiet[i]:
            j = i
            while j < len(quiet) and quiet[j]: j += 1
            if j - i >= 9 and i > 5 and j < len(quiet) - 5: gaps.append(((i + j) / 2 * 0.01, j - i))
            i = j
        else: i += 1
    need = len(groups) - 1
    if len(gaps) < need: return _spread(ws, start, end)
    # choose the `need` longest pauses, in time order, but prefer ones near where length-based spreading expects them
    chars = [sum(len(w) + 2 for w in g) for g in groups]; tot = sum(chars); dur = end - start
    expect = np.cumsum(chars)[:-1] / tot * dur; picks = []; avail = list(gaps)
    for ex in expect:
        best = max(avail, key=lambda g: g[1] - 25 * abs(g[0] - ex)); picks.append(best[0]); avail.remove(best)
    picks.sort(); bounds = [0.0] + picks + [dur]; out = []
    for g, a, b in zip(groups, bounds[:-1], bounds[1:]):
        out += _spread(g, start + a + (0.03 if a else 0), start + b - (0.05 if b < dur else 0))
    return out


def main(script_path, out):
    from kokoro_onnx import Kokoro
    spec = json.load(open(script_path))
    k = Kokoro(*ensure_model())
    voice, speed = spec.get("voice", "af_heart"), spec.get("speed", 0.98)
    gap_line, gap_scene = spec.get("gap_line", 0.36), spec.get("gap_scene", 0.62)
    t = spec.get("lead_in", 0.05); chunks = [np.zeros(int(SR * t))]; lines = []  # near-zero lead-in: the voice starts on frame 1
    for si, sc in enumerate(spec["scenes"]):
        for li, txt in enumerate(sc["lines"]):
            sp = spec.get("hook", {}).get("speed", speed) if si == 0 else speed  # hook lines can run hotter
            a, _ = k.create(txt, voice=voice, speed=sp, lang="en-us")
            idx = np.where(np.abs(a) > 0.01)[0]; a = a[max(idx[0] - 240, 0):idx[-1] + 480]
            d = len(a) / SR
            lines.append({"scene": si, "text": txt, "start": round(t, 3), "end": round(t + d, 3),
                          "words": word_times(txt, t, t + d, a)})
            last = li == len(sc["lines"]) - 1
            gap = gap_scene if (last or txt.endswith(("?", ":"))) else gap_line
            chunks += [a, np.zeros(int(SR * gap))]; t += d + gap
    os.makedirs(out, exist_ok=True)
    sf.write(os.path.join(out, "voice.wav"), np.concatenate(chunks), SR)
    json.dump({"duration": round(t, 3), "lines": lines}, open(os.path.join(out, "timing.json"), "w"), indent=1)
    print(f"voice: {t:.1f}s")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
