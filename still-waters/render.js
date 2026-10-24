// Renders verse videos frame-by-frame to silent 1080x1920 MP4 (sound gets added in TikTok).
// Usage: node render.js [verse-id | all] [fps]
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const vm = require('vm');

const FPS = +(process.argv[3] || 30);
const sandbox = { window: {} };
vm.runInNewContext(fs.readFileSync(path.join(__dirname, 'verses.js'), 'utf8'), sandbox);
const all = sandbox.window.VERSES.map(v => v.id);
const want = process.argv[2] || 'all';
const ids = want === 'all' ? all : [want];
fs.mkdirSync(path.join(__dirname, 'out'), { recursive: true });

(async () => {
  const browser = await chromium.launch();
  for (const id of ids) {
    if (!all.includes(id)) throw new Error(`unknown verse id: ${id}`);
    const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
    await page.goto(`file://${path.join(__dirname, 'index.html')}?render=1&v=${encodeURIComponent(id)}`);
    await page.waitForFunction(() => window.__ready);
    const { duration } = await page.evaluate(() => window.__meta);
    const frames = Math.round(duration * FPS);
    const stage = await page.$('#stage');
    const out = path.join(__dirname, 'out', id + '.mp4');

    const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-i', '-',
      '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '16', '-preset', 'slow', '-movflags', '+faststart', out], { stdio: ['pipe', 'inherit', 'inherit'] });
    const done = new Promise((res, rej) => ff.on('close', c => c ? rej(new Error('ffmpeg ' + c)) : res()));
    for (let f = 0; f < frames; f++) {
      await page.evaluate(t => window.__seek(t), f / FPS);
      const buf = await stage.screenshot({ type: 'jpeg', quality: 95 });
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
      if (f % 60 === 0) process.stdout.write(`\r${id}: frame ${f}/${frames}`);
    }
    ff.stdin.end(); await done; await page.close();
    console.log(`\r${id}: wrote ${out} (${duration}s)`);
  }
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
