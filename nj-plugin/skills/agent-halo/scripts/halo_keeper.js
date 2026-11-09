// Keeps the halo on every agent's Chrome from outside, whichever way the agent launched it. See ../SKILL.md.
// Usage: node halo_keeper.js [--once|--ensure]      Singleton; ends by itself after IDLE_MIN minutes with no agent window.
// --ensure starts one in the background if none is running (the machine hook, on every Bash or PowerShell call).
// It only ever evaluates the (idempotent) drawing script in page targets, so it can't press, type or navigate.
const { execFile } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { haloScript } = require('./halo.js');

const SCAN_MS = 10000;
const DRAW_MS = 2000;
const IDLE_MIN = 30;
const LOCK = path.join(os.tmpdir(), 'agent-halo-keeper.pid');

/** Which agent owns a window, from its Chrome command line and its parent's. null = a person's run: stays plain. */
function identify(chromeCmd, parentCmd) {
  const text = `${chromeCmd} ${parentCmd}`.replace(/\\/g, '/');
  if (/tools\/run-(menu|ui)|playwright[/ ].*test|test-server/i.test(parentCmd)) return null;
  // client deliverables are filmed: the manual recorder and its profiles never get a halo (devil review 2026-11-09)
  if (/src\/manual|manuals?\/|recorder|rehearse|record-|\/flows\//i.test(text)) return null;
  // only agent work: an NJ-QA run folder, or an explicit AGENT_ROLE; never a person's own Chrome
  if (!/nj-qa|AGENT_ROLE/i.test(text)) return null;
  const key = (text.match(/PROJ-\d+/i) || [''])[0];
  const fromDir = (chromeCmd.replace(/\\/g, '/').match(/user-data-dir="?[^"]*?([^/" ]+)"?(?: |$)/) || [])[1] || '';
  const fromPath = (text.match(/\/scripts\/([^/ ]+)\//) || [])[1] || '';
  const fromKit = /\/kit\/[^/ ]+\.ts/.test(text) ? 'leader' : '';
  const agent = fromPath || (/^proj-chrome-/.test(fromDir) ? '' : fromDir.replace(/-(portal|backoffice|bo|profile)$/i, '')) || fromKit;
  if (!agent) return /nj-qa/i.test(text) ? { role: 'agent', name: key } : null;
  const role = /^(t-|tester)/i.test(agent) ? 'tester' : /^scav/i.test(agent) ? 'scavenger' : /^harvest/i.test(agent) ? 'harvester' : /^leader/i.test(agent) ? 'leader' : /^director/i.test(agent) ? 'director' : agent;
  return { role, name: `${agent === role ? '' : agent} ${key}`.trim() };
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

function chromes() {
  const ps = "Get-CimInstance Win32_Process | Where-Object { $_.Name -in 'chrome.exe','node.exe' } | Select-Object ProcessId,ParentProcessId,Name,CommandLine | ConvertTo-Json -Compress";
  return new Promise((resolve) => {
    execFile('powershell', ['-NoProfile', '-Command', ps], { maxBuffer: 64 * 1024 * 1024, windowsHide: true }, (e, out) => {
      if (e) return resolve([]);
      let list;
      try { list = [].concat(JSON.parse(out)); } catch { return resolve([]); }
      const byId = new Map(list.map((p) => [p.ProcessId, p]));
      resolve(list.filter((p) => p.Name === 'chrome.exe' && /--remote-debugging-port=\d+/.test(p.CommandLine || '') && !/--type=/.test(p.CommandLine || ''))
        .map((p) => ({ port: p.CommandLine.match(/--remote-debugging-port=(\d+)/)[1], who: identify(p.CommandLine, (byId.get(p.ParentProcessId) || {}).CommandLine || '') })));
    });
  });
}

async function draw(windows) {
  let drawn = 0;
  for (const w of windows) {
    const script = w.who && haloScript(w.who.role === 'agent' ? 'agent' : w.who.role, w.who.name);
    if (!script) continue;
    try {
      const targets = await (await fetch(`http://127.0.0.1:${w.port}/json/list`, { signal: AbortSignal.timeout(2000) })).json();
      for (const t of targets) {
        if (t.type !== 'page' || !t.webSocketDebuggerUrl || !/^https?:|^data:/.test(t.url)) continue;
        if (await evaluate(t.webSocketDebuggerUrl, `if(!document.getElementById('nj-qa-halo')){${script}}`)) drawn++;
      }
    } catch { /* that window just closed */ }
  }
  return drawn;
}

function keeperAlive() {
  try {
    const pid = Number(fs.readFileSync(LOCK, 'utf8'));
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
  fs.writeFileSync(LOCK, String(process.pid));
  process.on('exit', () => { try { fs.unlinkSync(LOCK); } catch { /* gone */ } });
  let windows = [];
  let lastSeen = Date.now();
  let lastScan = 0;
  for (;;) {
    if (Date.now() - lastScan >= SCAN_MS) { windows = await chromes(); lastScan = Date.now(); }
    const drawn = await draw(windows);
    if (windows.some((w) => w.who)) lastSeen = Date.now();
    if (process.argv.includes('--once')) { console.log(JSON.stringify({ windows, drawn })); return; }
    if (Date.now() - lastSeen > IDLE_MIN * 60000) { console.log('idle: ending'); return; }
    await new Promise((r) => setTimeout(r, DRAW_MS));
  }
}

module.exports = { identify };
if (require.main === module) main();
