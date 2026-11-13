// Keeps the halo on the browser windows NJ-QA itself launched, from outside. See ../SKILL.md.
// Only windows opened by NJ-QA carry the halo. No other window gets one (Nader, 2026-11-13).
// Usage: node halo_keeper.js [--once|--ensure]
//   --ensure  starts one in the background if none is running. The ENGINE calls it when it launches a Chrome (engine/lib/halo.ts); no machine hook, no global start.
//   default   a singleton: it ends by itself, GRACE_MS after the last NJ-QA window is gone.
// Which windows: ONLY those in the registry NJ-QA's engine writes, <dir>/<pid>.json {pid, port, profile, role, name}, <dir> = $NJQA_HALO_DIR or <tmp>/njqa-halo.
// Nothing else: not the user's Chrome, not the hub's --app window, not another tool's Playwright Chrome. It only evaluates the (idempotent) drawing script in page targets: it can't press, type or navigate.
const fs = require('fs');
const os = require('os');
const path = require('path');
const { haloScript } = require('./halo.js');

const DRAW_MS = 2000;
const GRACE_MS = 20000;
const REGISTRY = () => process.env.NJQA_HALO_DIR || path.join(os.tmpdir(), 'njqa-halo');
const LOCK = () => path.join(path.dirname(REGISTRY()), 'agent-halo-keeper.pid'); // beside the registry

/** The windows the engine registered and that are still alive. */
function registered() {
  const out = [];
  let files = [];
  try { files = fs.readdirSync(REGISTRY()); } catch { return out; }
  for (const f of files.filter((n) => n.endsWith('.json'))) {
    const file = path.join(REGISTRY(), f);
    try {
      const r = JSON.parse(fs.readFileSync(file, 'utf8'));
      let alive = false;
      try { process.kill(Number(r.pid), 0); alive = true; } catch (e) { alive = e.code === 'EPERM'; }
      if (!alive || !fs.existsSync(r.profile)) { fs.rmSync(file, { force: true }); continue; }
      if (r.port && r.role) out.push({ port: String(r.port), who: { role: r.role, name: r.name || '' } });
    } catch { /* a half-written entry: next pass */ }
  }
  return out;
}

function evaluate(wsUrl, expression) {
  return new Promise((resolve) => {
    const ws = new WebSocket(wsUrl);
    const done = (ok) => { try { ws.close(); } catch { /* closing */ } resolve(ok); };
    const timer = setTimeout(() => done(false), 3000);
    ws.onopen = () => ws.send(JSON.stringify({ id: 1, method: 'Runtime.evaluate', params: { expression } }));
    ws.onmessage = () => { clearTimeout(timer); done(true); };
    ws.onerror = () => { clearTimeout(timer); done(false); };
  });
}

async function draw(windows) {
  let drawn = 0;
  for (const w of windows) {
    const script = w.who && haloScript(w.who.role, w.who.name);
    if (!script) continue;
    try {
      const targets = await (await fetch(`http://127.0.0.1:${w.port}/json/list`, { signal: AbortSignal.timeout(2000) })).json();
      for (const t of targets) {
        if (t.type !== 'page' || !t.webSocketDebuggerUrl || !/^https?:|^data:|^file:/.test(t.url)) continue;
        if (await evaluate(t.webSocketDebuggerUrl, `if(!document.getElementById('nj-qa-halo')){${script}}`)) drawn++;
      }
    } catch { /* that window just closed */ }
  }
  return drawn;
}

function keeperAlive() {
  try {
    const pid = Number(fs.readFileSync(LOCK(), 'utf8'));
    if (!pid || pid === process.pid) return false;
    process.kill(pid, 0);
    return true;
  } catch { return false; }
}

async function main() {
  if (process.argv.includes('--ensure')) {
    if (!keeperAlive()) require('child_process').spawn(process.execPath, [__filename], { detached: true, stdio: 'ignore', windowsHide: true }).unref();
    return;
  }
  if (keeperAlive()) { console.log('already running'); return; }
  fs.mkdirSync(path.dirname(REGISTRY()), { recursive: true });
  fs.writeFileSync(LOCK(), String(process.pid));
  process.on('exit', () => { try { if (Number(fs.readFileSync(LOCK(), 'utf8')) === process.pid) fs.unlinkSync(LOCK()); } catch { /* gone */ } });
  let lastSeen = Date.now();
  for (;;) {
    const windows = registered();
    const all = windows;
    const drawn = await draw(all);
    if (all.length) lastSeen = Date.now();
    if (process.argv.includes('--once')) { console.log(JSON.stringify({ windows: all, drawn })); return; }
    if (Date.now() - lastSeen > GRACE_MS) { console.log('no NJ-QA window left: ending'); return; }
    await new Promise((r) => setTimeout(r, DRAW_MS));
  }
}

module.exports = { registered, REGISTRY };
if (require.main === module) main();
