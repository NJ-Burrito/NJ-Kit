#!/usr/bin/env node
/**
 * Turn vault families into `@font-face` CSS the PDF pipeline can use.
 *
 * Every face comes out as a base64 `data:` URI, and that is not laziness about
 * paths — it is the one delivery that always works. A page built with
 * `page.setContent()` has no document origin, so a `file:///` font URL is a
 * cross-origin subresource and Chrome refuses it **silently**: the browser
 * substitutes a system font, the PDF embeds that instead, and nothing anywhere
 * says so. A `data:` URI is part of the stylesheet, so there is nothing to
 * refuse. It is also the only form that reaches Chrome's header and footer
 * templates, which are separate documents with no stylesheet of their own.
 *
 *   import { fontCss } from './font-css.mjs';
 *   const css = fontCss(['Amiri', 'IBM Plex Serif']);
 *
 *   node font-css.mjs Amiri "IBM Plex Serif" > fonts.css
 */
import { readFileSync, readdirSync, existsSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

export const VAULT = join(dirname(dirname(fileURLToPath(import.meta.url))), 'fonts');

/**
 * Fonts somebody bought, dropped into `fonts/licensed/` by hand.
 *
 * They have no manifest because no script fetched them, so the file name is the
 * record: `<Family>-<weight>[i].<ttf|otf>`, spaces and all —
 * `AmmanV3 Sans-700.otf`. Anything that does not parse is skipped rather than
 * guessed at; a font whose weight we invented would silently be used for the
 * wrong thing.
 */
function licensed() {
  const dir = join(VAULT, 'licensed');
  if (!existsSync(dir)) return [];

  const files = readdirSync(dir);

  // Chrome cannot embed a CFF font program in a PDF. It falls back to Type 3
  // glyph procedures — one unnamed font object per text run — and says nothing,
  // so the failure is invisible until somebody reads the PDF's font list.
  // Refuse rather than let that ship.
  const cff = files.filter((f) => /\.otf$/i.test(f)
    && !files.includes(f.replace(/\.otf$/i, '.ttf')));
  if (cff.length) {
    throw new Error(
      `these are CFF/OpenType and Chrome will not embed them properly: ${cff.join(', ')}\n` +
      'Convert them first — the outlines are preserved:\n' +
      `  python scripts/otf-to-ttf.py "fonts/licensed/${cff[0]}"`
    );
  }

  const byFamily = new Map();
  for (const file of files) {
    // A .ttf beside a .otf wins; the .otf is then just the original.
    const parsed = /^(.+)-(\d{3})(i?)\.(ttf)$/i.exec(file);
    if (!parsed) continue;
    const [, family, weight, italic, ext] = parsed;
    if (!byFamily.has(family)) {
      byFamily.set(family, {
        family, script: 'licensed', role: 'drop-in', licence: 'see fonts/licensed/README.md',
        note: 'supplied by hand — check its embedding grant before delivering',
        files: [],
      });
    }
    byFamily.get(family).files.push({
      weight: Number(weight),
      style: italic ? 'italic' : 'normal',
      file: `licensed/${file}`,
      format: ext.toLowerCase() === 'otf' ? 'opentype' : 'truetype',
    });
  }
  return [...byFamily.values()];
}

const manifest = () => [
  ...JSON.parse(readFileSync(join(VAULT, 'MANIFEST.json'), 'utf8')),
  ...licensed(),
];

/** Every family in the vault, with its role, script and licence. */
export function families() {
  return manifest().map(({ files, ...rest }) => rest);
}

/**
 * @param {string[]} wanted    family names, exactly as they appear in the manifest
 * @param {object}   [options]
 * @param {number[]} [options.weights]  only these weights (default: all present)
 * @param {boolean}  [options.italics]  include italic faces (default: true)
 */
export function fontCss(wanted, options = {}) {
  const { weights, italics = true } = options;
  const all = manifest();
  const out = [];

  for (const name of wanted) {
    const entry = all.find((e) => e.family === name);
    if (!entry) {
      const near = all.map((e) => e.family).filter((f) => f.toLowerCase().includes(name.toLowerCase().slice(0, 5)));
      throw new Error(`"${name}" is not in the vault.${near.length ? ` Did you mean ${near.join(', ')}?` : ''}`);
    }
    for (const face of entry.files) {
      if (weights && !weights.includes(face.weight)) continue;
      if (!italics && face.style === 'italic') continue;
      const bytes = readFileSync(join(VAULT, face.file)).toString('base64');
      // A CFF-flavoured .otf must be declared as `opentype`; call it truetype
      // and Chrome rejects the face — silently, as it rejects everything else.
      const format = face.format ?? 'truetype';
      const mime = format === 'opentype' ? 'font/otf' : 'font/ttf';
      out.push(
        `@font-face{font-family:'${entry.family}';font-style:${face.style};font-weight:${face.weight};` +
        // `block` rather than `swap`: a print run must never race the fonts and
        // snapshot a page set in the fallback.
        `font-display:block;src:url(data:${mime};base64,${bytes}) format('${format}')}`
      );
    }
  }
  return out.join('\n');
}

// Windows gives argv[1] a drive letter, so the naive `file://${argv[1]}`
// comparison never matches and the CLI silently does nothing.
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const args = process.argv.slice(2);
  if (!args.length) {
    console.error('usage: node font-css.mjs <family>...\n');
    for (const f of families()) console.error(`  ${f.script.padEnd(6)} ${f.role.padEnd(6)} ${f.family}`);
    process.exit(1);
  }
  process.stdout.write(fontCss(args) + '\n');
}
