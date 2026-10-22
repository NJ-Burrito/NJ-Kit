#!/usr/bin/env node
/**
 * Render one sentence in several families, one family per page, so their copy
 * behaviour can be compared.
 *
 * Run this before adopting a font for body text. Two families in this vault
 * displace letters *inside* words when the text is extracted — invisible on the
 * page, obvious the moment a reader pastes a paragraph into an email — and the
 * only way to know which is to print a sentence and read it back.
 *
 *   node copy-fidelity.mjs out.pdf                       # every Arabic family
 *   node copy-fidelity.mjs out.pdf Amiri "Readex Pro"    # just these
 *
 * Then score it:  python copy-fidelity.py out.pdf
 *
 * Needs playwright resolvable — run it from inside a project that has it.
 */
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { families, fontCss } from './font-css.mjs';

/** Chosen for the things that go wrong: a lam-alef, a hamza, a lone alef
 *  maqsura, a final full stop, and a word with three joined medial letters. */
const SAMPLE = 'يشرح هذا الدليل كيفية تسجيل الدخول إلى بوابة الأعمال الخاصة بالمؤسسة.';

const out = process.argv[2];
if (!out) {
  console.error('usage: node copy-fidelity.mjs <out.pdf> [family]...');
  process.exit(1);
}
const named = process.argv.slice(3);
const wanted = named.length
  ? named
  : families().filter((f) => f.script === 'ar').map((f) => f.family);

const pages = wanted
  .map((f) => `<section style="font-family:'${f}'"><p>${SAMPLE}</p></section>`)
  .join('\n');

const html = `<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><style>
${fontCss(wanted, { weights: [400], italics: false })}
body{margin:0;font-size:13pt;line-height:1.9}
section{break-after:page;padding:12mm}
</style></head><body>${pages}</body></html>`;

const browser = await chromium.launch();
const page = await browser.newPage();
await page.setContent(html, { waitUntil: 'load' });
await page.evaluate(() => document.fonts.ready);

const missing = await page.evaluate(
  (names) => names.filter((n) => !document.fonts.check(`13pt "${n}"`)), wanted);
if (missing.length) {
  await browser.close();
  throw new Error(`fonts did not load: ${missing.join(', ')}`);
}

await page.pdf({ path: out, format: 'A4', tagged: true,
  margin: { top: '10mm', bottom: '10mm', left: '10mm', right: '10mm' } });
await browser.close();

// The scorer needs to know which page is which family.
writeFileSync(out.replace(/\.pdf$/, '') + '.pages.json',
  JSON.stringify({ sample: SAMPLE, families: wanted }, null, 2));
console.log(`${wanted.length} families → ${out}`);
