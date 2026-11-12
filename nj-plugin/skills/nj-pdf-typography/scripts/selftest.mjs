#!/usr/bin/env node
/**
 * Prove the whole chain, end to end, in one command.
 *
 * Renders the example document, then reads back the PDF's own font list and the
 * text that copies out of it. If this passes, the vault is intact, the faces
 * embed, the header and footer carry a real font, and Arabic survives a round
 * trip. If it fails it says which of those broke.
 *
 *   node selftest.mjs            # in the vault's recommended face
 *   node selftest.mjs Cairo      # or any family, to see one fail
 *
 * Runs from any directory: the skill carries its own playwright under
 * `node_modules/`, so it no longer has to be invoked from a project that
 * happens to have one.
 */
import { readFile } from 'node:fs/promises';
import { spawnSync } from 'node:child_process';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { tmpdir } from 'node:os';
import { renderPdf } from './render-pdf.mjs';

const HERE = dirname(fileURLToPath(import.meta.url));
// Cairo is the house face as of 2026-09-03 and the only family left in the
// vault, so it is also the default here. Note what that costs: the previous
// default was Amiri, which returns every Arabic word whole when a reader
// copies a paragraph out of the PDF, and Cairo does not — see the note in
// SKILL.md. This test is expected to report the copy failure; that is the
// test working, not the test being broken.
const fonts = process.argv.slice(2).length ? process.argv.slice(2) : ['Cairo'];
const out = join(tmpdir(), `pdf-typography-selftest-${Date.now()}.pdf`);

// A sentence and a lead-in from the example, checked word by word after the
// round trip. Anything that scrambles letters shows up here.
const EXPECT = [
  'يشرح هذا الدليل كيفية تسجيل الدخول إلى بوابة الأعمال الخاصة بالمؤسسة',
  'المرفقات المطلوبة عند اختيار',
];

console.log(`rendering the example in ${fonts.join(' + ')}\n`);

await renderPdf({
  html: await readFile(join(HERE, '..', 'reference', 'example.html'), 'utf8'),
  out,
  fonts,
  margin: { top: '18mm', bottom: '18mm', left: '16mm', right: '16mm' },
  header: '<div style="width:100%;padding:0 16mm;text-align:start">نموذج ضبط الطباعة</div>',
  footer: '<div style="width:100%;padding:0 16mm;text-align:center">'
        + 'صفحة <span class="pageNumber"></span> من <span class="totalPages"></span></div>',
});

const check = spawnSync(
  process.platform === 'win32' ? 'python' : 'python3',
  [join(HERE, 'check-pdf.py'), out, ...EXPECT.flatMap((e) => ['--expect', e])],
  { encoding: 'utf8', env: { ...process.env, PYTHONUTF8: '1', PYTHONIOENCODING: 'utf-8' } }
);
process.stdout.write(check.stdout ?? '');
process.stderr.write(check.stderr ?? '');

console.log(`\nthe PDF is at ${out} — open it and copy a line out by eye too.`);
process.exit(check.status ?? 1);
