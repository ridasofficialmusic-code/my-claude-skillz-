# Kinetic Money: rise-and-grind kinetic typography

9:16 (1080×1920) kinetic-type template for a money and motivation channel. Black background, a gold and white palette, the Anton display font, camera shake and flashes on each slam, gold dust and film grain.

- `index.html`: the whole animation. Open it in a browser to preview (click or press space to pause, click the bar to scrub).
- `render.js`: renders it frame by frame to MP4 and adds a sub-boom and whoosh sound effect on every impact.

```bash
node render.js out/rise-and-grind.mp4 30   # needs playwright + ffmpeg
```

## Editing
Each entry in `SCENES` is one beat: `len` (seconds), `impacts` (local times that trigger shake and booms), optional `flashes`, `build()` (creates the text) and `update(lt)` (animates it). To change the script, edit the strings in `build()`. Swap `@YOURCHANNEL` in the last scene for your handle.

The sound effects are only impact hits. Add your music bed or voiceover in your editor, or ask Claude to sync the cuts to a track's beats.
