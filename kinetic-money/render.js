// Renders index.html frame-by-frame to MP4 and lays impact SFX on every slam.
// Usage: node render.js [out.mp4] [fps]
const { chromium } = require('playwright');
const { spawn, execFileSync } = require('child_process');
const path = require('path');
const fs = require('fs');

const OUT = path.resolve(process.argv[2] || 'out/rise-and-grind.mp4');
const FPS = +(process.argv[3] || 30);
const TMP = path.join(path.dirname(OUT), '.tmp');
fs.mkdirSync(TMP, { recursive: true });

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  await page.goto('file://' + path.join(__dirname, 'index.html') + '?render=1');
  await page.waitForFunction(() => window.__ready);
  const { duration, impacts } = await page.evaluate(() => window.__meta);
  const frames = Math.round(duration * FPS);
  const stage = await page.$('#stage');

  const silent = path.join(TMP, 'video.mp4');
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-i', '-',
    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '17', '-preset', 'medium', silent], { stdio: ['pipe', 'inherit', 'inherit'] });
  const done = new Promise((res, rej) => ff.on('close', c => c ? rej(new Error('ffmpeg ' + c)) : res()));

  for (let f = 0; f < frames; f++) {
    await page.evaluate(t => window.__seek(t), f / FPS);
    const buf = await stage.screenshot({ type: 'jpeg', quality: 95 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (f % 60 === 0) process.stdout.write(`\rframe ${f}/${frames}`);
  }
  ff.stdin.end(); await done; await browser.close();
  console.log(`\rframes done (${frames})`);

  // SFX: a pitch-dropping sub boom with a click transient, plus a short whoosh leading into each impact
  const boom = path.join(TMP, 'boom.wav'), whoosh = path.join(TMP, 'whoosh.wav');
  execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'lavfi', '-i',
    "aevalsrc=exprs='0.85*sin(2*PI*(42*t+110*(1-exp(-22*t))/22))*exp(-4.5*t)+0.3*(random(0)*2-1)*exp(-70*t)':s=48000:d=1.4", boom]);
  execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'lavfi', '-i',
    "aevalsrc=exprs='0.5*(random(0)*2-1)*pow(t/0.22,3)*lt(t,0.22)':s=48000:d=0.22", '-af', 'bandpass=f=1800:width_type=o:w=2', whoosh]);

  const n = impacts.length;
  const parts = [`[0:a]asplit=${n}${impacts.map((_, i) => `[b${i}]`).join('')}`, `[1:a]asplit=${n}${impacts.map((_, i) => `[w${i}]`).join('')}`];
  impacts.forEach((t, i) => {
    parts.push(`[b${i}]adelay=${Math.round(t * 1000)}:all=1[bd${i}]`);
    parts.push(`[w${i}]adelay=${Math.max(0, Math.round((t - .22) * 1000))}:all=1,volume=0.6[wd${i}]`);
  });
  const ins = impacts.map((_, i) => `[bd${i}][wd${i}]`).join('');
  parts.push(`${ins}amix=inputs=${n * 2}:normalize=0,alimiter=limit=0.8,apad,atrim=0:${duration}[a]`);

  execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-i', boom, '-i', whoosh, '-i', silent,
    '-filter_complex', parts.join(';'), '-map', '2:v', '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', OUT]);
  fs.rmSync(TMP, { recursive: true, force: true });
  console.log('wrote', OUT);
})().catch(e => { console.error(e); process.exit(1); });
