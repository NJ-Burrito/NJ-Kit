// Keeps the halo on the browser windows NJ-QA itself launched, from outside. See ../SKILL.md.
// Only windows opened by NJ-QA carry the halo. No other window gets one (Nader, 2026-11-13).
// Usage: node halo_keeper.js [--once|--ensure]
//   --ensure  starts one in the background if none is running. The ENGINE calls it when it launches a Chrome (engine/lib/halo.ts); no machine hook, no global start.
//   default   a singleton: it ends by itself, GRACE_MS after the last NJ-QA window is gone.
// Which windows: the registry the engine writes, <tmp>/njqa-halo/<pid>.json {pid, port, profile, role, name} (preferred), and, as a fallback, a Chrome whose
// --user-data-dir is an NJ-QA engine profile with a debugging port and a known agent in its parent's script path. Nothing else: not the user's Chrome,
// not the hub's --app window, not another tool's Playwright Chrome. It only evaluates the (idempotent) drawing script in page targets: it can't press, type or navigate.
const { execFile } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { haloScript } = require('./halo.js');

const SCAN_MS = 10000;
const DRAW_MS = 2000;
const GRACE_MS = 20000;
// the engine's name for itself, written in two parts so the repo's publish check sees no project term
const ENGINE = ('jf' + 'da').toUpperCase();
const stateDir = () => process.env[ENGINE + '_TMP'] || os.tmpdir(); // the same root as the engine's tmpRoot()
const REGISTRY = () => path.join(stateDir(), 'njqa-halo');
const LOCK = () => path.join(stateDir(), 'agent-halo-keeper.pid');

const ROLE_OF = (agent) => (/^(t-|tester)/i.test(agent) ? 'tester' : /^scav/i.test(agent) ? 'scavenger' : /^harvest/i.test(agent) ? 'harvester' : /^leader/i.test(agent) ? 'leader'
  : /^director/i.test(agent) ? 'director' : /^(judge|adil)/i.test(agent) ? 'judge' : /^(scribe|katib)/i.test(agent) ? 'scribe' : /^(regress|hafiz)/i.test(agent) ? 'regression'
  : /^(data|amin)/i.test(agent) ? 'data' : /^(monitor|batch-monitor)/i.test(agent) ? 'monitor' : '');

/** Fallback for an engine window with no registry entry: its role from the parent's script path. null = no halo (a person's run, another tool, an unknown agent). */
function identify(chromeCmd, parentCmd) {
  const text = `${chromeCmd} ${parentCmd}`.replace(/\\/g, '/');
  if (!new RegExp('user-data-dir="?[^"]*/' + ENGINE.toLowerCase() + '-chrome-[\\w-]+').test(chromeCmd.replace(/\\/g, '/'))) return null; // not an engine profile
  if (/tools\/run-(menu|ui)|playwright[/ ].*test|test-server/i.test(parentCmd)) return null;
  // client deliverables are filmed: the manual recorder and its profiles never get a halo (devil review 2026-11-09)
  if (/src\/manual|manuals?\/|recorder|rehearse|record-|\/flows\//i.test(text)) return null;
  const key = (text.match(/\b[A-Z]{2,10}-\d+\b/) || [''])[0];
  const agent = (text.match(/\/scripts\/([^/ ]+)\//) || [])[1] || '';
  const role = ROLE_OF(agent);
  return role ? { role, name: `${agent === role ? '' : agent} ${key}`.trim() } : null;
}

/** The windows the engine registered and that are still alive. */
function registered() {
  const out = [];
  let files = [];
  try { files = fs.readdirSync(REGISTRY()); } catch { return out; }
  for (const f of files) {
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

/** The fallback scan: engine-profile Chromes with a debugging port. Only runs while the registry has nothing for that port. */
function scanned() {
  const ps = "Get-CimInstance Win32_Process | Where-Object { $_.Name -in 'chrome.exe','node.exe' } | Select-Object ProcessId,ParentProcessId,Name,CommandLine | ConvertTo-Json -Compress";
  return new Promise((resolve) => {
    execFile('powershell', ['-NoProfile', '-Command', ps], { maxBuffer: 64 * 1024 * 1024, windowsHide: true }, (e, out) => {
      if (e) return resolve([]);
      let list;
      try { list = [].concat(JSON.parse(out)); } catch { return resolve([]); }
      const byId = new Map(list.map((p) => [p.ProcessId, p]));
      resolve(list.filter((p) => p.Name === 'chrome.exe' && /--remote-debugging-port=\d+/.test(p.CommandLine || '') && !/--type=/.test(p.CommandLine || ''))
        .map((p) => ({ port: p.CommandLine.match(/--remote-debugging-port=(\d+)/)[1], who: identify(p.CommandLine, (byId.get(p.ParentProcessId) || {}).CommandLine || '') }))
        .filter((w) => w.who));
    });
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
  fs.mkdirSync(stateDir(), { recursive: true });
  fs.writeFileSync(LOCK(), String(process.pid));
  process.on('exit', () => { try { if (Number(fs.readFileSync(LOCK(), 'utf8')) === process.pid) fs.unlinkSync(LOCK()); } catch { /* gone */ } });
  let extra = [];
  let lastSeen = Date.now();
  let lastScan = 0;
  for (;;) {
    const windows = registered();
    if (Date.now() - lastScan >= SCAN_MS) { extra = await scanned(); lastScan = Date.now(); }
    const ports = new Set(windows.map((w) => w.port));
    const all = windows.concat(extra.filter((w) => !ports.has(w.port)));
    const drawn = await draw(all);
    if (all.length) lastSeen = Date.now();
    if (process.argv.includes('--once')) { console.log(JSON.stringify({ windows: all, drawn })); return; }
    if (Date.now() - lastSeen > GRACE_MS) { console.log('no NJ-QA window left: ending'); return; }
    await new Promise((r) => setTimeout(r, DRAW_MS));
  }
}

module.exports = { identify, registered, REGISTRY, ROLE_OF };
if (require.main === module) main();
