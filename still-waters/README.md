# Still Waters Daily: verse video template

Silent 1080×1920 / 30fps verse videos for TikTok. Add the sound in the TikTok app.

**Flow (about 14s, loops seamlessly):** a hook line, then the series tag and reference, then the verse revealed word by word. The keyword glows gold and the closing phrase turns to warm italics. Then a hold, a share CTA, and a fade back to the opening frame.

## Add a verse
Add an entry to `verses.js` with these fields:
- `id`, `day`, `ref` and `translation`
- `hook`: the short opening line
- `lines`: how the verse breaks across lines on screen
- `keyword`: the word(s) that glow gold
- `emphasis`: the words on the last line set in warm italics
- `cta`: the closing call to action

## Render
```bash
node render.js galatians-6-9   # one video  → out/galatians-6-9.mp4
node render.js all             # every verse
```
Open `index.html?v=<id>` in a browser to preview. Click to pause, and click the bar to scrub.

Scenes are drawn in code (`golden-hour` so far). The background motion is periodic over the clip length, so the last frame flows straight into the first.
