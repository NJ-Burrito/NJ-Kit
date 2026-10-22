// hero_boxes.mjs -- writes hf/snapshots/hero-boxes.json: for every scene
// (`.clip.scene`), seeks the master timeline to the scene's hero-hold time
// and records the bounding box of its `[data-hero]` element plus the stage.
//
// ponytail: hero-hold time = scene midpoint (start + duration*0.5) -- the DNA
// (choreography.md #2) asks for "still and fully visible for >=0.8s of its
// scene" but doesn't name a single instant; midpoint is the cheapest point
// that is inside that hold window for any reasonable choreography. Revisit
// with a real hold-window field on the scene if this ever mis-samples a
// scene whose hero settles very late.
//
// Usage: node hero_boxes.mjs <path/to/hf/index.html>
// Output: <hf-dir>/snapshots/hero-boxes.json  { "<scene-id>": {x,y,w,h}, ... }
import { fileURLToPath } from "node:url";
import path from "node:path";
import fs from "node:fs";
import os from "node:os";
import { createRequire } from "node:module";

// ponytail: this script ships inside a Claude skill dir, not under the
// ENSERA repo, so plain `import "playwright"` can't see ENSERA's
// node_modules (ESM resolution walks up from the importing file's own
// path). Resolve it explicitly from the repo that has it installed.
const require = createRequire(path.join(process.env.ENSERA_ROOT ?? path.join(os.homedir(), "Desktop", "ENSERA"), "package.json"));
const { chromium } = require("playwright");

const htmlPath = process.argv[2];
if (!htmlPath) {
  console.error("usage: node hero_boxes.mjs <path/to/hf/index.html>");
  process.exit(1);
}
const absHtml = path.resolve(htmlPath);
const hfDir = path.dirname(absHtml);
const outDir = path.join(hfDir, "snapshots");

let browser;
try {
  browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  await page.goto("file://" + absHtml.replace(/\\/g, "/"));
  await page.waitForFunction(() => window.__timelines && Object.keys(window.__timelines).length > 0);

  const scenes = await page.$$eval(".clip.scene[id]", (els) =>
    els.map((el) => ({
      id: el.id,
      start: parseFloat(el.dataset.start || "0"),
      duration: parseFloat(el.dataset.duration || "0"),
    }))
  );

  const boxes = {};
  const noHero = [];
  for (const scene of scenes) {
    const t = scene.start + scene.duration * 0.5;
    await page.evaluate((time) => {
      const tl = window.__timelines["main"] || Object.values(window.__timelines)[0];
      tl.seek(time, false);
    }, t);
    // rehearsal-0921: CSS.escape does not exist in Node (only in a browser
    // global) -- this ran inside Playwright's Node process, not the page, so
    // it threw on every scene before the fix. HyperFrames scene/element ids
    // are already restricted to [\w-] (the build template requires it), so
    // a plain string is a safe selector without needing real CSS escaping.
    const box = await page.$eval(`#${scene.id} [data-hero]`, (el) => {
      const r = el.getBoundingClientRect();
      return { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) };
    }).catch(() => null);
    if (box) {
      // Light-ground fix (prefilm-fix-0921): a scene whose hero sits on a
      // dark-paper backing shape marks it `data-hero-backing`; record its
      // box too so hero_check.py measures hero-vs-backing and backing-vs-ground.
      const backing = await page.$eval(`#${scene.id} [data-hero-backing]`, (el) => {
        const r = el.getBoundingClientRect();
        return { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) };
      }).catch(() => null);
      boxes[scene.id] = backing ? { ...box, backing } : box;
    } else {
      noHero.push(scene.id);
    }
  }
  const stageBox = await page.$eval("#root", (el) => {
    const r = el.getBoundingClientRect();
    return { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) };
  }).catch(() => null);

  fs.mkdirSync(outDir, { recursive: true });
  fs.writeFileSync(
    path.join(outDir, "hero-boxes.json"),
    JSON.stringify({ ...boxes, __stage: stageBox }, null, 2),
    "utf-8"
  );
  console.log(`hero_boxes: scenes=${scenes.length} boxed=${Object.keys(boxes).length} no_hero=${noHero.length}`);
  if (noHero.length) console.log("NO_HERO: " + noHero.join(", "));
} finally {
  if (browser) await browser.close();
}
