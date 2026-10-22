"""One-shot build: script.json -> voiceover, music, video, thumbnails, metadata.
Usage: python3 build.py script.json OUT_DIR [--skip-tts]
Outputs in OUT_DIR: <slug>_short.mp4, <slug>_voiceover.mp3, thumbnail_9x16.png, thumbnail_16x9.png, timing.json
"""
import json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))


def sh(*a): subprocess.check_call(list(a))


def main(spec_path, out, skip_tts=False):
    spec_path = os.path.abspath(spec_path); out = os.path.abspath(out); os.makedirs(out, exist_ok=True)
    spec = json.load(open(spec_path)); slug = spec.get("slug") or re.sub(r"[^a-z0-9]+", "-", spec["topic"].lower()).strip("-")[:48]
    py = sys.executable
    if not skip_tts: sh(py, os.path.join(HERE, "tts.py"), spec_path, out)
    timing = json.load(open(os.path.join(out, "timing.json")))
    if timing["duration"] > spec.get("duration", 60.0) - 0.5:
        raise SystemExit(f"voiceover is {timing['duration']:.1f}s - trim the script or raise 'speed' (target <= {spec.get('duration', 60.0) - 1.5:.0f}s)")
    sh(py, os.path.join(HERE, "music.py"), spec_path, out)
    sh(py, os.path.join(HERE, "render.py"), spec_path, out, "video")
    sh(py, os.path.join(HERE, "render.py"), spec_path, out, "thumbs")
    final = os.path.join(out, f"{slug}_short.mp4"); d = str(spec.get("duration", 60.0))
    sh("ffmpeg", "-y", "-loglevel", "error", "-i", os.path.join(out, "video_silent.mp4"), "-i", os.path.join(out, "voice.wav"), "-i", os.path.join(out, "music.wav"),
       "-filter_complex", "[1:a]aresample=48000,highpass=f=70,acompressor=threshold=-18dB:ratio=3:attack=5:release=80,volume=1.6[v];"
       "[v][2:a]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=9[a]",
       "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-t", d, "-movflags", "+faststart", final)
    sh("ffmpeg", "-y", "-loglevel", "error", "-i", os.path.join(out, "voice.wav"), "-b:a", "192k", os.path.join(out, f"{slug}_voiceover.mp3"))
    for f in ("video_silent.mp4", "music.wav", "parts.txt"):  # voice.wav kept so --skip-tts rebuilds work
        p = os.path.join(out, f)
        if os.path.exists(p): os.remove(p)
    print("done:", final)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], "--skip-tts" in sys.argv)
