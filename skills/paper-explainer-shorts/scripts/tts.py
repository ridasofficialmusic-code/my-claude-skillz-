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


def word_times(text, start, end):
    ws = text.split(); wt = [len(w) + 2 for w in ws]; tot = sum(wt); t = start; out = []
    for w, x in zip(ws, wt):
        d = (end - start) * x / tot; out.append({"w": w, "s": round(t, 3), "e": round(t + d, 3)}); t += d
    return out


def main(script_path, out):
    from kokoro_onnx import Kokoro
    spec = json.load(open(script_path))
    k = Kokoro(*ensure_model())
    voice, speed = spec.get("voice", "af_heart"), spec.get("speed", 0.98)
    gap_line, gap_scene = spec.get("gap_line", 0.36), spec.get("gap_scene", 0.62)
    t = 0.3; chunks = [np.zeros(int(SR * t))]; lines = []
    for si, sc in enumerate(spec["scenes"]):
        for li, txt in enumerate(sc["lines"]):
            a, _ = k.create(txt, voice=voice, speed=speed, lang="en-us")
            idx = np.where(np.abs(a) > 0.01)[0]; a = a[max(idx[0] - 240, 0):idx[-1] + 480]
            d = len(a) / SR
            lines.append({"scene": si, "text": txt, "start": round(t, 3), "end": round(t + d, 3),
                          "words": word_times(txt, t, t + d)})
            last = li == len(sc["lines"]) - 1
            gap = gap_scene if (last or txt.endswith(("?", ":"))) else gap_line
            chunks += [a, np.zeros(int(SR * gap))]; t += d + gap
    os.makedirs(out, exist_ok=True)
    sf.write(os.path.join(out, "voice.wav"), np.concatenate(chunks), SR)
    json.dump({"duration": round(t, 3), "lines": lines}, open(os.path.join(out, "timing.json"), "w"), indent=1)
    print(f"voice: {t:.1f}s")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
