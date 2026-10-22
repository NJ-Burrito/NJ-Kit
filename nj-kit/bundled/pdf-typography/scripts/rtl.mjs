#!/usr/bin/env node
/**
 * Putting Latin and digits into an Arabic line without the line coming apart.
 *
 * Left to itself the bidi algorithm resolves neutral characters — brackets,
 * dashes, colons, the space before a number — against whatever surrounds them,
 * so «رقم الطلب 1234567890 (SRS)» renders with its bracket at the wrong end
 * and the number welded to the word beside it. Isolating each Latin *phrase*
 * fixes it; isolating each *word* does not, because the neutrals between the
 * words then resolve outward again.
 *
 * This affects how the line looks, not how it extracts — a mixed line is stored
 * in visual order whatever you do, and every real viewer reorders it on copy.
 * Do it for the rendering; do not expect it to change what pastes out.
 *
 *   import { bidi, esc } from './rtl.mjs';
 *   `<p>${bidi('رقم الطلب 1234567890 ضمن مديرية التدقيق — SRS v1.2')}</p>`
 */

/** HTML-escape. Everything below emits markup, so this comes first. */
export function esc(text) {
  return String(text ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

/**
 * A run of Latin letters, digits and the punctuation that belongs inside it —
 * `SRS v1.2`, `PROJ-UM-LG-001-AR`, `1234567890`, `(ISO 9001)`. Trailing
 * neutrals are handed back to the Arabic, which is where they belong: a full
 * stop after a Latin phrase ends the Arabic sentence, not the phrase.
 */
const LATIN_RUN = /[A-Za-z0-9][A-Za-z0-9 _@#%&/\\.,:;=+*'"()\[\]{}<>|-]*[A-Za-z0-9)\]}]|[A-Za-z0-9]/g;

/**
 * Escape `text` and wrap every Latin/numeric phrase in `<bdi dir="ltr">`.
 * @param {string} text
 * @returns {string} HTML
 */
export function bidi(text) {
  const raw = String(text ?? '');
  let out = '';
  let last = 0;
  for (const match of raw.matchAll(LATIN_RUN)) {
    const start = match.index;
    const end = start + match[0].length;
    out += esc(raw.slice(last, start));
    out += `<bdi dir="ltr">${esc(match[0])}</bdi>`;
    last = end;
  }
  return out + esc(raw.slice(last));
}

if (process.argv[1] && import.meta.url === (await import('node:url')).pathToFileURL(process.argv[1]).href) {
  const text = process.argv.slice(2).join(' ');
  if (!text) {
    console.error('usage: node rtl.mjs "<arabic text with Latin in it>"');
    process.exit(1);
  }
  console.log(bidi(text));
}
