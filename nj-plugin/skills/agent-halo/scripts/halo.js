// Agent halo, for any Playwright (Node) script. See ../SKILL.md. No dependencies.
const COLOURS = { scavenger: '#1e6fff', tester: '#ff7a00', leader: '#12a150', director: '#e01e1e', harvester: '#9b4dff' };
const SILVER = '#c0c0c0';
const HOST_ID = 'nj-qa-halo';
const HIDE = `#${HOST_ID}{display:none!important}`;

// Names are small letters; codes such as PROJ-5494 or S-157 stay in capitals (the owner 2026-11-09).
function nameText(name) {
  return String(name || '').trim().split(/\s+/).map((w) => (/^[A-Za-z]+-\d+$/.test(w) ? w.toUpperCase() : w.toLowerCase())).join(' ');
}

// «TYPE: name». An agent with no assigned type shows AGENT: and its agent-map name.
function haloScript(role, name = '') {
  const text = String(role || '').trim();
  if (!text) return null;
  const key = text.toLowerCase();
  const colour = COLOURS[key] || SILVER;
  const type = COLOURS[key] ? text.toUpperCase() : 'AGENT';
  const shown = nameText(COLOURS[key] ? name : (name || text));
    return `(() => {
  const draw = () => {
    if (document.getElementById(${JSON.stringify(HOST_ID)}) || !document.documentElement) return;
    const host = document.createElement('div');
    host.id = ${JSON.stringify(HOST_ID)};
    host.style.cssText = 'position:fixed;inset:0;z-index:2147483647;pointer-events:none';
    const root = host.attachShadow({ mode: 'closed' });
    // Apple-style (2026-11-09): a thin tinted rim with a soft inner glow, and a floating glass pill.
    // Glass = a dark translucent material with blur, so the label stays legible over any page.
    const css = document.createElement('style');
    css.textContent = \`
      .rim{position:fixed;inset:0;pointer-events:none;box-sizing:border-box;border:3px solid ${colour};
        box-shadow:inset 0 0 0 1px rgba(255,255,255,.18),inset 0 0 28px -6px ${colour};border-radius:10px}
      .pill{position:fixed;top:10px;left:50%;translate:-50% 0;pointer-events:none;white-space:nowrap;display:flex;align-items:center;gap:10px;
        padding:6px 18px 6px 14px;border-radius:999px;background:rgba(18,20,24,.72);color:#f5f7fa;
        -webkit-backdrop-filter:blur(20px) saturate(180%);backdrop-filter:blur(20px) saturate(180%);
        border:1px solid ${colour};box-shadow:0 8px 28px rgba(0,0,0,.35),inset 0 1px 0 rgba(255,255,255,.14);
        animation:in .26s cubic-bezier(.2,.9,.3,1) both}
      .dot{width:10px;height:10px;border-radius:50%;background:${colour};box-shadow:0 0 10px ${colour}}
      .type{font:700 20px/1.2 'Thmanyah Serif Display','Thmanyah Sans',serif;letter-spacing:.04em;color:${colour}}
      .who{font:400 14px/1.2 'Thmanyah Serif Text','Thmanyah Sans',serif;letter-spacing:.01em;color:rgba(245,247,250,.86)}
      @keyframes in{from{opacity:0;scale:.94;filter:blur(6px)}to{opacity:1;scale:1;filter:none}}
      @media (prefers-reduced-motion:reduce){.pill{animation:fade .2s ease both}@keyframes fade{from{opacity:0}}}
      @media (prefers-reduced-transparency:reduce){.pill{background:#14171c;-webkit-backdrop-filter:none;backdrop-filter:none}}
      @media (prefers-contrast:more){.pill{background:#000;border-width:2px}.rim{border-width:4px}}\`;
    const edge = document.createElement('div');
    edge.className = 'rim';
    const tag = document.createElement('div');
    tag.className = 'pill';
    tag.dir = 'ltr';
    const dot = document.createElement('span');
    dot.className = 'dot';
    const type = document.createElement('span');
    type.className = 'type';
    type.textContent = ${JSON.stringify(type)} + ':';
    tag.append(dot, type);
    if (${JSON.stringify(shown)}) {
      const who = document.createElement('span');
      who.className = 'who';
      who.textContent = ${JSON.stringify(shown)};
      tag.append(who);
    }
    root.append(css, edge, tag);
    document.documentElement.appendChild(host);
  };
  draw();
  new MutationObserver(draw).observe(document, { childList: true, subtree: true });
})();`;
}

// Evidence is captured as if the halo did not exist: page and element screenshots, whole window included (the owner 2026-11-09).
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
async function installHalo(context, page, role = process.env.AGENT_ROLE || process.env.NJ_QA_ROLE, name = process.env.AGENT_NAME) {
  const script = haloScript(role, name);
  if (!script) return;
  try {
    await context.addInitScript(script);
    context.on('page', hideInShots);
    hideInShots(page);
    await page.evaluate(script).catch(() => undefined);
  } catch { /* cosmetic */ }
}

/** The code to pass to the Playwright MCP's browser_run_code_unsafe. */
function printCode(role, name) {
  const script = haloScript(role, name);
  return `async (page) => { const s = ${JSON.stringify(script)}; await page.context().addInitScript(s); await page.evaluate(s); }`;
}

module.exports = { haloScript, nameText, installHalo, printCode };

if (require.main === module) {
  if (process.argv[2]) {
    console.log(printCode(process.argv[2], process.argv[3]));
  } else {
    // self-check: node halo.js
    const assert = require('assert');
    assert.ok(haloScript('tester').includes('#ff7a00'));
    assert.ok(haloScript('Scavenger', 'scav-user').includes('#1e6fff') && haloScript('Scavenger', 'scav-user').includes('"SCAVENGER"') && haloScript('Scavenger', 'scav-user').includes('"scav-user"'));
    assert.strictEqual(nameText('Tester-R1 proj-5494 s-157'), 'tester-r1 PROJ-5494 S-157');
    assert.strictEqual(nameText('NJ-QA Leader'), 'nj-qa leader');
    assert.ok(haloScript('leader').includes('#12a150') && haloScript('director').includes('#e01e1e'));
    const other = haloScript('sonnet-lead');
    assert.ok(other.includes(SILVER) && other.includes('"sonnet-lead"') && other.includes('"AGENT"'));
    assert.strictEqual(haloScript(''), null);
    assert.strictEqual(haloScript(undefined), null);
    assert.ok(!haloScript('a<b>').includes('innerHTML'));
    console.log('agent-halo self-check OK');
  }
}
