---
name: nj-agent-halo
description: "Every browser window the NJ-QA tool opens, and only those, carries a coloured border and the agent's type at the top, so a person can tell agent windows apart. Use whenever an NJ-QA agent opens a headed browser through Playwright, a script or the Playwright MCP; no other window gets one. Cosmetic: no effect on clicks, page text or screenshots."
---

# Agent halo: which agent owns this window

| Agent | Colour |
|---|---|
| Scavenger | 🔵 blue |
| Tester | 🟠 orange |
| Leader | 🟢 green |
| Director | 🔴 red |
| Harvester | 🟣 purple (chosen, the owner did not assign one) |
| Any other NJ-QA agent | ⚪ silver, with its name as shown in the agent map |

## The text

`TYPE: name` in the page's serif face (Thmanyah when installed, else the system serif). **TYPE** is capitals, bold, 20px. The name, as in the agent map, is small letters, not bold, 14px, except codes such as PROJ-5494, which stay in capitals: **TESTER:** tester-r1 PROJ-4285. An agent with no assigned type shows **AGENT:** and its name.

## It is automatic (the keeper)

`scripts/halo_keeper.js` runs in the background and draws the halo from outside on every Chrome the NJ-QA tool opened (its profile folder or launching script path contains `nj-qa`), however the agent launched it. Every other Chrome stays plain, agent or not. A new window gets it within about 10 seconds, and it comes back within about 2 seconds after a page loads. It names the window from the script's path or the profile folder. Agents named `tester-*`, `t-*`, `scav*`, `harvest*`, `leader*` and `director*` get their colours, and any other folder name gets silver.

Start it with `node scripts/halo_keeper.js` (or from a hook of your own on Bash and PowerShell calls); it keeps running while agents have windows open, and it ends itself after 30 minutes with no NJ-QA window, or after 2 minutes if none has appeared since it started. Runs a person starts (the Playwright runner, your own menus) stay plain, and so does your everyday Chrome. A profile folder named for the agent gives the window its name, so agents should name theirs that way.

The Playwright MCP's browser has no debugging port, so inside an NJ-QA run it needs the manual call below; outside NJ-QA, don't add one.

## How to apply it by hand

**A Playwright script** (Node), right after creating the context and page:

```js
const { installHalo } = require('<plugin>/skills/nj-agent-halo/scripts/halo.js');
await installHalo(context, page, 'tester', 'tester-r1 PROJ-4285'); // type, agent-map name
```

These can also come from the environment: `NJ_QA_ROLE=tester AGENT_NAME="tester-r1 PROJ-4285"`. Without a name it does nothing, so a person's own runs stay plain.

**The Playwright MCP:** call `browser_run_code_unsafe` once, right after the first navigation, with the code `printCode` prints:

```bash
node <plugin>/skills/nj-agent-halo/scripts/halo.js tester "tester-r1 PROJ-4285"
```

**Your own test suite:** call `installHalo` from the helper that opens a fresh window, gated on `AGENT_ROLE`, so a person's runs stay plain.

## Evidence

Every capture method is allowed; use whichever suits the job (owner, 2026-11-09).

| Capture | Halo in the result |
|---|---|
| `page.screenshot`, `locator.screenshot`, helpers built on them such as `shotOf` | Hidden automatically |
| Page text, DOM queries, text scans | Never included |
| A script's own `page.screenshot` when it doesn't use `freshWindow`, Playwright MCP screenshot, raw CDP capture, video, OS screen capture | Visible, and that's fine |

The manual recorder (`project-tests/src/manual/recorder.ts`) doesn't draw it, so client videos stay plain.

Why it can't disturb anything: clicks pass through (`pointer-events: none`), its text sits in a closed shadow root that page queries and text scans never see, and any failure to draw is swallowed.
