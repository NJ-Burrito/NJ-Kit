#!/usr/bin/env node
// English-only, <=10-option, suggest-only wrapper around @receptron/laya.
// Never call this from a per-event hook (nj-laya rule 10, load not yet warm-measured
// under 1s) and never let its output trigger an action (rule 1) — write-only JSON.
//
// Usage: node laya_ask.mjs --question "..." --options "A,B,C" [--out result.json]
import { Laya } from "@receptron/laya";
import { writeFileSync } from "node:fs";
import { pathToFileURL } from "node:url";

const REVISION = "v0.1.2"; // pinned per nj-laya rule 14 (@receptron/laya installed version)
const MAX_OPTIONS = 10;

function parseArgs(argv) {
  const out = {};
  for (let i = 0; i < argv.length; i += 2) {
    out[argv[i].replace(/^--/, "")] = argv[i + 1];
  }
  return out;
}

function isAsciiEnglish(s) {
  // ponytail: crude but sufficient gate — non-ASCII means route away (rule 4).
  return /^[\x00-\x7F]*$/.test(s);
}

export async function ask({ question, options }) {
  if (!question || !options || options.length === 0) {
    throw new Error("question and at least one option are required");
  }
  if (options.length > MAX_OPTIONS) {
    throw new Error(`too many options (${options.length} > ${MAX_OPTIONS}); nj-laya rule 5`);
  }
  if (!isAsciiEnglish(question) || options.some((o) => !isAsciiEnglish(o))) {
    throw new Error("non-English input; nj-laya rule 4 routes Arabic away from Laya");
  }

  const laya = await Laya.load();
  const criteria = {};
  for (const o of options) criteria[o] = o;
  const result = await laya.systemOne(
    { text: question },
    { pick: { type: "choice", instructions: question, criteria } }
  );
  await laya.close();

  // Suggest-only: choice + confidence only (rule 6, rule 2 — never noul/act_probability).
  return {
    revision: REVISION,
    checkpoint: "english",
    question,
    options,
    choice: result.answers.pick.choice,
    confidence: result.answers.pick.confidence,
    suggest_only: true,
  };
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (!args.question || !args.options) {
    console.error("usage: laya_ask.mjs --question '...' --options 'A,B,C' [--out out.json]");
    process.exit(2);
  }
  const options = args.options.split(",").map((s) => s.trim()).filter(Boolean);
  try {
    const out = await ask({ question: args.question, options });
    const json = JSON.stringify(out, null, 2);
    if (args.out) writeFileSync(args.out, json + "\n");
    else console.log(json);
  } catch (e) {
    console.error(`laya_ask error: ${e.message}`);
    process.exit(1);
  }
}

// Windows bug (found kacs-v4, 2026-09-25): `file://${argv[1]}` never equals
// import.meta.url there (backslashes, missing leading slash), so main() never
// fired. pathToFileURL builds the same URL form Node uses for import.meta.url.
if (import.meta.url === pathToFileURL(process.argv[1]).href) {
  main();
}
