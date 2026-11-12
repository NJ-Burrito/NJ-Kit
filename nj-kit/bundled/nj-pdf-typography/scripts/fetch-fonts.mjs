#!/usr/bin/env node
/**
 * Fill the font vault.
 *
 * Every family here is open licence (SIL OFL 1.1 or Apache 2.0), which is the
 * whole point: a PDF *embeds* the glyphs it draws with, so the file we hand a
 * ministry is a redistribution of the typeface. Segoe UI, Dubai and the rest of
 * the Windows library are licensed for use on Windows, not for embedding in a
 * document we then send somewhere else — reaching for them because they were
 * already installed is how a deliverable acquires a licence problem nobody
 * looks at until it matters.
 *
 * Files are fetched as TrueType, not WOFF2. Google's CSS API serves whichever
 * the caller's User-Agent can handle, and an old UA gets the original .ttf;
 * PDF has no notion of WOFF, so a .ttf is the format that goes in unaltered and
 * the one fonttools can inspect afterwards.
 *
 *   node fetch-fonts.mjs             refresh anything missing
 *   node fetch-fonts.mjs --force     re-download everything
 *   node fetch-fonts.mjs Cairo Inter just those families
 */
import { mkdir, writeFile, readFile, access } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const VAULT = join(dirname(dirname(fileURLToPath(import.meta.url))), 'fonts');

/**
 * A bare UA, and it has to be exactly this bare.
 *
 * Google's CSS API tailors its answer to what the caller can render. A modern
 * UA gets woff2 split into a dozen unicode-range subsets — for Noto Sans Arabic
 * that is one file for Arabic, one for maths, one for symbols, one for
 * latin-ext, each a partial font. Chrome stitches those together happily; a PDF
 * cannot, and a build that grabbed the wrong subset would embed a font with no
 * Arabic in it at all. `Mozilla/5.0` with nothing after it gets a single
 * whole-font .ttf per weight, which is the only shape worth having here.
 */
const LEGACY_UA = 'Mozilla/5.0';

/**
 * The roster.
 *
 * `role` is not decoration — it is what the CSS generator keys on, so a build
 * asks for a role and gets a family rather than naming files by hand.
 */
/**
 * The roster — one family.
 *
 * The vault held twenty-six families and was pruned to Cairo on 2026-09-03 at
 * the client's instruction: «download Google font Cairo, all of its variations
 * in English and Arabic, delete any other fonts you have, and use this one as
 * the primary for all documents.» The other 108 files are in the recycle bin,
 * restorable; the Google-served ones also come back with one command.
 *
 * One family is a real constraint, not a tidy-up: a document set in one face
 * cannot drift between faces, and a build cannot silently fall back to a
 * second. The cost is that comparing candidates now needs a re-fetch first —
 * `fetch-fonts.mjs "Scheherazade New"` still works, because the API is Google's
 * and not this file's.
 *
 * `role` is what the CSS generator keys on, so a build asks for a role and gets
 * a family rather than naming files by hand.
 */
const ROSTER = [
  { family: 'Cairo', script: 'ar', role: 'ui',
    weights: [200, 300, 400, 500, 600, 700, 800, 900], licence: 'OFL-1.1',
    note: 'The house face for every document. Arabic and Latin drawn together in one family, eight weights — so a mixed line needs no fallback and no second family has to be kept in step.' },
];

const slug = (s) => s.replace(/\s+/g, '');

async function exists(p) {
  try { await access(p); return true; } catch { return false; }
}

/** Ask Google for one family and return its parsed @font-face records. */
async function faces(entry) {
  const axis = entry.italics
    ? 'ital,wght@' + entry.weights.flatMap((w) => [`0,${w}`, `1,${w}`]).join(';')
    : 'wght@' + entry.weights.join(';');
  const url = `https://fonts.googleapis.com/css2?family=${encodeURIComponent(entry.family)}:${axis}&display=block`;

  const res = await fetch(url, { headers: { 'User-Agent': LEGACY_UA } });
  if (!res.ok) throw new Error(`${entry.family}: CSS API answered ${res.status}`);
  const css = await res.text();

  // A unicode-range in the answer means we were served subsets, not fonts.
  // Fail rather than quietly save a quarter of a typeface under a full name.
  if (/unicode-range/.test(css)) throw new Error(`${entry.family}: served as subsets, not whole fonts`);

  const out = [];
  for (const block of css.split('@font-face').slice(1)) {
    const weight = /font-weight:\s*(\d+)/.exec(block)?.[1];
    const style = /font-style:\s*(\w+)/.exec(block)?.[1] ?? 'normal';
    const src = /url\((https:[^)]+\.ttf)\)/.exec(block)?.[1];
    if (!weight || !src) continue;
    if (out.some((f) => f.weight === Number(weight) && f.style === style)) continue;
    out.push({ weight: Number(weight), style, src });
  }
  if (!out.length) throw new Error(`${entry.family}: no @font-face blocks came back`);
  return out;
}

const only = process.argv.slice(2).filter((a) => !a.startsWith('--'));
const force = process.argv.includes('--force');
const wanted = only.length
  ? ROSTER.filter((e) => only.some((o) => e.family.toLowerCase().includes(o.toLowerCase())))
  : ROSTER;

const manifest = [];
let fetched = 0, kept = 0;

for (const entry of wanted) {
  const dir = join(VAULT, entry.script);
  await mkdir(dir, { recursive: true });

  let list;
  try {
    list = await faces(entry);
  } catch (err) {
    console.error(`  ✗ ${entry.family} — ${err.message}`);
    continue;
  }

  const files = [];
  for (const face of list) {
    const name = `${slug(entry.family)}-${face.weight}${face.style === 'italic' ? 'i' : ''}.ttf`;
    const path = join(dir, name);
    if (!force && (await exists(path))) { kept++; files.push({ ...face, file: `${entry.script}/${name}` }); continue; }
    const bin = await fetch(face.src, { headers: { 'User-Agent': LEGACY_UA } });
    if (!bin.ok) { console.error(`  ✗ ${name} — ${bin.status}`); continue; }
    await writeFile(path, Buffer.from(await bin.arrayBuffer()));
    fetched++;
    files.push({ ...face, file: `${entry.script}/${name}` });
  }
  console.log(`  ✓ ${entry.family.padEnd(22)} ${files.length} face(s)`);
  manifest.push({ ...entry, files: files.map(({ src, ...f }) => f) });
}

// Anything hand-dropped into fonts/licensed keeps its own record, written by
// hand — this script must never invent a licence it has not read.
const licencedNote = join(VAULT, 'licensed', 'README.md');
if (!(await exists(licencedNote))) {
  await mkdir(join(VAULT, 'licensed'), { recursive: true });
  await writeFile(licencedNote, [
    '# Licensed fonts (drop-in)',
    '',
    'Fonts that cannot be downloaded automatically because somebody sells them.',
    'Put the `.ttf`/`.otf` files here, one per weight, named',
    '`<Family>-<weight>[i].ttf` — e.g. `FFAmmanSerif-400.ttf`.',
    '',
    'Before you do: check the licence covers **embedding in a document**, which',
    'is a separate grant from installing the font. A desktop licence usually',
    'permits it; a webfont-only licence usually does not.',
    '',
    '## FF Amman Sans / FF Amman Serif',
    '',
    'Yanone, 2010, published by FontFont — now Monotype. One of the very few',
    'families drawn bilingually from scratch: Arabic and Latin in the same file,',
    'and the first with true Arabic italics. Seven sans weights, four serif.',
    'Because the Latin is *in* the family, "Amman in English" needs no separate',
    'font — buy the family and both scripts are there.',
    '',
    'It is commercial. The `Amman V3` files circulating on the free-download',
    'sites are repackaged copies of it, and a document embedding one is',
    'distributing an unlicensed typeface. Buy it from Monotype, drop the files',
    'here, and `make-font-css.mjs` will pick them up on its own.',
    '',
    'Until then the open stand-ins are **Amiri** for the Arabic and **Literata**',
    'for the Latin.',
    '',
  ].join('\n'));
}

/**
 * A named fetch adds to the vault. It must never subtract from it.
 *
 * `manifest` holds only the families this run touched, so writing it straight
 * out after `fetch-fonts.mjs Amiri` left the index listing one family and every
 * other face on disk invisible — `font-css.mjs` then answers «"Amiri" is not in
 * the vault» about fonts sitting right there. The files were never at risk; the
 * index was, and the index is what every build reads.
 *
 * So a run merges: what it fetched wins for those families, and every other
 * entry already on file is kept.
 */
let previous = [];
try {
  previous = JSON.parse(await readFile(join(VAULT, 'MANIFEST.json'), 'utf8'));
} catch {
  previous = [];
}
/**
 * …and it must not keep an entry whose files are gone.
 *
 * The merge above was added so a named fetch could not truncate the index. The
 * other half of the same rule: a family pruned from the vault has to leave the
 * index too, or `font-css.mjs` offers a face that is no longer on disk and the
 * build fails at the last step with «not in the vault» about a family the index
 * says it has.
 */
const onDisk = (entry) =>
  (entry.files ?? []).length > 0 &&
  entry.files.every((f) => existsSync(join(VAULT, f.file ?? f)));

const touched = new Set(manifest.map((e) => e.family));
const merged = [...previous.filter((e) => !touched.has(e.family) && onDisk(e)), ...manifest].sort(
  (a, b) => ROSTER.findIndex((r) => r.family === a.family) - ROSTER.findIndex((r) => r.family === b.family)
);
await writeFile(join(VAULT, 'MANIFEST.json'), JSON.stringify(merged, null, 2) + '\n');
console.log(`\n${fetched} downloaded, ${kept} already present → ${VAULT}`);
