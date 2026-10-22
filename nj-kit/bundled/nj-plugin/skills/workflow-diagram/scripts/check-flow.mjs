#!/usr/bin/env node
/**
 * Lint a workflow flow before it is drawn.
 *
 * Every check here corresponds to a figure that was actually delivered wrong.
 * The point is not to prove a flow is good — only your eyes on the rendered
 * page do that — but to make the failures that are *mechanically detectable*
 * cost seconds instead of a review cycle.
 *
 *   node check-flow.mjs flow.json          # one flow, or an array of flows
 *   node check-flow.mjs                    # reads JSON on stdin
 *
 * Exit code is the number of errors, so it composes with `&&`.
 */
import fs from 'node:fs';

/* The abjadi sequence connectors are lettered with. Anything past its end must
   fall back to a number: codepoint arithmetic from أ walks the hamza forms and
   produces ؤ إ ئ, which read as typos. */
const MARKS = ['أ', 'ب', 'ت', 'ث', 'ج', 'ح', 'خ', 'د', 'ذ', 'ر', 'ز', 'س', 'ش', 'ص'];

const KINDS = new Set(['start', 'end', 'process', 'decision', 'system', 'output']);
const LANES = new Set(['applicant', 'staff', 'system']);

/** Rows beyond this stop fitting one A4 landscape sheet at a readable size. */
const ROWS_PER_FIGURE = 9;
/** `wrap()` keeps 8 lines as a runaway guard; a label near that was truncated. */
const LONG_LABEL = 8 * 28;

const problems = [];
const err = (where, msg) => problems.push({ level: 'error', where, msg });
const warn = (where, msg) => problems.push({ level: 'warn', where, msg });

function checkNode(node, where, seen) {
  if (!node) return;
  const at = `${where}/${node.id ?? '(no id)'}`;

  if (!node.id) err(where, 'node has no id');
  else if (seen.has(node.id)) err(at, `duplicate node id "${node.id}"`);
  else seen.add(node.id);

  if (!KINDS.has(node.kind)) err(at, `unknown kind "${node.kind}"`);
  if (!node.lane) err(at, 'no lane — "who does this" is the question the figure exists to answer');
  else if (!LANES.has(node.lane)) err(at, `unknown lane "${node.lane}"`);

  const text = String(node.ar ?? '').trim();
  if (!text) err(at, 'empty label');
  else if (/^[-–—]$/.test(text)) err(at, 'label is a lone dash — say «لا يوجد» or drop the node');
  else if (/translation-not-found/.test(text)) {
    err(at, `untranslated key reached the figure: ${text}`);
  } else if (text.length > LONG_LABEL) {
    warn(at, `label is ${text.length} chars — check it is not being truncated`);
  }

  // An end node in its lane's colour cannot say whether the request finished or
  // was stopped, which is the thing a reader traces the chart to find out.
  if (node.kind === 'end' && !node.tone) {
    err(at, 'end node has no tone — set "ok" (closed) or "stop" (ended without an output)');
  }
  if (node.tone && !['ok', 'stop'].includes(node.tone)) {
    err(at, `unknown tone "${node.tone}"`);
  }
}

function checkFlow(flow, index) {
  const where = flow.id || flow.title || `flow[${index}]`;
  const rows = Array.isArray(flow.rows) ? flow.rows : [];
  if (!rows.length) {
    err(where, 'no rows');
    return;
  }

  const seen = new Set();
  const ids = new Set();
  for (const row of rows) if (row?.main?.id) ids.add(row.main.id);

  let connectors = 0;

  for (const [i, row] of rows.entries()) {
    const at = `${where}[${i}]`;
    if (!row?.main) {
      err(at, 'row has no main node');
      continue;
    }
    checkNode(row.main, at, seen);

    const branches = Array.isArray(row.branches) ? row.branches : [];

    // Rule 1: a gateway with only the happy path asserts there is no other way
    // out, which is worse than drawing no gateway at all.
    if (row.main.kind === 'decision' && !branches.length) {
      err(`${at}/${row.main.id}`, 'decision shows only one answer — every decision must show both');
    }
    /**
     * An *absent* onward is an oversight; an empty one is a decision.
     *
     * A flow derived from an old SRS with no walk behind it deliberately sets
     * `onward: ''` — no screen has been seen, and captioning the edge «موافقة»
     * would invent a button. That is correct, and it must be backed by an open
     * question naming the gap. A missing key is the different thing: nobody
     * decided anything.
     */
    if (row.main.kind === 'decision' && row.onward === undefined) {
      err(`${at}/${row.main.id}`, 'decision has no onward label');
    } else if (row.main.kind === 'decision' && row.onward === '') {
      warn(
        `${at}/${row.main.id}`,
        'uncaptioned onward edge — correct only if no screen was seen; confirm an open question says so'
      );
    }

    const lanesUsed = new Map();
    for (const [j, branch] of branches.entries()) {
      const bat = `${at}/branch[${j}]`;
      const label = String(branch?.label ?? '').trim();
      if (!label) err(bat, 'branch has no label — the edge must carry the button verbatim');
      if (/translation-not-found/.test(label)) {
        err(bat, `untranslated key on an edge: ${label}`);
      }

      if (branch.node) checkNode(branch.node, bat, seen);

      if (branch.returnsTo) {
        connectors += 1;
        if (!ids.has(branch.returnsTo)) {
          err(bat, `returnsTo "${branch.returnsTo}" is not a row in this flow`);
        }
      } else if (!branch.node) {
        err(bat, 'branch neither lands on a node nor returns anywhere');
      }
      if (branch.node && branch.returnsTo) {
        warn(bat, 'branch has both a node and returnsTo — a return loop needs no node');
      }

      // Two branches in the same lane land in the same place; they are only
      // free to coexist because a refusal is the institution's and a return is
      // the applicant's.
      const lane = branch.node?.lane ?? row.main.lane;
      lanesUsed.set(lane, (lanesUsed.get(lane) ?? 0) + 1);
    }
    for (const [lane, n] of lanesUsed) {
      if (n > 1) warn(at, `${n} branches in lane "${lane}" — the second is pushed to the next sub-row`);
    }
  }

  if (connectors > MARKS.length) {
    err(where, `${connectors} connectors but only ${MARKS.length} letters — the rest fall back to numbers`);
  }
  if (rows.length > ROWS_PER_FIGURE) {
    warn(where, `${rows.length} rows — over ${ROWS_PER_FIGURE} this should split at a desk boundary rather than shrink`);
  }

  // Rule: nothing in the figure that nobody has seen.
  const staff = rows.filter((r) => r?.main?.lane === 'staff' && r.main.kind === 'decision');
  if (!staff.length) {
    warn(where, 'no staff desks — confirm the back-office walk actually ran');
  }
}

function main() {
  const file = process.argv[2];
  let raw;
  try {
    raw = file ? fs.readFileSync(file, 'utf8') : fs.readFileSync(0, 'utf8');
  } catch (error) {
    console.error(`could not read ${file ?? 'stdin'}: ${error.message}`);
    process.exit(1);
  }

  let parsed;
  try {
    parsed = JSON.parse(raw);
  } catch (error) {
    console.error(`not JSON: ${error.message}`);
    process.exit(1);
  }

  const flows = Array.isArray(parsed) ? parsed : parsed.flows ?? [parsed];
  flows.forEach(checkFlow);

  const errors = problems.filter((p) => p.level === 'error');
  const warnings = problems.filter((p) => p.level === 'warn');

  for (const p of problems) {
    console.log(`${p.level === 'error' ? '✗' : '~'} ${p.where}: ${p.msg}`);
  }
  if (!problems.length) console.log('✓ flow is structurally sound — now look at the rendered page');
  else console.log(`\n${errors.length} error(s), ${warnings.length} warning(s)`);

  process.exit(errors.length);
}

main();
