#!/usr/bin/env node
/* NJ-MULTIMEDIA frame probe: seek a HyperFrames composition to given times, screenshot each, and FAIL on
     - an element carrying data-axis="center" | "left:<px>" | "right:<px>" more than --tol px (default 1) off its axis
       (measured on the text's own box for text, the element box otherwise; only while visible),
     - any rendered face whose family does not match --font (Chrome's real platform fonts via CDP, not the CSS),
     - Arabic on-screen text with tashkeel, tatweel, Persian letters, Latin , ; ? beside Arabic, or Arabic-Indic digits,
     - any page error.
   node frame_probe.mjs <index.html> --times 0,1.5,10 [--font Thmanyah] [--tol 1] [--out dir] [--stage "#stage"] [--hash nograin]
   Playwright: resolved from PLAYWRIGHT_DIR, the current folder, or the composition's folder (npm i -D playwright).
   Exit 0 PASS, 1 FAIL. Writes <out>/report.json and t<sec>.png per time. Headless, throwaway profile, always closed. */
import { createRequire } from "node:module";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { pathToFileURL } from "node:url";

const argv = process.argv.slice(2);
const file = argv.find((a, i) => !a.startsWith("--") && !(argv[i - 1] || "").startsWith("--"));
const opt = (k, d) => { const i = argv.indexOf(k); return i >= 0 ? argv[i + 1] : d; };
if (!file) { console.log("usage: node frame_probe.mjs <index.html> --times 0,1.5 [--font Thmanyah] [--tol 1] [--out dir]"); process.exit(1); }
const html = path.resolve(file);
const times = String(opt("--times", "0")).split(",").map(Number).filter((x) => !Number.isNaN(x));
const fontRe = new RegExp(opt("--font", "Thmanyah"), "i");
const tol = Number(opt("--tol", "1"));
const out = path.resolve(opt("--out", path.join(path.dirname(html), "..", "review", "frames")));
const stageSel = opt("--stage", "");

function loadPlaywright() {
  const bases = [process.env.PLAYWRIGHT_DIR, process.cwd(), path.dirname(html)].filter(Boolean);
  for (const b of bases) {
    try { return createRequire(path.join(path.resolve(b), "package.json"))("playwright"); } catch {}
    try { return createRequire(path.join(path.resolve(b), "index.js"))(path.resolve(b)); } catch {}
  }
  console.log("FAIL playwright not found: set PLAYWRIGHT_DIR to a folder with node_modules/playwright, or npm i -D playwright");
  process.exit(1);
}
const { chromium } = loadPlaywright();

const src = fs.readFileSync(html, "utf8");
const W = +(/data-width="(\d+)"/.exec(src) || [0, 1920])[1];
const H = +(/data-height="(\d+)"/.exec(src) || [0, 1080])[1];
fs.mkdirSync(out, { recursive: true });
const profile = fs.mkdtempSync(path.join(os.tmpdir(), "mm-probe-"));
const ctx = await chromium.launchPersistentContext(profile, { headless: true, viewport: { width: W, height: H } });
const report = { file: html, size: [W, H], times, axis: [], fonts: {}, fontFaults: [], arabic: [], errors: [] };
try {
  const page = await ctx.newPage();
  page.on("pageerror", (e) => report.errors.push(String(e)));
  page.on("console", (m) => { if (m.type() === "error" && !/^Unsafe attempt to load URL file:/.test(m.text())) report.errors.push(m.text()); }); // Chrome file:// origin noise, not a page fault
  await page.goto(pathToFileURL(html).href + (opt("--hash", "") ? "#" + opt("--hash", "") : ""));
  await page.evaluate(() => document.fonts.ready);
  const hasTl = await page.waitForFunction(() => window.__timelines && Object.keys(window.__timelines).length, null, { timeout: 8000 }).then(() => true).catch(() => false);
  if (!hasTl) report.errors.push("no window.__timelines: not a HyperFrames composition, or it failed to start");
  const cdp = await ctx.newCDPSession(page);
  await cdp.send("DOM.enable"); await cdp.send("CSS.enable");

  for (const t of times) {
    const snap = await page.evaluate(({ t, stageSel }) => {
      const tl = window.__timelines && Object.values(window.__timelines)[0];
      if (tl) tl.seek(t, false);
      const stage = (stageSel && document.querySelector(stageSel)) || document.getElementById("stage") || document.querySelector("[data-composition-id]") || document.body;
      const sr = stage.getBoundingClientRect();
      const visible = (el) => { for (let e = el; e && e !== document; e = e.parentElement) { const cs = getComputedStyle(e); if (cs.display === "none" || cs.visibility === "hidden" || +cs.opacity === 0) return false; } const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
      const box = (el) => { if (el.textContent.trim() && !el.querySelector("svg,img,canvas")) { const r = document.createRange(); r.selectNodeContents(el); return r.getBoundingClientRect(); } return el.getBoundingClientRect(); };
      const axis = [];
      for (const el of stage.querySelectorAll("[data-axis]")) {
        if (!visible(el)) continue;
        const b = box(el), spec = el.dataset.axis, x0 = b.left - sr.left, x1 = b.right - sr.left;
        let off;
        if (spec === "center") off = (x0 + x1) / 2 - sr.width / 2;
        else if (spec.startsWith("left:")) off = x0 - +spec.slice(5);
        else if (spec.startsWith("right:")) off = (sr.width - x1) - +spec.slice(6);
        else continue;
        axis.push({ id: el.id || el.className || el.tagName, text: el.textContent.trim().slice(0, 40), spec, off: Math.round(off * 100) / 100 });
      }
      document.querySelectorAll("[data-mmg]").forEach((e) => e.removeAttribute("data-mmg"));
      const w = document.createTreeWalker(stage, NodeFilter.SHOW_TEXT); const texts = []; let n;
      while ((n = w.nextNode())) if (n.nodeValue.trim()) { texts.push(n.nodeValue.trim()); n.parentElement.setAttribute("data-mmg", "1"); }
      return { axis, texts };
    }, { t, stageSel });
    await page.waitForTimeout(50);
    await page.screenshot({ path: path.join(out, `t${String(t).replace(".", "_")}.png`) });
    for (const a of snap.axis) if (Math.abs(a.off) > tol) report.axis.push({ t, ...a });
    const ar = snap.texts.filter((s) => /[؀-ۿ]/.test(s));
    const bad = { tashkeel: /[ً-ْٰ]/, tatweel: /ـ/, persian: /[کیگپچژ]/, latinPunct: /[؀-ۿ]\s*[,;?]|[,;?]\s*[؀-ۿ]/, arabicIndicDigits: /[٠-٩۰-۹]/ };
    for (const s of ar) for (const [k, re] of Object.entries(bad)) if (re.test(s)) report.arabic.push({ t, rule: k, text: s.slice(0, 60) });
    const { root } = await cdp.send("DOM.getDocument", { depth: -1 });
    const { nodeIds } = await cdp.send("DOM.querySelectorAll", { nodeId: root.nodeId, selector: "[data-mmg]" });
    for (const id of nodeIds) {
      const { fonts } = await cdp.send("CSS.getPlatformFontsForNode", { nodeId: id }).catch(() => ({ fonts: [] }));
      for (const f of fonts) report.fonts[f.familyName] = (report.fonts[f.familyName] || 0) + f.glyphCount;
    }
  }
  report.arabic = [...new Map(report.arabic.map((a) => [a.rule + a.text, a])).values()];
  report.fontFaults = Object.keys(report.fonts).filter((f) => !fontRe.test(f) || /cairo/i.test(f));
} finally {
  await ctx.close();
  fs.rmSync(profile, { recursive: true, force: true });
}
const fail = report.axis.length || report.fontFaults.length || report.arabic.length || report.errors.length;
fs.writeFileSync(path.join(out, "report.json"), JSON.stringify(report, null, 2));
console.log(`${fail ? "FAIL" : "PASS"} frame_probe ${times.length} times | axis faults ${report.axis.length} (tol ${tol}px) | fonts ${JSON.stringify(report.fonts)} non-house ${report.fontFaults.length} | arabic faults ${report.arabic.length} | page errors ${report.errors.length}`);
for (const a of report.axis.slice(0, 10)) console.log(`  axis t=${a.t} ${a.spec} off ${a.off}px  ${a.id} "${a.text}"`);
for (const f of report.fontFaults) console.log(`  font not house: ${f}`);
for (const a of report.arabic.slice(0, 10)) console.log(`  arabic ${a.rule} t=${a.t}: ${a.text}`);
for (const e of report.errors.slice(0, 5)) console.log(`  error: ${e}`);
console.log(`  frames + report: ${out}`);
process.exit(fail ? 1 : 0);
