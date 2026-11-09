// nj-rank «📈 Metrics» tab (the owner 2026-11-05, simplified the same day): the story first, in plain words,
// then a ranked "how you compare" with the QA team, then ONE trend chart; everything else folded away.
// Charts: Flint (microsoft/flint-chart) on Vega-Lite. Data: #njr-mdata (nj_rank.py metrics_data);
// team rows come from team_metrics.py (weekly, scheduled). Libraries load only when the tab opens.
(function () {
  const CDN = {
    flint: 'https://cdn.jsdelivr.net/npm/flint-chart@1.0.1/+esm',
    umd: ['https://cdn.jsdelivr.net/npm/vega@6.4.0/build/vega.min.js',
          'https://cdn.jsdelivr.net/npm/vega-lite@6.5.0/build/vega-lite.min.js',
          'https://cdn.jsdelivr.net/npm/vega-embed@7.3.0/build/vega-embed.min.js'],
  };
  const FONT = "'Thmanyah Serif Text', Georgia, serif";
  const M = JSON.parse(document.getElementById('njr-mdata').textContent);
  const $ = s => document.querySelector(s);
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const DAY = 864e5;
  let lib = null, st = { period: '28' };
  try { Object.assign(st, JSON.parse(sessionStorage.getItem('njr-m2') || '{}')); } catch (e) {}

  // ---------- dates (local days; week starts Sunday, weekend Fri+Sat) ----------
  const dkey = t => { const d = new Date(t); return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0'); };
  const parse = s => new Date(s + 'T00:00:00').getTime();
  const weekOf = s => { const t = parse(s); return dkey(t - new Date(t).getDay() * DAY); };
  const today = dkey(Date.now()), END = parse(today) + DAY;
  const inWin = (d, days, back) => d && parse(d) >= END - (back + 1) * days * DAY && parse(d) < END - back * days * DAY;
  const cur = (l, days) => l.filter(x => inWin(x.d, days, 0)), prev = (l, days) => l.filter(x => inWin(x.d, days, 1));
  const count = (l, k) => l.reduce((m, x) => (m[x[k]] = (m[x[k]] || 0) + 1, m), {});
  const top = (l, k, n) => Object.entries(count(l, k)).sort((a, b) => b[1] - a[1]).slice(0, n);
  const pct = v => Math.round(v * 100) + '%';
  const PERIOD = { '7': ['the last 7 days', 'the 7 days before'], '28': ['the last 4 weeks', 'the 4 weeks before'],
                   '84': ['the last 12 weeks', 'the 12 weeks before'] };

  function streak(work) {
    const days = new Set(work.map(x => x.d)); let t = parse(today), n = 0;
    if (!days.has(today)) t -= DAY;
    for (let g = 0; g < 400; g++, t -= DAY) { const wd = new Date(t).getDay(); if (wd === 5 || wd === 6) continue; if (days.has(dkey(t))) n++; else break; }
    return n;
  }
  const real = bugs => { const n = bugs.length, nb = bugs.filter(b => b.g === 'Not a bug').length; return n ? (n - nb) / n : NaN; };
  const fixed = bugs => { const v = bugs.filter(b => b.g !== 'Not a bug'); return v.length ? v.filter(b => b.g === 'Fixed').length / v.length : NaN; };
  const more = (a, b, unit) => a > b ? `<b class="good">more</b> than ${b} ${unit}` : a < b ? `<b class="bad">fewer</b> than ${b} ${unit}` : `the <b>same</b> as ${unit}`;
  const ordinal = n => n + ({ 1: 'st', 2: 'nd', 3: 'rd' }[n] || 'th');  // a team of a handful

  // ---------- the story: 3–5 plain sentences, numbers bold, one icon each ----------
  function story(days) {
    const [now, before] = PERIOD[st.period];
    const w = cur(M.work, days), wp = prev(M.work, days), lines = [];
    const pj = top(w, 'p', 3).map(([k, n]) => `${esc(k)} (${n})`).join(', ');
    lines.push(['🛠', `In ${now} you finished <b>${w.length}</b> pieces of work — ${more(w.length, wp.length, 'in ' + before)}.`
      + (pj ? ` Most of it went to ${pj}.` : '')]);
    const T = M.team && M.team.members;
    if (T && T.length > 1) {
      const rows = T.map(m => ({ m, b: cur(m.bugs, days) })), me = rows.find(r => r.m.me) || rows[0];
      const others = rows.filter(r => r !== me), avg = others.reduce((s, r) => s + r.b.length, 0) / others.length;
      const rank = rows.filter(r => r.b.length > me.b.length).length + 1;
      lines.push(['🐞', `You found <b>${me.b.length}</b> Bugs — <b class="${rank === 1 ? 'good' : rank === rows.length ? 'bad' : ''}">${ordinal(rank)} of ${rows.length}</b> in the QA team. `
        + `The others found <b>${Math.round(avg)}</b> on average.`]);
      const rm = real(me.b), ro = real(others.flatMap(r => r.b));
      if (isFinite(rm)) lines.push(['🎯', `<b>${pct(rm)}</b> of your Bugs were real problems (not rejected as «ليس Bug»)`
        + (isFinite(ro) ? ` — the others: <b>${pct(ro)}</b>.` : '.')]);
      const t = trendWord(me.m.bugs);
      if (t) lines.push(['📈', t]);
    }
    const sk = streak(M.work);
    lines.push([sk ? '🔥' : '⏸', sk ? `You have logged work <b>${sk} working days in a row</b>.` : 'No work logged since the last working day — the streak starts again with the next item.']);
    return lines;
  }
  function trendWord(bugs) {  // last 6 full weeks vs the 6 before, per week
    const wk = parse(weekOf(today)), per = (a, b) => bugs.filter(x => x.d && parse(x.d) >= wk - a * 7 * DAY && parse(x.d) < wk - b * 7 * DAY).length / 6;
    const recent = per(6, 0), earlier = per(12, 6);
    if (!recent && !earlier) return '';
    const r = recent.toFixed(1), e = earlier.toFixed(1);
    return recent > earlier * 1.1 ? `Your Bugs per week are <b class="good">rising</b>: ${r} a week lately, up from ${e}.`
      : recent < earlier * 0.9 ? `Your Bugs per week are <b class="bad">slowing</b>: ${r} a week lately, down from ${e}.`
      : `Your Bugs per week are <b>steady</b> at about ${r} a week.`;
  }

  // ---------- how you compare: ranked rows, no axes ----------
  function compare(days) {
    const T = M.team && M.team.members;
    if (!T || T.length < 2) return '<p class="mempty">Team data appears after the first weekly pull (team_metrics.py).</p>';
    const rows = T.map(m => { const b = cur(m.bugs, days); return { m, n: b.length, real: real(b), fix: fixed(b),
      pj: top(b, 'p', 3).map(([k, n]) => `${esc(k)} ${n}`).join(' · ') }; });
    const board = (title, hint, key, fmt) => {
      const r = rows.filter(x => isFinite(x[key])).sort((a, b) => b[key] - a[key]), max = Math.max(...r.map(x => x[key]), 1e-9);
      return `<div class="board"><h4>${title}</h4><p class="hint">${hint}</p>` + r.map((x, i) =>
        `<div class="brow${x.m.me ? ' me' : ''}"><span class="rk">${['🥇', '🥈', '🥉'][i] || (i + 1)}</span>`
        + `<span class="nm">${esc(x.m.me ? 'You' : x.m.name.split(' ')[0])}${key === 'n' && x.pj ? `<small>${x.pj}</small>` : ''}</span>`
        + `<span class="bt"><i style="width:${Math.max(2, x[key] / max * 100)}%"></i></span><b>${fmt(x[key])}</b></div>`).join('')
        + (r.length ? '' : '<p class="mempty">Nobody filed Bugs in this period.</p>') + '</div>';
    };
    return board('🐞 Bugs found', 'More = more problems caught', 'n', String)
      + board('🎯 Real problems', 'Share not rejected as «ليس Bug»', 'real', pct)
      + board('✅ Fixed so far', 'Share of real Bugs now Done or Closed', 'fix', pct);
  }

  // ---------- charts ----------
  const script = src => new Promise((ok, bad) => { const s = document.createElement('script'); s.src = src; s.onload = ok; s.onerror = () => bad(new Error('could not load ' + src)); document.head.appendChild(s); });
  async function load() {
    if (lib) return lib;
    for (const u of CDN.umd) await script(u);
    const f = await import(CDN.flint);
    return (lib = { assemble: f.assembleVegaLite, embed: window.vegaEmbed });
  }
  function spec(title, subtitle, chartType, values, semantic, encodings, colors, w) {
    const you = getComputedStyle(document.documentElement).getPropertyValue('--accent').trim();  // single-series = you = purple
    return { input: { data: { values }, semantic_types: semantic, theme_spec: { extends: 'powerbi-light', ink: { series: { single: you } } },
      chart_spec: { chartType, title, subtitle, encodings, baseSize: { width: w || 440, height: 240 } } }, colors };
  }
  async function draw(el, s) {
    if (!s.input.data.values.length) { el.innerHTML = '<p class="mempty">No data in this period.</p>'; return; }
    const vl = lib.assemble(s.input);
    // post-Flint: Thmanyah, the page's own colours (follows ☀/🌙), fixed series colours where given
    const css = getComputedStyle(document.documentElement), tok = n => css.getPropertyValue(n).trim();
    const swap = { '#ffffff': tok('--card'), '#f2f2f2': tok('--line'), '#605e5c': tok('--muted'), '#252423': tok('--ink'), '#dfdddc': tok('--line') };
    (function walk(o) {
      if (!o || typeof o !== 'object') return;
      if (s.colors && o.color && o.color.field && s.colors[o.color.field]) o.color.scale = s.colors[o.color.field];
      for (const k in o) {
        const v = o[k];
        if (typeof v !== 'string') { walk(v); continue; }
        if (/(^f|F)ont$/.test(k)) o[k] = FONT; else if (swap[v.toLowerCase()]) o[k] = swap[v.toLowerCase()];
      }
    })(vl);
    const box = el.appendChild(document.createElement('div'));
    await lib.embed(box, vl, { actions: false, renderer: 'svg' });
  }
  function weekly(list, weeks) {  // {week: n} for the last `weeks` weeks, zeros included
    const start = parse(weekOf(today)) - (weeks - 1) * 7 * DAY, m = {};
    for (let i = 0; i < weeks; i++) m[dkey(start + i * 7 * DAY)] = 0;
    list.forEach(x => { if (x.d) { const w = weekOf(x.d); if (w in m) m[w]++; } });
    return m;
  }
  function trendCharts() {
    const out = [], WEEKS = 12, T = M.team && M.team.members;
    const you = getComputedStyle(document.documentElement).getPropertyValue('--accent').trim();
    if (T && T.length > 1) {
      const me = T.find(m => m.me) || T[0], others = T.filter(m => m !== me);
      const mw = weekly(me.bugs, WEEKS), ow = others.map(o => weekly(o.bugs, WEEKS)), vals = [];
      Object.keys(mw).forEach(w => { vals.push({ Week: w, Who: 'You', Bugs: mw[w] });
        vals.push({ Week: w, Who: 'Team average', Bugs: +(ow.reduce((s, o) => s + o[w], 0) / ow.length).toFixed(1) }); });
      out.push(['main', 'Purple line above the grey line = that week you found more Bugs than the average teammate.',
        spec('Bugs found per week: you vs the team', 'Last 12 weeks, all Jira projects · the last point is this week, still in progress', 'Line Chart', vals,
          { Week: 'Date', Who: 'Category', Bugs: 'Count' }, { x: { field: 'Week' }, y: { field: 'Bugs' }, color: { field: 'Who' } },
          { Who: { domain: ['You', 'Team average'], range: [you, '#9ca3af'] } }, 900)]);
    }
    const ww = weekly(M.work, WEEKS);
    out.push(['main', 'Taller bar = a busier week. Compare the right end with the left end to see if you are speeding up.',
      spec('Work you finished per week', 'Last 12 weeks, every project in nj-rank · the last bar is this week, still in progress', 'Bar Chart',
        Object.entries(ww).map(([Week, Items]) => ({ Week, Items })), { Week: 'Date', Items: 'Count' },
        { x: { field: 'Week' }, y: { field: 'Items' } }, null, 900)]);
    return out;
  }
  function detailCharts(days) {
    const out = [], w = cur(M.work, days), T = M.team && M.team.members;
    if (T && T.length > 1) {
      const vals = [];
      T.forEach(m => Object.entries(weekly(m.bugs, 12)).forEach(([Week, Bugs]) => vals.push({ Week, Person: m.me ? 'You' : m.name.split(' ')[0], Bugs })));
      out.push(spec('Bugs per week, each person', 'Last 12 weeks', 'Line Chart', vals, { Week: 'Date', Person: 'Name', Bugs: 'Count' },
        { x: { field: 'Week' }, y: { field: 'Bugs' }, color: { field: 'Person' } }));
      const pv = [];
      T.forEach(m => Object.entries(count(cur(m.bugs, days), 'p')).forEach(([Project, Bugs]) => pv.push({ Person: m.me ? 'You' : m.name.split(' ')[0], Project, Bugs })));
      out.push(spec('Bugs by project, each person', 'In the chosen period', 'Stacked Bar Chart', pv, { Person: 'Name', Project: 'Category', Bugs: 'Count' },
        { y: { field: 'Person' }, x: { field: 'Bugs' }, color: { field: 'Project' } }));
    }
    out.push(spec('Your work by project', 'In the chosen period', 'Bar Chart', top(w, 'p', 12).map(([Project, Items]) => ({ Project, Items })),
      { Project: 'Category', Items: 'Count' }, { y: { field: 'Project', sort: '-x' }, x: { field: 'Items' } }));
    out.push(spec('Your work by type', 'In the chosen period', 'Bar Chart', top(w, 'w', 12).map(([Type, Items]) => ({ Type, Items })),
      { Type: 'Category', Items: 'Count' }, { y: { field: 'Type', sort: '-x' }, x: { field: 'Items' } }));
    out.push(spec('Your PROJ Bugs: services with the most', 'Top 10 in the chosen period', 'Bar Chart',
      top(cur(M.bugs, days), 'svc', 10).map(([Service, Bugs]) => ({ Service, Bugs })),
      { Service: 'Category', Bugs: 'Count' }, { y: { field: 'Service', sort: '-x' }, x: { field: 'Bugs' } }, null, 900));
    return out;
  }

  async function render() {
    if (!$('#njr-metrics')) return;
    try { sessionStorage.setItem('njr-m2', JSON.stringify(st)); } catch (e) {}
    document.querySelectorAll('#m-period button').forEach(b => b.classList.toggle('on', b.dataset.p === st.period));
    const days = +st.period;
    $('#m-story').innerHTML = '<h3>📖 Your story</h3>' + story(days).map(([i, t]) => `<p><span class="si">${i}</span><span>${t}</span></p>`).join('')
      + (M.team && M.team.fetched_at ? `<p class="hint">Team numbers from Jira (all projects), pulled ${esc(M.team.fetched_at.slice(0, 16).replace('T', ' '))}; refreshed every Sunday.</p>` : '');
    $('#m-compare').innerHTML = compare(days);
    const msg = $('#m-msg');
    try { msg.textContent = lib ? '' : 'Loading charts…'; await load(); msg.textContent = ''; }
    catch (e) { msg.textContent = '⚠ Charts need internet the first time (' + e.message + '). The story and ranking above are still current.'; return; }
    const tc = trendCharts();
    $('#m-trend').innerHTML = tc.map((c, i) => `<div class="mcard wide"><p class="say">💡 ${c[1]}</p><div id="m-t${i}"></div></div>`).join('');
    for (let i = 0; i < tc.length; i++) await safe($('#m-t' + i), tc[i][2]);
    const dc = detailCharts(days);
    $('#m-grid').innerHTML = dc.map((c, i) => `<div class="mcard${c.input.chart_spec.baseSize.width > 500 ? ' wide' : ''}" id="m-c${i}"></div>`).join('');
    if ($('#m-more').open) for (let i = 0; i < dc.length; i++) await safe($('#m-c' + i), dc[i]);
    else $('#m-more').ontoggle = () => { if ($('#m-more').open) render(); };
  }
  async function safe(el, s) {
    try { await draw(el, s); } catch (e) { el.innerHTML = `<p class="mempty">⚠ ${esc(s.input.chart_spec.title)}: ${esc(e.message)}</p>`; console.error(e); }
  }

  document.querySelectorAll('#m-period button').forEach(b => b.onclick = () => { st.period = b.dataset.p; render(); });
  window.njMetrics = render;
  matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
    if (!document.documentElement.dataset.theme && document.body.dataset.tab === 'metrics') render();
  });
})();
