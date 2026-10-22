// Diagnostic twin of visual_gate.mjs check 7 (same thresholds, same containment exemption), but
// uncapped and located: prints slide page, both boxes and a text snippet for every overlapping pair.
// usage: node overlap_probe.mjs <url>
import { chromium } from "playwright";
const url = process.argv[2];
const browser = await chromium.launch({ channel: "chrome" });
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
await page.goto(url, { waitUntil: "load" });
await page.evaluate(() => document.fonts.ready);
await page.waitForTimeout(1500);
const out = await page.evaluate(() => {
  const els = [...document.querySelectorAll("body *")].filter((el) => {
    const r = el.getBoundingClientRect();
    if (r.width < 2 || r.height < 2) return false;
    const p = getComputedStyle(el).position;
    return p !== "fixed" && p !== "sticky";
  });
  const res = [];
  const d = (el, r) => `${el.tagName.toLowerCase()}[${Math.round(r.left)},${Math.round(r.top % 1080)} ${Math.round(r.width)}x${Math.round(r.height)}] "${(el.textContent || "").trim().slice(0, 30)}"`;
  for (let i = 0; i < els.length; i++) for (let j = i + 1; j < els.length; j++) {
    const a = els[i], b = els[j];
    if (a.contains(b) || b.contains(a)) continue;
    const ra = a.getBoundingClientRect(), rb = b.getBoundingClientRect();
    const ix = Math.max(0, Math.min(ra.right, rb.right) - Math.max(ra.left, rb.left));
    const iy = Math.max(0, Math.min(ra.bottom, rb.bottom) - Math.max(ra.top, rb.top));
    if (ix <= 0 || iy <= 0) continue;
    const inter = ix * iy, sm = Math.min(ra.width * ra.height, rb.width * rb.height), vf = iy / Math.min(ra.height, rb.height);
    if (inter / sm > 0.3 || vf > 0.5) res.push(`page ${Math.floor(ra.top / 1080) + 1}: ${d(a, ra)} <> ${d(b, rb)}`);
  }
  return res;
});
console.log(out.length + " overlapping pairs");
for (const l of out) console.log(l);
await browser.close();
