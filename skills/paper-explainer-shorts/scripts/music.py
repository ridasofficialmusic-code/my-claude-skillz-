"""Paper-style soundtrack: bouncy marimba + shaker/clap, paper rustles on scene changes, ducked under the voice.
Usage: python3 music.py script.json WORK_DIR  -> WORK_DIR/music.wav
"""
import json, os, sys
import numpy as np, soundfile as sf

SR = 48000
PROGRESSIONS = {"bright": [[60, 64, 67], [65, 69, 72], [67, 71, 74], [57, 60, 64]],   # C F G Am
                "curious": [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]],  # Am F C G
                "night": [[50, 53, 57], [46, 50, 53], [53, 57, 60], [48, 52, 55]]}    # Dm Bb F C


def main(spec_path, work):
    spec = json.load(open(spec_path)); timing = json.load(open(os.path.join(work, "timing.json")))
    dur = spec.get("duration", 60.0); n = int(SR * dur); t = np.arange(n) / SR; R = np.random.default_rng(0)
    nf = lambda m: 440 * 2 ** ((m - 69) / 12)

    def tone(m, d, decay, harm, amp):
        tt = np.arange(int(d * SR)) / SR
        return sum(a * np.sin(2 * np.pi * nf(m) * k * tt) for k, a in harm) * np.exp(-tt * decay) * np.minimum(1, tt * 200) * amp

    def add(buf, s, at):
        i = int(at * SR); e = min(i + len(s), n)
        if 0 <= i < n: buf[i:e] += s[:e - i]

    mus = np.zeros(n); bpm = spec.get("bpm", 112); b = 60 / bpm; ch = PROGRESSIONS[spec.get("mood", "curious")]
    for j in range(int(dur / (b / 2))):
        c = ch[int(j * b / 2 / (4 * b)) % 4]; pat = [0, 2, 1, 2, 0, 1, 2, 1]
        add(mus, tone(c[pat[j % 8]] + 12, 0.4, 9, [(1, 1), (4, 0.25), (10, 0.05)], 0.09), j * b / 2)
        if j % 4 == 0: add(mus, tone(c[0] - 12, 0.6, 5, [(1, 1), (2, 0.3)], 0.17), j * b / 2)
        L = int(0.05 * SR); sh = R.normal(0, 1, L) * np.exp(-np.arange(L) / SR * 70) * (0.03 if j % 2 else 0.015)
        add(mus, np.diff(sh, prepend=0), j * b / 2)
        if j % 8 == 4:
            L = int(0.08 * SR); add(mus, R.normal(0, 1, L) * np.exp(-np.arange(L) / SR * 40) * 0.07, j * b / 2)
    starts = sorted({min(l["start"] for l in timing["lines"] if l["scene"] == s) - 0.25 for s in range(1, len(spec["scenes"]))})
    for s in starts:  # paper rustle under each scene change
        L = int(0.35 * SR); add(mus, np.diff(R.normal(0, 1, L), prepend=0) * np.hanning(L) * 0.12, s - 0.05)
    mus *= np.minimum(1, np.minimum(t / 0.4, (dur - t) / 2.0))
    v, vsr = sf.read(os.path.join(work, "voice.wav")); vi = np.abs(np.interp(t, np.arange(len(v)) / vsr, v, right=0))
    k = int(0.15 * SR); env = np.convolve(vi, np.ones(k) / k, "same"); mus *= 1 - 0.45 * np.clip(env * 12, 0, 1)
    sf.write(os.path.join(work, "music.wav"), np.stack([mus, mus], 1).astype(np.float32), SR)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
