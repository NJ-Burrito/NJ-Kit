// Agent halo, for any Playwright (Node) script. See ../SKILL.md. No dependencies.
// Only windows opened by NJ-QA carry the halo. No other window gets one (Nader, 2026-11-13): a role that is not one of the crew draws nothing.
const fs = require('fs');
const path = require('path');

const COLOURS = { scavenger: '#38B6FF', tester: '#FF8A1F', leader: '#2EDB82', director: '#FF4D4D', harvester: '#B87CFF',
  // 2026-11-12: the crew grew to 11. Teal for the Batch Monitor; gold, indigo, magenta and olive are the FINAL hues (art lane: brand/palette.md).
  monitor: '#17D4C0', judge: '#FFE23A', scribe: '#4046EE', regression: '#EE3FDA', data: '#B5E61D' };
const HOST_ID = 'nj-qa-halo';
const OUTLINE = { light: '#F7F0FF', dark: '#05030A' }; // the ribbon's outline pair: one of the two separates it from any page
const HIDE = `#${HOST_ID}{display:none!important}`;
const FACES = path.join(__dirname, '..', 'faces'); // the crew member's clay face, a 48 px S cut baked at 2x (redesign/clay/sheets), webp

// THE ONE SWITCH (Nader picked 'c', 2026-11-13): 'a' lit glow edge + face pill, 'b' corner tab badge, 'c' dusk ribbon with an outline.
// Changing it, or the STYLES table below, touches nothing else. NJ_QA_HALO_STYLE overrides it for one run (used by the frames).
const STYLE = 'c';

// Names are small letters; codes such as PROJ-5494 or S-157 stay in capitals (Nader 2026-11-09).
function nameText(name) {
  return String(name || '').trim().split(/\s+/).map((w) => (/^[A-Za-z]+-\d+$/.test(w) ? w.toUpperCase() : w.toLowerCase())).join(' ');
}

const lum = (hex) => {
  const c = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255).map((v) => (v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4));
  return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2];
};
/** Black or white text, whichever reads better on the crew colour. */
const inkOn = (hex) => ((lum(hex) + 0.05) / 0.05 >= 1.05 / (lum(hex) + 0.05) ? '#101216' : '#FFFFFF');
const alpha = (hex, a) => `${hex}${Math.round(a * 255).toString(16).padStart(2, '0')}`;

function faceOf(key) {
  try { return `data:image/webp;base64,${fs.readFileSync(path.join(FACES, `${key}.webp`)).toString('base64')}`; } catch { return ''; }
}

// Each direction is CSS only. Shared parts: .rim (the window edge, at most 28 px deep), .tab (the label at the edge, at most 28 px tall),
// .face (the clay portrait), .dot (state), .type, .who. Everything is pointer-events:none and lives in a closed shadow root.
const COMMON = `
  .rim,.tab{position:fixed;pointer-events:none;box-sizing:border-box}
  .tab{display:flex;align-items:center;white-space:nowrap;max-width:92vw;height:28px;overflow:hidden}
  .face{flex:none;width:28px;height:28px;border-radius:50%;object-fit:cover;background:#1A0E33}
  .type{font:700 15px/1 'Thmanyah Serif Display','Thmanyah Sans',serif;letter-spacing:.05em}
  .who{font:400 12px/1 'Thmanyah Serif Text','Thmanyah Sans',serif;letter-spacing:.01em}
  .dot{flex:none;width:8px;height:8px;border-radius:50%}
  .k,.o,.f{display:none}
  @media (prefers-reduced-motion:reduce){.tab,.dot{animation:none!important}}`;

const STYLES = {
  // (a) a lit glow edge: a 2 px line, a soft inner light 26 px deep, and a glass tab hanging from the top edge with the clay face.
  a: (c) => `
    .rim{inset:0;box-shadow:inset 0 0 0 2px ${c},inset 0 0 0 3px rgba(255,255,255,.2),inset 0 0 26px -3px ${alpha(c, 0.7)},inset 0 0 10px 0 ${alpha(c, 0.35)}}
    .tab{top:0;left:50%;translate:-50% 0;gap:8px;padding:0 14px 0 0;border-radius:0 0 16px 16px;background:rgba(18,20,24,.84);color:#f5f7fa;
      -webkit-backdrop-filter:blur(16px) saturate(170%);backdrop-filter:blur(16px) saturate(170%);
      box-shadow:0 0 0 1px ${c},0 6px 18px rgba(0,0,0,.35),inset 0 -1px 0 rgba(255,255,255,.12);animation:in .26s cubic-bezier(.2,.9,.3,1) both}
    .face{box-shadow:0 0 0 2px ${c}}
    .type{color:${c}} .who{color:rgba(245,247,250,.88)}
    .dot{background:${c};box-shadow:0 0 8px ${c}}
    @keyframes in{from{opacity:0;translate:-50% -8px}to{opacity:1;translate:-50% 0}}
    @media (prefers-reduced-transparency:reduce){.tab{background:#14171c;-webkit-backdrop-filter:none;backdrop-filter:none}}
    @media (prefers-contrast:more){.tab{background:#000}.rim{box-shadow:inset 0 0 0 4px ${c}}}`,
  // (b) a corner tab badge: the colour itself is the badge, a state dot that breathes, and only a thin 2 px edge.
  b: (c, ink) => `
    .rim{inset:0;border:2px solid ${c}}
    .tab{top:0;left:16px;gap:8px;padding:0 12px 0 0;border-radius:0 0 10px 10px;background:${c};color:${ink};box-shadow:0 4px 12px rgba(0,0,0,.3);animation:in .22s ease-out both}
    .face{box-shadow:inset 0 0 0 2px ${ink === '#FFFFFF' ? 'rgba(255,255,255,.9)' : 'rgba(16,18,22,.8)'};border-radius:0 0 0 10px}
    .type{color:${ink}} .who{color:${ink};opacity:.86}
    .dot{background:${ink};box-shadow:0 0 0 3px ${alpha(ink, 0.28)};animation:beat 1.6s ease-in-out infinite}
    @keyframes in{from{opacity:0;translate:0 -8px}to{opacity:1;translate:0 0}}
    @keyframes beat{50%{opacity:.45}}`,
  // (c) a dusk-diorama ribbon (Nader's pick, 2026-11-13) with an OUTLINE so it separates on light and dark pages: a 1 px dark keyline outside, a 1.5 px light outline inside it,
  // then the dusk fill with stars and the role-colour hem. The edge line gets the same pair. All of it sits in the 28 px edge band; nothing reaches into the page.
  c: (c) => `
    .rim{inset:0;border:1px solid ${OUTLINE.dark};box-shadow:inset 0 0 0 1.5px ${OUTLINE.light},inset 0 -4.5px 0 0 ${c},inset 0 0 28px -4px rgba(42,22,80,.92),inset 0 0 14px -2px ${alpha(c, 0.28)}}
    .tab{top:0;left:50%;translate:-50% 0;gap:9px;padding:0 26px 0 18px;color:#F7F0FF;overflow:visible;animation:in .3s cubic-bezier(.2,.9,.3,1) both}
    .k,.o,.f{display:block;position:absolute;clip-path:polygon(0 0,100% 0,calc(100% - 9px) 50%,100% 100%,0 100%,9px 50%)}
    .k{inset:0;background:${OUTLINE.dark}}
    .o{inset:0 1px 1px 1px;background:${OUTLINE.light}}
    .f{inset:0 2.5px 2.5px 2.5px;background:linear-gradient(0deg,${c} 0 2px,#0000 2px),radial-gradient(circle at 78% 30%,#fff8 0 1px,#0000 1.5px),radial-gradient(circle at 90% 70%,#fff6 0 1px,#0000 1.5px),radial-gradient(circle at 60% 22%,#fff5 0 1px,#0000 1.5px),linear-gradient(180deg,#2A1650,#1A0E33)}
    .face,.type,.who,.dot{position:relative;z-index:1}
    .face{width:20px;height:20px;box-shadow:0 0 0 1.5px ${c}}
    .type{color:${c}} .who{color:#C2B3E0}
    .dot{background:${c};box-shadow:0 0 8px ${c}}
    @keyframes in{from{opacity:0;translate:-50% -10px}to{opacity:1;translate:-50% 0}}`,
};

// «TYPE: name». A role that is not one of the crew gets no halo at all (the old catch-all colour is gone, 2026-11-13).
function haloScript(role, name = '', style = process.env.NJ_QA_HALO_STYLE || STYLE) {
  const key = String(role || '').trim().toLowerCase();
  const colour = COLOURS[key];
  if (!colour) return null;
  const css = COMMON + (STYLES[style] || STYLES.a)(colour, inkOn(colour));
  const shown = nameText(name);
  return `(() => {
  const draw = () => {
    if (document.getElementById(${JSON.stringify(HOST_ID)}) || !document.documentElement) return;
    const host = document.createElement('div');
    host.id = ${JSON.stringify(HOST_ID)};
    host.style.cssText = 'position:fixed;inset:0;z-index:2147483647;pointer-events:none';
    const root = host.attachShadow({ mode: 'closed' });
    const css = document.createElement('style');
    css.textContent = ${JSON.stringify(css)};
    const edge = document.createElement('div');
    edge.className = 'rim';
    const tab = document.createElement('div');
    tab.className = 'tab';
    tab.dir = 'ltr';
    for (const n of ['k', 'o', 'f']) { const l = document.createElement('i'); l.className = n; tab.append(l); }
    const face = ${JSON.stringify(faceOf(key))};
    if (face) { const img = document.createElement('img'); img.className = 'face'; img.alt = ''; img.src = face; tab.append(img); }
    const type = document.createElement('span');
    type.className = 'type';
    type.textContent = ${JSON.stringify(`${key.toUpperCase()}:`)};
    tab.append(type);
    if (${JSON.stringify(shown)}) {
      const who = document.createElement('span');
      who.className = 'who';
      who.textContent = ${JSON.stringify(shown)};
      tab.append(who);
    }
    const dot = document.createElement('span');
    dot.className = 'dot';
    tab.append(dot);
    root.append(css, edge, tab);
    document.documentElement.appendChild(host);
  };
  draw();
  new MutationObserver(draw).observe(document, { childList: true, subtree: true });
})();`;
}

// Evidence is captured as if the halo did not exist: page and element screenshots, whole window included (Nader 2026-11-09).
function hideInShots(page) {
  const shot = page.screenshot.bind(page);
  page.screenshot = (o = {}) => shot({ ...o, style: `${o.style || ''}${HIDE}` });
  const proto = Object.getPrototypeOf(page.locator('html'));
  if (!proto.__njHalo) {
    const element = proto.screenshot;
    proto.screenshot = function (o = {}) { return element.call(this, { ...o, style: `${o.style || ''}${HIDE}` }); };
    proto.__njHalo = true;
  }
}

/** Cosmetic: a failure here never reaches the run. */
async function installHalo(context, page, role = process.env.NJ_QA_ROLE, name = process.env.AGENT_NAME) {
  const script = haloScript(role, name);
  if (!script) return;
  try {
    await context.addInitScript(script);
    context.on('page', hideInShots);
    hideInShots(page);
    await page.evaluate(script).catch(() => undefined);
  } catch { /* cosmetic */ }
}

/** The code to pass to the Playwright MCP's browser_run_code_unsafe. Empty when the role is not one of the crew. */
function printCode(role, name) {
  const script = haloScript(role, name);
  if (!script) return '';
  return `async (page) => { const s = ${JSON.stringify(script)}; await page.context().addInitScript(s); await page.evaluate(s); }`;
}

module.exports = { haloScript, nameText, installHalo, printCode, COLOURS, STYLES, STYLE, OUTLINE };

if (require.main === module) {
  if (process.argv[2]) {
    console.log(printCode(process.argv[2], process.argv[3]));
  } else {
    // self-check: node halo.js
    const assert = require('assert');
    assert.ok(haloScript('tester').includes('#FF8A1F'));
    assert.ok(haloScript('Scavenger', 'scav-user').includes('#38B6FF') && haloScript('Scavenger', 'scav-user').includes('"SCAVENGER:"') && haloScript('Scavenger', 'scav-user').includes('"scav-user"'));
    assert.strictEqual(nameText('Tester-R1 proj-5494 s-157'), 'tester-r1 PROJ-5494 S-157');
    assert.strictEqual(nameText('NJ-QA Leader'), 'nj-qa leader');
    assert.ok(haloScript('leader').includes('#2EDB82') && haloScript('director').includes('#FF4D4D'));
    for (const [r, c] of Object.entries({ monitor: '#17D4C0', judge: '#FFE23A', scribe: '#4046EE', regression: '#EE3FDA', data: '#B5E61D' })) {
      assert.ok(haloScript(r, 'x').includes(c) && haloScript(r, 'x').includes(JSON.stringify(`${r.toUpperCase()}:`)), r);
    }
    assert.strictEqual(Object.keys(COLOURS).length, 10, 'ten crew keys carry a halo (the eleventh, Awn, has none)');
    assert.strictEqual(new Set(Object.values(COLOURS)).size, Object.keys(COLOURS).length, 'every crew hue is its own');
    // the catch-all case is gone: a role outside the crew draws nothing
    assert.strictEqual(haloScript('sonnet-lead'), null);
    assert.strictEqual(haloScript('agent', 'x'), null);
    assert.strictEqual(haloScript(''), null);
    assert.strictEqual(haloScript(undefined), null);
    assert.ok(!haloScript('tester', 'a<b>').includes('innerHTML'));
    for (const k of Object.keys(COLOURS)) assert.ok(faceOf(k).length > 1000, `face missing for ${k}`);
    for (const s of Object.keys(STYLES)) {
      const out = haloScript('judge', 'adil PROJ-1', s);
      assert.ok(out.includes('#FFE23A') && out.includes('pointer-events:none') && !new RegExp("silv" + "er", "i").test(out) && !/cairo/i.test(out), `style ${s}`);
    }
    console.log('nj-agent-halo self-check OK');
  }
}
