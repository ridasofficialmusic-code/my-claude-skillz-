# script.json: scene spec

```jsonc
{
  "topic": "Why your brain replays embarrassing moments",   // used for the output file slug
  "slug": "why-you-still-cringe",                           // optional override
  "voice": "af_heart", "speed": 1.08,                       // Kokoro voice + speed
  "gap_line": 0.3, "gap_scene": 0.55,                       // pauses (s) after a line / at a scene end or after "?" ":"
  "duration": 51.0,                                         // final length: last spoken word + 0.3 s (loop ending)
  "lead_in": 0.05,                                          // silence before the first word (keep ~0 so frame 1 has voice)
  "hook": {"speed": 1.12, "punch": 1.15, "shake": 14, "caption_size": 96},  // scene-0 voice speed, frame-1 zoom/shake, bigger hook captions
  "scene_punch": 1.06,                                      // small zoom-in on every scene change
  "caption_style": "marker",                                // humanised captions: handwritten phrase strips + highlighter (omit = ransom-note scraps)
  "emphasis": ["deleted", "pickle"],                        // words drawn in terracotta in marker captions
  "caption_y": 1330, "caption_x": 515, "caption_max_w": 880, // TikTok + YouTube safe placement (defaults)
  "mood": "curious", "bpm": 112,                            // music: curious (Am F C G) | bright (C F G Am) | night (Dm Bb F C)
  "scenes": [ { "name": "hook", "bg": "night", "lines": ["..."], "elements": [ ... ] } ],
  "thumbnail": { "bg": "night", "vertical": [ ...elements ], "horizontal": [ ...elements ] }
}
```

Canvas: 1080×1920. Coordinates are the **centre** of each element. Visual zone y 250–1250; captions are drawn automatically at y ≈ 1400. Thumbnails: vertical 1080×1920, horizontal 1280×720. They use the same element types, with `t` (seconds) for dynamic ones.

## Common element fields
| field | meaning |
|---|---|
| `type` | one of the types below |
| `x`, `y`, `rot`, `scale` | position (px), rotation (degrees, + = counter-clockwise), size multiplier |
| `at` | when it appears, scene-relative. Number (s) or anchor: `"amygdala"` (first spoken word starting with this), `"keep#2"` (2nd occurrence), `"One@2"` (first match inside line 2 of the scene; use it when the word also appears earlier), `"line2"` (start of line index 2), `"word+0.3"`, `"end-0.5"`. Omit = scene start (in scene 0 = visible from frame 1). |
| `out` | when it leaves (same anchor syntax); it shrinks out over 0.3 s |
| `anim` | entrance: `pop` (default, stop-motion overshoot), `slide_left`, `slide_right`, `slide_up`, `slide_down`, `none` |
| `loop` | `bob`, `spin` (+`spin_speed` deg/s), `shake` (+`shake_for` s), `pulse`, `wiggle` |
| `jitter` | `false` to disable the stop-motion jitter |
| `from`, `move_dur` | glide from `[x, y]` to `x, y` over `move_dur` s, starting at `at`. Unlike `anim`, it moves on frame 1 in scene 0, so use it for the visual hook. |

Colours: `cream paper mustard terra teal navy sky pink red green night ink skin blush brainpink white` or `[r,g,b]`.

## Element types
| type | params | notes |
|---|---|---|
| `label` | `text`, `size` (90), `font` `bold`/`marker`, `color` (scrap), `fg` (text) | the workhorse: torn-paper text strip. Keep width under 1000 px (about 16 chars at size 70). |
| `bubble` | `text`, `style` `speech`/`thought`, `size` (70), `maxw` (620), `tail` `left`/`right`, `font`, `color`, `fg` | auto-wraps |
| `person` | `mood` `neutral`/`happy`/`sad`/`cringe`/`shock`, `r` (120), `color` (shirt), `hair`, `shirt` (text on shirt) | sprite is about 3r × 5.2r; the head sits about 0.9r above `y` |
| `bed` | `r` (110), `awake` (true), `frame`, `blanket` | a person lying in bed |
| `brain` | `r` (230), `color` | about 3r × 2.4r |
| `alarm` | `r` (120), `color` | flashing siren; pair it with `loop: shake` |
| `clock` | `r` (260), `time` (hours, e.g. 2.0), `speed` (turns/s), `color` | dynamic |
| `sun` / `moon` / `stars` | `r` / `r` / `w`, `h`, `count` | sun rays rotate |
| `circle` / `star` / `heart` | `r`, `color` | basic cut-outs |
| `panel` | `w`, `h`, `color` | a big torn sheet to frame a mini-scene |
| `bookmark` | `w`, `h`, `text`, `color` | ribbon |
| `replay` | `r`, `color` | two circular arrows; use `loop: spin` |
| `play_card` | `w`, `h`, `text` (caption under), `color` | "video" card with a play button |
| `counter` | `from`, `to`, `dur`, `prefix`, `suffix`, `size`, `color` | counts up with ease-in |
| `bars` | `items: [{label, value(0-100), value_text?, color}]`, `stagger` (s between bars), `h`, `bar_w` | animated comparison chart: use it for the study number |
| `tshirt` | `text` (`\n` for lines), `s`, `size`, `color` | |
| `badge` | `kind` `check`/`cross`, `r`, `color` | |
| `arrow` | `len`, `w`, `color` | points right; `rot: -90` points down, `90` points up |
| `spotlight` | `w`, `h`, `color` | translucent cone, no shadow; put it before the person in the list |
| `follow` | `text` ("FOLLOW"), `size`, `color` | CTA button; use `loop: pulse` |
| `comment` | `user`, `text`, `w`, `avatar` | fake comment card for the CTA |
| `note` | `kind` `single`/`double`, `r` (50), `color` | music note; scatter them with `loop: bob` |
| `worm` | `r` (55), `segments` (6), `color`, `headphones` (true) | wiggling earworm mascot |
| `crossword` | `n` (5), `cell` (90) | puzzle grid spelling EAR / WORM |
| `shower` | `s`, `color`, `water` | shower head with falling drops (dynamic) |
| `noodle` | `r` (150), `mood` `happy`/`guilty`/`smug`/`shock`/`think`/`sad`, `pose` `idle`/`wave`/`point`/`point_left`/`shrug`/`hold`/`think`/`walk`, `hold` `pickle`/`note`/`sign` (+`sign` text), `look` [x,y], `talk` (true) | **The mascot.** Lip-syncs to the voice, blinks, and bounces while talking. Change pose or mood by stacking elements with `at`/`out` and `anim: "none"` (instant stop-motion swaps). Feet sit about 1.45r below `y`. |
| `door` | `w`, `h`, `open` (0–1) or `swing` [from, to, seconds], `color`, `frame`, `inside` | hinged paper door |
| `pickle` | `r`, `face` | standalone pickle (Noodle can also `hold` one) |
| `shreds` | `spread`, `fall`, `count`, `colors`, `seed` | falling torn paper; `y` = start point + fall/2 |
| `scissors` | `s`, `snip` (true) | snipping scissors |
| `box` | `part` `back`/`front`, `w`, `h`, `text`, `color` | put sliding items between the back and front to drop them "into" the box |
| `calendar` | `top`, `text`, `w`, `h`, `color` | tear-off calendar page |

Elements draw in list order (later = on top). Need a new prefab? Add a function to `scripts/render.py` with `@prefab("name")` (or `dynamic=True` if it animates). Build it from `Canvas.blob/rect/poly/line/text` so it keeps the torn-paper look.
