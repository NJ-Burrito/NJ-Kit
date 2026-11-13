---
name: nj-agent-halo
description: "Only windows opened by NJ-QA carry the halo, a coloured edge and the crew member's type at the top, so a person can tell them apart. No other window gets one. Use whenever an NJ-QA agent opens a headed browser through Playwright, a script or the Playwright MCP. Cosmetic: no effect on clicks, page text or screenshots."
---

# Agent halo: which agent owns this window

**Only windows opened by NJ-QA carry the halo. No other window gets one.** The style is the dusk ribbon with a light outline and dark keyline (Nader, 2026-11-13).

| Agent | Name (EN / AR) | Halo key | Colour |
|---|---|---|---|
| Scavenger | Kashif / كاشف | `scavenger` | 🔵 blue `#38B6FF` |
| Tester | Burhan / برهان | `tester` | 🟠 orange `#FF8A1F` |
| Leader | Bonanza / بونانزا | `leader` | 🟢 green `#2EDB82` |
| Director | Farid / فريد | `director` | 🔴 red `#FF4D4D` |
| Harvester | Rasid / راصد | `harvester` | 🟣 purple `#B87CFF` |
| Batch Monitor | Nader / نادر | `monitor` | 🩵 teal `#17D4C0` |
| Evidence judge | Adil / عادل | `judge` | 🟡 gold `#FFE23A` |
| Scribe | Katib / كاتب | `scribe` | 🔷 indigo `#4046EE` |
| Regression keeper | Hafiz / حافظ | `regression` | 🟣 magenta `#EE3FDA` |
| Test-data keeper | Amin / أمين | `data` | 🫒 olive `#B5E61D` |
| Awn / عون | | none | no halo |

The hues come from NJ-QA's `brand/palette.md` and live in `scripts/halo.js` (`COLOURS`). A role outside the crew draws nothing, and a name change never changes a key. Each crew member's clay face is in `faces/<key>.webp`.

## The look: one switch

`STYLE` in `scripts/halo.js` picks one of three directions (`a` lit glow edge with the face in a glass tab, `b` corner tab badge, `c` dusk ribbon with an outline). `c` is the default. Every direction stays at the window edge (rim at most 28 px deep, label at most 28 px tall), uses Thmanyah when installed, and is `pointer-events:none`. `NJ_QA_HALO_STYLE=a|b|c` overrides it for one run.

## The text

`TYPE: name`. **TYPE** is capitals, bold. The name, as in the agent map, is small letters, not bold, except codes such as PROJ-5494, which stay in capitals: **TESTER:** tester-r1 PROJ-4285.

## It is automatic (the keeper)

`scripts/halo_keeper.js` redraws the halo from outside on the windows NJ-QA launched, so it comes back within about 2 seconds after a page loads. Which windows: only those in the registry NJ-QA's engine writes when it starts a Chrome (`<dir>/<pid>.json`: pid, port, profile, role, name; `<dir>` is `$NJQA_HALO_DIR`, else `njqa-halo` in the system temp folder). A Chrome that is not in the registry, such as your everyday Chrome or another tool's, never gets one, so without NJ-QA the skill draws nothing.

NJ-QA's engine starts the keeper itself (`halo_keeper.js --ensure`); there is no machine hook. It ends by itself about 20 seconds after the last NJ-QA window is gone. Runs a person starts stay plain.

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

## Evidence

Every capture method is allowed; use whichever suits the job (owner, 2026-11-09).

| Capture | Halo in the result |
|---|---|
| `page.screenshot`, `locator.screenshot`, helpers built on them such as `shotOf` | Hidden automatically |
| Page text, DOM queries, text scans | Never included |
| A script's own `page.screenshot` when it doesn't use `freshWindow`, Playwright MCP screenshot, raw CDP capture, video, OS screen capture | Visible, and that's fine |

Why it can't disturb anything: clicks pass through (`pointer-events: none`), its text sits in a closed shadow root that page queries and text scans never see, and any failure to draw is swallowed.
