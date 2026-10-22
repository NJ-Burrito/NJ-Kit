#!/usr/bin/env node
/**
 * HTML in, PDF out, with every rule from the skill already applied.
 *
 * The point of this file is that the rules are not optional and not remembered.
 * Fonts arrive as base64 so `setContent` cannot refuse them; loading is awaited
 * *and* asserted, because `fonts.ready` only promises that loading finished, not
 * that it worked; the header and footer templates get their own copy of the
 * faces, since Chrome renders them as separate documents; and the print is
 * tagged. Every one of those was a bug in this project before it was a line here.
 *
 *   import { renderPdf } from './render-pdf.mjs';
 *   await renderPdf({ html, out: 'doc.pdf', fonts: ['Amiri', 'Literata'] });
 *
 *   node render-pdf.mjs page.html doc.pdf --fonts Amiri,Literata --landscape
 *
 * Needs playwright. It is resolved from the current project first, so run it
 * from somewhere that has one installed.
 */
import { readFile, writeFile } from 'node:fs/promises';
import { createRequire } from 'node:module';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { fontCss } from './font-css.mjs';
import { readHouseStyle } from './house-style.mjs';

const HERE = dirname(fileURLToPath(import.meta.url));

/**
 * Find a playwright, wherever it lives.
 *
 * A global skill has no `node_modules` of its own, so the browser has to come
 * from the project being worked in. Anything else would make the skill
 * unusable in exactly the situation it exists for.
 */
async function chromium() {
  const roots = [process.cwd(), join(process.cwd(), '..'), HERE];
  for (const root of roots) {
    for (const pkg of ['playwright', 'playwright-core']) {
      try {
        const req = createRequire(join(root, 'noop.js'));
        const mod = await import(pathToFileURL(req.resolve(pkg)).href);
        // Playwright is CommonJS, so importing it by file URL puts its exports
        // under `default` rather than on the namespace itself.
        const found = mod.chromium ?? mod.default?.chromium;
        if (found) return found;
      } catch { /* try the next one */ }
    }
  }
  throw new Error(
    'playwright not found. The skill normally carries its own copy — restore it ' +
    'with `npm install playwright --no-save` in the skill directory, or run this ' +
    'from a project that has playwright installed.'
  );
}

/** Put a stylesheet into a document that may or may not have a head. */
function injectCss(html, css) {
  const style = `<style data-pdf-typography>\n${css}\n</style>`;
  if (/<\/head>/i.test(html)) return html.replace(/<\/head>/i, `${style}\n</head>`);
  if (/<body[^>]*>/i.test(html)) return html.replace(/<body[^>]*>/i, (m) => `${m}\n${style}`);
  return style + '\n' + html;
}

/**
 * @param {object}   opts
 * @param {string}   opts.html            the document
 * @param {string}   opts.out             where to write the PDF
 * @param {string[]} [opts.fonts]         vault families to embed; defaults to the
 *                                        project's recorded house style
 * @param {string}   [opts.baseCss]       extra CSS, after the faces and the baseline
 * @param {boolean}  [opts.baseline=true] include assets/print-base.css
 * @param {string}   [opts.format='A4']
 * @param {boolean}  [opts.landscape=false]
 * @param {object}   [opts.margin]
 * @param {string}   [opts.header]        header template HTML (Chrome's own classes work)
 * @param {string}   [opts.footer]        footer template HTML
 * @param {string[]} [opts.headerFonts]   families for the templates; defaults to the first of `fonts`
 */
export async function renderPdf(opts) {
  const {
    html, out, baseCss = '', baseline = true,
    format = 'A4', landscape = false, header, footer,
    margin = { top: '16mm', bottom: '16mm', left: '14mm', right: '14mm' },
  } = opts;

  if (!html) throw new Error('renderPdf needs html');
  if (!out) throw new Error('renderPdf needs an output path');

  // A face chosen once is inherited by every later build, which is why it is on
  // disk rather than in an argument. Passing `fonts` overrides it for this run
  // only — it does not rewrite the project's choice; `house-style.mjs --set`
  // does that, deliberately.
  const fonts = opts.fonts?.length ? opts.fonts : readHouseStyle()?.fonts ?? [];
  if (!fonts.length) {
    throw new Error(
      'no font chosen. Ask which face this document should be set in, then record it:\n' +
      '  node house-style.mjs --set "Amiri,Literata" --note "why"\n' +
      'Candidates and their copy-fidelity scores are in reference/families.md.'
    );
  }
  const headerFonts = opts.headerFonts ?? fonts.slice(0, 1);

  const faces = fontCss(fonts);

  /**
   * Bind the chosen faces to the document.
   *
   * Declaring a `@font-face` does not use it, and a face nothing uses is a face
   * Chrome never loads — so without this the document prints in a system font
   * with the vault sitting unused in its head. The first family is the
   * document's voice; a second, if given, takes the Latin, which is what a
   * two-font choice like «Amiri + Literata» means.
   *
   * Both are plain declarations, so any rule in the document's own stylesheet
   * overrides them — as it should.
   */
  const bind = [
    `body{font-family:${fonts.map((f) => `'${f}'`).join(',')},serif}`,
    fonts[1] && `:lang(en),.latin,code,kbd,samp,pre{font-family:'${fonts[1]}','${fonts[0]}',serif}`,
  ].filter(Boolean).join('\n');

  const base = baseline ? await readFile(join(HERE, '..', 'assets', 'print-base.css'), 'utf8') : '';
  const page$ = injectCss(html, [faces, base, bind, baseCss].filter(Boolean).join('\n'));

  const launch = await chromium();
  const browser = await launch.launch();
  try {
    const page = await browser.newPage();
    await page.setContent(page$, { waitUntil: 'load' });

    // Ask for each face by name rather than waiting to see whether the layout
    // happens to need it: a family used only in a heading, or only on page 9,
    // would otherwise not be loaded yet when the check runs.
    const missing = await page.evaluate(async (names) => {
      await Promise.all(names.map((n) => document.fonts.load(`16px "${n}"`).catch(() => {})));
      await document.fonts.ready;
      // The assertion that would have caught every silent fallback in this
      // project. `fonts.ready` resolves just as happily when nothing loaded.
      return names.filter((n) => !document.fonts.check(`16px "${n}"`));
    }, fonts);
    if (missing.length) {
      throw new Error(
        `these faces did not load: ${missing.join(', ')}.\n` +
        'Chrome will have substituted a system font. Check the family name ' +
        'against `node font-css.mjs` and that the vault has that weight.'
      );
    }

    const templates = {};
    if (header || footer) {
      // Separate documents: they inherit nothing, so they get their own faces
      // and their own reset. Regular weight only — nothing here is set in bold
      // and the base64 would double the template for no reason.
      // The `font-family` here is not decoration. A template that declares a
      // face and never binds it renders in Chrome's default — which is how a
      // document set entirely in Amiri still ends up with Arial in its font
      // list, from six words of running head.
      const tplCss = `<style>${fontCss(headerFonts, { weights: [400], italics: false })}
 *{margin:0;font-size:8pt;color:#6B7280;-webkit-print-color-adjust:exact;` +
        `font-family:${headerFonts.map((f) => `'${f}'`).join(',')},serif}</style>`;
      templates.displayHeaderFooter = true;
      templates.headerTemplate = tplCss + (header ?? '<div></div>');
      templates.footerTemplate = tplCss + (footer ?? '<div></div>');
    }

    await page.pdf({
      path: out, format, landscape, margin, printBackground: true,
      // A structure tree: reading order for Acrobat, Word and screen readers.
      tagged: true,
      ...templates,
    });
  } finally {
    await browser.close();
  }
  return out;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const args = process.argv.slice(2);
  const flag = (name, fallback) => {
    const i = args.indexOf(`--${name}`);
    return i === -1 ? fallback : args[i + 1];
  };
  const [input, output] = args.filter((a) => !a.startsWith('--') && !args[args.indexOf(a) - 1]?.startsWith('--'));

  if (!input || !output) {
    console.error('usage: node render-pdf.mjs <in.html> <out.pdf> [--fonts Amiri,Literata] [--landscape] [--format A4]');
    console.error('       without --fonts the project\'s recorded house style is used.');
    process.exit(1);
  }
  const fonts = (flag('fonts', '') || '').split(',').map((s) => s.trim()).filter(Boolean);
  await renderPdf({
    html: await readFile(resolve(input), 'utf8'),
    out: resolve(output),
    ...(fonts.length ? { fonts } : {}),
    format: flag('format', 'A4'),
    landscape: args.includes('--landscape'),
  });
  const used = fonts.length ? fonts : readHouseStyle()?.fonts ?? [];
  console.log(`${output}  ·  set in ${used.join(', ')}${fonts.length ? '' : ' (house style)'}`);
}
