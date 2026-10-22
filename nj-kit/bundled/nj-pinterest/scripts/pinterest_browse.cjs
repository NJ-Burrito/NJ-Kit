#!/usr/bin/env node
/**
 * pinterest_browse.cjs — headed Playwright browse of Pinterest on the owner's own
 * signed-in profile, under his verbal, personal, non-transferable permission
 * (see ../SKILL.md and the memory file it quotes). CLI only, never MCP.
 *
 * Requires `playwright` to be importable. This script does not live inside a
 * project's node_modules, so either:
 *   (a) run it from a project directory that already has playwright installed
 *       (`cd <project> && node <this path>/pinterest_browse.cjs ...`), or
 *   (b) set PLAYWRIGHT_REQUIRE_PATH to a node_modules that has it:
 *       PLAYWRIGHT_REQUIRE_PATH=C:\path\to\project\node_modules node pinterest_browse.cjs ...
 *
 * Usage:
 *   node pinterest_browse.cjs --query "motion design pitch deck" \
 *     --out artifacts/research/<project>/refs/pinterest/pins.jsonl \
 *     [--limit 40] [--thumbnails] [--ensera-tag <session-tag>] \
 *     [--profile "%LOCALAPPDATA%\nj-pinterest-profile"]
 *
 * Never signs in, never accepts a terms/checkpoint screen. If the loaded page
 * shows logged-out or a verification wall, it stops and prints exactly what it
 * saw, then closes the browser. Exit 3 in that case.
 */
const path = require("node:path");
const fs = require("node:fs");
const os = require("node:os");

function requirePlaywright() {
  const extra = process.env.PLAYWRIGHT_REQUIRE_PATH;
  if (extra) {
    return require(require.resolve("playwright", { paths: [extra] }));
  }
  return require("playwright"); // resolves from cwd's node_modules if run from a project
}

function parseArgs(argv) {
  const out = { limit: 40, thumbnails: false };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--thumbnails") out.thumbnails = true;
    else if (a.startsWith("--")) {
      out[a.slice(2)] = argv[i + 1];
      i++;
    }
  }
  return out;
}

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

function politeDelay() {
  // ponytail: fixed 1-3s jitter is the whole pacing model; add a token bucket
  // if a run ever needs to run longer than a single research session.
  return sleep(1000 + Math.random() * 2000);
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (!args.query || !args.out) {
    console.error(
      "usage: pinterest_browse.cjs --query \"...\" --out pins.jsonl [--limit 40] [--thumbnails] [--ensera-tag TAG] [--profile PATH]"
    );
    process.exit(2);
  }

  const { chromium } = requirePlaywright();
  const profileDir =
    args.profile || path.join(os.homedir(), "AppData", "Local", "nj-pinterest-profile");
  const tag = args["ensera-tag"] || "nj-pinterest";
  const limit = Number(args.limit) || 40;

  fs.mkdirSync(path.dirname(args.out), { recursive: true });
  const thumbDir = path.join(path.dirname(args.out), "reference-only");
  if (args.thumbnails) fs.mkdirSync(thumbDir, { recursive: true });

  const context = await chromium.launchPersistentContext(profileDir, {
    headless: false, // always headed — the owner's live account (nj-pinterest rule)
    slowMo: 150,
    args: [`--window-name=${tag}`],
  });

  let exitCode = 0;
  try {
    const page = context.pages()[0] || (await context.newPage());
    await page.goto("https://www.pinterest.com/", { waitUntil: "domcontentloaded" });
    await politeDelay();

    // Signed-out or a checkpoint/verification wall: stop, report, never act on it.
    const loginButton = await page.locator('text="Log in"').first();
    const isLoggedOut = await loginButton.isVisible().catch(() => false);
    if (isLoggedOut) {
      console.error(
        "NOT SIGNED IN: Pinterest shows a 'Log in' control on the home page. " +
          "the owner signs in himself on this profile (%LOCALAPPDATA%\\nj-pinterest-profile) " +
          "before this script is run again. Screen title: " + (await page.title())
      );
      exitCode = 3;
      return;
    }
    const checkpointText = await page
      .locator('text=/verify|confirm it.s you|suspicious/i')
      .first()
      .isVisible()
      .catch(() => false);
    if (checkpointText) {
      console.error(
        "VERIFICATION SCREEN: Pinterest is showing a checkpoint/verification page. " +
          "Screen title: " + (await page.title()) + ". Stopping without acting on it."
      );
      exitCode = 3;
      return;
    }

    const searchUrl = `https://www.pinterest.com/search/pins/?q=${encodeURIComponent(args.query)}`;
    await page.goto(searchUrl, { waitUntil: "domcontentloaded" });
    await politeDelay();

    const seen = new Set();
    const rows = [];
    let stagnantScrolls = 0;
    while (rows.length < limit && stagnantScrolls < 6) {
      const pins = await page.locator('[data-test-id="pin"]').all();
      for (const pin of pins) {
        if (rows.length >= limit) break;
        const link = await pin.locator("a").first().getAttribute("href").catch(() => null);
        if (!link || seen.has(link)) continue;
        seen.add(link);
        const img = pin.locator("img").first();
        const title = await img.getAttribute("alt").catch(() => "");
        const imageUrl = await img.getAttribute("src").catch(() => "");
        rows.push({
          pin_url: new URL(link, "https://www.pinterest.com").href,
          title: title || "",
          description: "",
          board: "",
          image_url: imageUrl || "",
          retrieved: new Date().toISOString().slice(0, 10),
        });
        if (args.thumbnails && imageUrl) {
          try {
            const resp = await page.request.get(imageUrl);
            const buf = await resp.body();
            const id = link.split("/").filter(Boolean).pop() || String(rows.length);
            fs.writeFileSync(path.join(thumbDir, `${id}.jpg`), buf);
          } catch {
            // best-effort; metadata row already captured
          }
        }
        await politeDelay();
      }
      const before = rows.length;
      await page.mouse.wheel(0, 1800);
      await politeDelay();
      if (rows.length === before) stagnantScrolls++;
      else stagnantScrolls = 0;
    }

    const lines = rows.map((r) => JSON.stringify(r)).join("\n") + (rows.length ? "\n" : "");
    fs.writeFileSync(args.out, lines);
    console.log(JSON.stringify({ query: args.query, saved: rows.length, out: args.out }));
  } finally {
    await context.close();
  }
  process.exit(exitCode);
}

main().catch((e) => {
  console.error(`pinterest_browse error: ${e.message}`);
  process.exit(1);
});
