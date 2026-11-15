// Render a three.js scene page frame by frame in headless Chromium and pipe it to ffmpeg with the narration.
// Usage (from the repo root):
//   node lib/render3d.js <scene.html> <work_dir_with_timeline_and_narration> <out.mp4> [fps=20] [maxSeconds=0]
// The page must define window.ready = true, window.setup(timeline) and window.renderAt(seconds).
// It is served from the repo root, so it can import "three" via the importmap in lib/stage3d.js examples.
const { chromium } = require("playwright");
const { spawn } = require("child_process");
const http = require("http"), fs = require("fs"), path = require("path");

const ROOT = path.resolve(__dirname, "..");
const [SCENE, WORK, OUT] = process.argv.slice(2, 5).map(p => path.resolve(p));
const FPS = Number(process.argv[5] || 20), MAXS = Number(process.argv[6] || 0);
if (!SCENE || !WORK || !OUT) { console.error("usage: node lib/render3d.js scene.html work_dir out.mp4 [fps] [maxSeconds]"); process.exit(2); }
const tl = JSON.parse(fs.readFileSync(path.join(WORK, "timeline.json")));
const total = MAXS ? Math.min(MAXS, tl.total) : tl.total;
process.env.NO_PROXY = [process.env.NO_PROXY, "127.0.0.1", "localhost"].filter(Boolean).join(",");

const types = { ".html": "text/html", ".js": "text/javascript", ".mjs": "text/javascript", ".json": "application/json", ".png": "image/png" };
const server = http.createServer((req, res) => {
  const f = path.join(ROOT, decodeURIComponent(req.url.split("?")[0]));
  if (!f.startsWith(ROOT)) { res.writeHead(403); return res.end(); }
  fs.readFile(f, (e, d) => { if (e) { res.writeHead(404); return res.end(); }
    res.writeHead(200, { "Content-Type": types[path.extname(f)] || "application/octet-stream" }); res.end(d); });
});

(async () => {
  await new Promise(r => server.listen(0, "127.0.0.1", r));
  const port = server.address().port;
  const browser = await chromium.launch({ args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
  let pageErrors = 0;
  page.on("console", m => { if (m.type() === "error") { pageErrors++; console.error("page:", m.text()); } });
  page.on("pageerror", e => { pageErrors++; console.error("pageerror:", e.message); });
  const url = `http://127.0.0.1:${port}/${path.relative(ROOT, SCENE).split(path.sep).join("/")}`;
  await page.goto(url);
  await page.waitForFunction(() => window.ready === true, null, { timeout: 60000 });
  await page.evaluate((t) => window.setup(t), tl);

  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  const ff = spawn("ffmpeg", ["-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", String(FPS), "-i", "-",
    "-i", path.join(WORK, "narration.wav"), "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-pix_fmt", "yuv420p",
    "-c:a", "aac", "-b:a", "96k", "-shortest", "-movflags", "+faststart", OUT], { stdio: ["pipe", "inherit", "inherit"] });

  const n = Math.round(total * FPS), t0 = Date.now();
  const checks = new Set([0.1, 0.35, 0.6, 0.85].map(f => Math.round(n * f)));
  for (let i = 0; i < n; i++) {
    await page.evaluate((t) => window.renderAt(t), i / FPS);
    const buf = await page.screenshot({ type: "jpeg", quality: 92 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once("drain", r));
    if (checks.has(i)) fs.writeFileSync(path.join(path.dirname(OUT), `check3d_${i}.jpg`), buf);
    if (i % (FPS * 10) === 0) console.log(`frame ${i}/${n}  ${((Date.now() - t0) / 1000).toFixed(0)}s`);
  }
  ff.stdin.end();
  const code = await new Promise(r => ff.on("close", r));
  await browser.close(); server.close();
  if (code) { console.error("ffmpeg failed", code); process.exit(1); }
  console.log(`3D video ${total.toFixed(1)}s, ${n} frames in ${((Date.now() - t0) / 1000).toFixed(0)}s -> ${OUT}` + (pageErrors ? ` (${pageErrors} page errors)` : ""));
})().catch(e => { console.error(e); server.close(); process.exit(1); });
