#!/usr/bin/env node
/**
 * The face and theme a project has already settled on.
 *
 * "Inherit what was chosen last time" is only a real rule if it is written
 * down. Kept in the head of whoever is building, it survives one session and
 * then quietly becomes "whatever the last script happened to say" — which is
 * how this project ended up printing in Segoe UI while its stylesheet asked for
 * something else.
 *
 * So the choice lives in `.pdf-typography.json` at the project root, next to
 * the other things a repo declares about itself. It is read on every build and
 * written only when someone actually decides.
 *
 *   node house-style.mjs                      show what this project uses
 *   node house-style.mjs --set Amiri,Literata record a decision
 */
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

export const FILE = '.pdf-typography.json';

/** Walk up from `from` until the file turns up, or the drive runs out. */
export function findHouseStyle(from = process.cwd()) {
  let dir = resolve(from);
  for (;;) {
    const candidate = join(dir, FILE);
    if (existsSync(candidate)) return candidate;
    const up = dirname(dir);
    if (up === dir) return null;
    dir = up;
  }
}

/**
 * What this project prints in, or null if nobody has said yet.
 * @returns {{fonts: string[], theme?: object, decidedOn?: string, note?: string}|null}
 */
export function readHouseStyle(from = process.cwd()) {
  const path = findHouseStyle(from);
  if (!path) return null;
  try {
    const style = JSON.parse(readFileSync(path, 'utf8'));
    return { ...style, path };
  } catch (err) {
    throw new Error(`${path} is not readable JSON: ${err.message}`);
  }
}

/**
 * Record a decision. `note` is for why — an inherited choice nobody can explain
 * is one somebody overturns on a whim six months later.
 */
export function writeHouseStyle(style, at = process.cwd()) {
  const path = join(resolve(at), FILE);
  const body = {
    fonts: style.fonts,
    ...(style.theme ? { theme: style.theme } : {}),
    decidedOn: style.decidedOn ?? new Date().toISOString().slice(0, 10),
    ...(style.note ? { note: style.note } : {}),
  };
  writeFileSync(path, JSON.stringify(body, null, 2) + '\n', 'utf8');
  return path;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const args = process.argv.slice(2);
  const set = args.indexOf('--set');
  if (set !== -1) {
    const fonts = (args[set + 1] ?? '').split(',').map((s) => s.trim()).filter(Boolean);
    if (!fonts.length) {
      console.error('usage: node house-style.mjs --set Amiri,Literata [--note "why"]');
      process.exit(1);
    }
    const note = args.indexOf('--note');
    const path = writeHouseStyle({ fonts, note: note === -1 ? undefined : args[note + 1] });
    console.log(`recorded ${fonts.join(', ')} → ${path}`);
  } else {
    const style = readHouseStyle();
    if (!style) {
      console.log(`no ${FILE} above ${process.cwd()} — nothing chosen yet, so ask.`);
      process.exit(0);
    }
    console.log(`${style.path}\n  fonts: ${style.fonts.join(', ')}`
      + (style.decidedOn ? `\n  decided: ${style.decidedOn}` : '')
      + (style.note ? `\n  because: ${style.note}` : ''));
  }
}
