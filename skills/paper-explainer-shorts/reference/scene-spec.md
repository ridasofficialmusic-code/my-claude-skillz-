# script.json: scene spec

```jsonc
{
  "topic": "Why your brain replays embarrassing moments",   // used for the output file slug
  "slug": "why-you-still-cringe",                           // optional override
  "voice": "af_heart", "speed": 1.08,                       // Kokoro voice + speed
  "gap_line": 0.3, "gap_scene": 0.55,                       // pauses (s) after a line / at a scene end or after "?" ":"
  "duration": 60.0,                                         // final video length
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
| `at` | when it appears, scene-relative. Number (s) or anchor: `"amygdala"` (first spoken word starting with this), `"keep#2"` (2nd occurrence), `"line2"` (start of line index 2), `"word+0.3"`, `"end-0.5"`. Omit = scene start (in scene 0 = visible from frame 1). |
| `out` | when it leaves (same anchor syntax); it shrinks out over 0.3 s |
| `anim` | entrance: `pop` (default, stop-motion overshoot), `slide_left`, `slide_right`, `slide_up`, `slide_down`, `none` |
| `loop` | `bob`, `spin` (+`spin_speed` deg/s), `shake` (+`shake_for` s), `pulse`, `wiggle` |
| `jitter` | `false` to disable the stop-motion jitter |

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
| `calendar` | `top`, `text`, `w`, `h`, `color` | tear-off calendar page |

Elements draw in list order (later = on top). Need a new prefab? Add a function to `scripts/render.py` with `@prefab("name")` (or `dynamic=True` if it animates). Build it from `Canvas.blob/rect/poly/line/text` so it keeps the torn-paper look.
