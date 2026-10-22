// Evidence shot (the owner method 2026-10-18): viewport only, target scrolled in + asserted inside viewport,
// red ring on the exact point (removed after), identity text blacked out. Generic: pass your own mask strings.
import path from 'node:path';
import type { Locator, Page } from '@playwright/test';
const maskJs = (w: string[]) => `(function(){var w=${JSON.stringify(w)};document.querySelectorAll('span,td,a,p,div,label,h1,h2,h3,h4,b,strong').forEach(function(el){if(el.children.length>0)return;var t=el.textContent||'';for(var i=0;i<w.length;i++){if(t.indexOf(w[i])!==-1){el.style.setProperty('background','#000','important');el.style.setProperty('color','#000','important');return;}}});})()`;
/** file name should say what it shows, e.g. 01-send-refused-termination-date-required.png. maskText = header identity + personal row data only, never the point shown. */
export async function evidenceShot(page: Page, file: string, targets: Locator[], maskText: string[] = []) {
  await targets[0].scrollIntoViewIfNeeded();
  if (maskText.length) await page.evaluate(maskJs(maskText));
  const vp = page.viewportSize() ?? (await page.evaluate(() => ({ width: innerWidth, height: innerHeight })));
  for (const [i, t] of targets.entries()) {
    await t.evaluate((el) => { const e = el as HTMLElement; e.setAttribute('data-ev-ring', e.style.outline + '|' + e.style.outlineOffset); e.style.outline = '4px solid #e11d48'; e.style.outlineOffset = '4px'; });
    const b = await t.boundingBox();
    if (!b || b.x < 0 || b.y < 0 || b.x + b.width > vp.width + 1 || b.y + b.height > vp.height + 1) throw new Error(`target ${i} not inside viewport for ${path.basename(file)}`);
  }
  await page.screenshot({ path: file, fullPage: false, animations: 'disabled', timeout: 20_000 });
  await page.evaluate(() => document.querySelectorAll('[data-ev-ring]').forEach((el) => { const e = el as HTMLElement; const [o, f] = (e.getAttribute('data-ev-ring') ?? '|').split('|'); e.style.outline = o; e.style.outlineOffset = f; e.removeAttribute('data-ev-ring'); }));
}
