---
name: paper-explainer-shorts
description: Make a finished 60-second YouTube Short in the "paper cut-out" explainer style (torn-paper collage, stop-motion jitter, ransom-note captions, AI voiceover, marimba music) for the everyday-psychology niche ("the weird science of being human"). Produces the video, voiceover, vertical + 16:9 thumbnails, and an upload kit (titles, description, hashtags, keywords, pinned comment). Use when the user asks for a short, reel, TikTok, explainer video, or "another one" in this style, or gives a topic like "why do songs get stuck in your head".
---

# Paper Explainer Shorts

One topic in, one upload-ready Short out. Everything renders locally (Python + Pillow + ffmpeg + Kokoro offline TTS), so it works without paid APIs.

**Look:** warm kraft-paper background, torn-edge cut-out shapes with soft shadows, choppy 12 fps stop-motion jitter, a paper sheet sliding up between scenes, word-by-word "ransom note" captions with the spoken word on a mustard scrap, and a torn-paper progress strip along the top.
**Niche:** everyday psychology: relatable "why does my brain do this?" questions answered with real science.

## Workflow

### 0. Setup (once per machine/session)
```bash
bash skills/paper-explainer-shorts/scripts/setup.sh
```

### 1. Pick the topic
If the user didn't give one, choose from `reference/topic-bank.md` or propose a few. A good topic passes all three tests:
- **Relatable:** most viewers have felt it ("that's so me").
- **Unquestioned:** people notice it but never asked *why*.
- **Answerable:** there is solid, citable research behind the explanation.

### 2. Write the script (read `reference/script-formula.md`)
Six scenes: **hook → reason #1 → turn → reason #2 → fix/good news → CTA**. That is 140–160 words, so the voice lands at 55–58 s. Every claim must be well supported; write the sources down for the upload kit. Never invent statistics.

### 3. Write the scene spec
Copy `examples/cringe-memories.json` into the work dir as `script.json` and replace its contents. Schema and every visual element type: `reference/scene-spec.md`. Rules of thumb:
- **Scene 0, first frame:** something must be on screen from frame 1 (elements with no `at`). The hook visual should match the thumbnail.
- **Change the picture every 2–4 s.** Anchor elements to spoken words (`"at": "amygdala"`) so visuals land on the word.
- **Keep the visual zone between y 250 and 1250.** Captions sit at y ≈ 1400, and the bottom ~350 px is covered by the YouTube UI.
- **Use one background colour per scene and alternate them**, e.g. night → cream → red (the turn) → cream → sky → teal (CTA). Avoid `mustard` as a scene background, because the active caption word is mustard.

### 4. Voice first, then check length
```bash
W=<work dir>; S=skills/paper-explainer-shorts/scripts
python3 $S/tts.py $W/script.json $W        # prints "voice: 57.3s"
```
The target is 55–58.5 s. If it's too long, cut words first; otherwise raise `speed` (1.0–1.12) or lower `gap_line`/`gap_scene`. Voices: `af_heart` (default, warm female), `am_michael`/`am_fenrir` (male), `bf_emma` (British female).

### 5. Preview and fix the layout (don't skip this)
```bash
python3 $S/preview.py $W/script.json $W     # -> $W/preview_sheet.png + thumbnails
```
Look at `preview_sheet.png` and the thumbnails. Check for overlaps, text running off the sheet, empty moments, and labels wider than about 1000 px. Fix the coordinates and timings in the spec and preview again. To inspect one frame: `python3 $S/render.py $W/script.json $W still 12.5 out.png`.

### 6. Build
```bash
python3 $S/build.py $W/script.json $W --skip-tts
```
This writes `<slug>_short.mp4` (1080×1920, 30 fps, 60 s, -14 LUFS), `<slug>_voiceover.mp3`, `thumbnail_9x16.png` and `thumbnail_16x9.png`. Rendering takes about 1.5 min on 4 cores. Spot-check a few frames of the final mp4 with ffmpeg before delivering.

### 7. Upload kit
Fill in `templates/upload-kit.md`: 3 title options (≤ 70 chars, with the hook phrase plus #shorts), a description (hook line, 3 emoji bullets, CTA, hashtags), 8–10 hashtags (the first three show above the title), 15–20 keywords, a pinned-comment prompt, and the sources.

### 8. Deliver
Save the files to `AI CONTENT/testers/NN-<slug>/` in the repo (the next number in sequence): the video, voiceover, both thumbnails and `upload-kit.md`, plus the final `script.json` so the video can be re-rendered. Commit, push, and send the video, thumbnails and kit to the user.

## Style rules (keep the channel recognisable)
- Fonts: **Bowlby One** for labels and captions, **Permanent Marker** for handwritten asides.
- Palette names: `cream paper mustard terra teal navy sky pink red green night ink`.
- Recurring beats: a `REASON #1` / `REASON #2` navy label, a `BUT...` turn on a red background, a green `THE GOOD NEWS` label, and a CTA on teal with a comment card plus a pulsing `+ FOLLOW` button.
- Sign-off line: "follow for more weird science of being human."

## Channel art
`python3 scripts/branding.py "AI CONTENT/channel-branding" "Weird Being Human" "the weird science of why you do what you do"` renders `banner_2560x1440.png` (title kept inside YouTube's 1546×423 safe area; check it with `banner_safe-area-check.png`) and `logo_800x800.png` (eye-brain mascot plus initials, circle-safe; `logo_circle-preview.png` shows it at 98 px).
