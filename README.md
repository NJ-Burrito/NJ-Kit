<div align="center">

<img src="docs/assets/hero.gif" alt="NJ-Kit: analyse, find the skill, plan, execute, gate, review. A script decides PASS or FAIL." width="640">

# NJ-Kit

## A working method for Claude Code.

## Skills that check their own work.

[![CI](https://github.com/NJ-Burrito/NJ-Kit/actions/workflows/ci.yml/badge.svg)](https://github.com/NJ-Burrito/NJ-Kit/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Font: Thmanyah, own licence](https://img.shields.io/badge/font-Thmanyah%20%E2%80%94%20own%20licence-1f2937.svg)](https://font.thmanyah.com)
[![Claude Code plugin](https://img.shields.io/badge/Claude%20Code-plugin-d97757.svg)](.claude-plugin/marketplace.json)
[![Skills](https://img.shields.io/badge/skills-43-7c3aed.svg)](#whats-inside)
[![Arabic and English](https://img.shields.io/badge/Arabic%20%2B%20English-first--class-0d9488.svg)](nj-plugin/skills/arabic-english-proofreading)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](nj-kit/scripts/install.py)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Nader%20Alzghoul-0A66C2?logo=linkedin&logoColor=white)](https://www.linkedin.com/in/nader-alzghoul)
[![GitHub](https://img.shields.io/badge/GitHub-NJ--Burrito-181717?logo=github&logoColor=white)](https://github.com/NJ-Burrito)
[![Portfolio](https://img.shields.io/badge/Portfolio-nj--burrito.github.io-0A66C2?logo=googlechrome&logoColor=white)](https://nj-burrito.github.io/)
[![Stars](https://img.shields.io/badge/stars-1-white?style=social&logo=github)](https://github.com/NJ-Burrito/NJ-Kit/stargazers)

**NJ-Kit is a free, open-source toolkit for Claude Code.** One working method (analyse → find the skill → plan → execute → review), a delegation model for teams of agents, and house skills for documents, QA, Jira, narration, audio and video. Every skill ends in a gate a script runs, not a promise.

### Pick how you want it. All free. 👇

| 🧩 Plugin | 🧰 Kit installer | 📂 Copy a skill | 🔤 NJ-Font |
|:---:|:---:|:---:|:---:|
| For **Claude Code** | Skills + hooks + house style on a new machine | For any agent that reads `SKILL.md` | A typeface by the creator |
| [Install ↓](#plugin) | [Install ↓](#kit) | [Browse ↓](#whats-inside) | [Install ↓](#nj-font) |

</div>

<a id="plugin"></a>

## 🧩 Plugin

In Claude Code, type these two lines:

```
/plugin marketplace add NJ-Burrito/NJ-Kit
/plugin install nj-kit@nj-kit
```

Then say: **"use nj-method"**. Claude Code gets the 23 plugin skills in one go.

<a id="kit"></a>

## 🧰 Kit installer

Sets up the skills, hooks, MCP servers and house style on a fresh machine. Needs Python 3.10+ ([uv](https://docs.astral.sh/uv/) recommended).

```bash
git clone https://github.com/NJ-Burrito/NJ-Kit
cd NJ-Kit
python nj-kit/scripts/install.py --check   # shows what it would do, changes nothing
python nj-kit/scripts/install.py           # does it
```

Skills land in `~/.claude/skills/` by default. `--scope project` puts them in one repo instead. Details: [nj-kit/README.md](nj-kit/README.md).

## 3 steps

1️⃣ **Install** the plugin or the kit

2️⃣ **Ask** for the work as you normally would

3️⃣ **Read the gate line** — every skill reports PASS/FAIL from a script, not from the model's opinion

<a id="whats-inside"></a>

## What's inside

### 🧠 Method and agents

| Skill | What it does |
|---|---|
| [nj-method](nj-plugin/skills/nj-method) | The default method for every request: analyse, find a skill, plan with checkpoints, execute, review |
| [nj-delegate](nj-plugin/skills/nj-delegate) | Governance for agent teams: a Lead decides, workers build, helpers do bounded work; every clause enforced |
| [nj-agent-ops](nj-plugin/skills/nj-agent-ops) | The transport layer: results through files, telemetry refused at write time (`relay.py`) |
| [nj-supervise](nj-plugin/skills/nj-supervise) | How to brief a worker and know it is actually working |
| [session-handoff](nj-plugin/skills/session-handoff) | Close a session with a `handoff.md` the next one reads first |
| [nj-learn](nj-plugin/skills/nj-learn) | Capture a lesson where it will be read again |
| [nj-wrapup](nj-plugin/skills/nj-wrapup) | Close a session or a tested service end to end, through gates |
| [devil](nj-plugin/skills/devil) | Ranked objections to a plan before you act on it |
| [nj-security-review](nj-plugin/skills/nj-security-review) | Audit third-party skills, plugins and MCP servers before installing |

### ✅ QA and Jira

| Skill | What it does |
|---|---|
| [nj-jira](nj-plugin/skills/nj-jira) | Analyse a ticket, file Bugs with evidence, QA re-check, keep a tracker |
| [nj-jira-to-automation](nj-plugin/skills/nj-jira-to-automation) | Turn a ticket into a runnable automation |
| [nj-qa-pipeline](nj-plugin/skills/nj-qa-pipeline) | Jira → notes → staging check → acceptance report → automation |
| [nj-automation-suite](nj-plugin/skills/nj-automation-suite) | Scaffold a portable, self-contained Playwright suite |
| [nj-rank](nj-plugin/skills/nj-rank) | Register finished work with its evidence and file it as Done |

### 📄 Documents and writing

| Skill | What it does |
|---|---|
| [pdf-typography](nj-plugin/skills/pdf-typography) | PDFs whose text stays real: selectable, searchable, then audited |
| [arabic-english-proofreading](nj-plugin/skills/arabic-english-proofreading) | Hamza, taa marbuta, bidi characters, mixed numerals, Latin punctuation in Arabic |
| [workflow-diagram](nj-plugin/skills/workflow-diagram) | Workflow figures drawn from evidence, BPMN-correct |
| [nj-writer](nj-plugin/skills/nj-writer) | Narration and script words, Arabic or English |
| [impact-copy](nj-plugin/skills/impact-copy) | Impact-first, metric-driven copy |
| [website-fine-print](nj-plugin/skills/website-fine-print) | Pre-ship site audit: privacy, hygiene, policy pages |

### 🎬 Audio and video

| Skill | What it does |
|---|---|
| [voice-clean](nj-plugin/skills/voice-clean) | Master a voiceover to broadcast loudness with ffmpeg only |
| [bg-music](nj-plugin/skills/bg-music) | Licence-cleared music beds and SFX, with credit lines |
| [nj-director](nj-plugin/skills/nj-director) | Plan the picture of a 30–90 s film: beat sheet, shots |

### 🧰 Bundled with the kit ([`nj-kit/bundled`](nj-kit/bundled))

nj-evidence · nj-knowledge-book · nj-researcher · nj-style-film · nj-motion-deck · nj-laya · nj-pinterest · srs-verifier · safe-delete · pdf-typography, plus third-party design skills (brandkit, design-taste-frontend, high-end-visual-design, minimalist-ui, redesign-existing-projects, hyperframes-studio, general-video) and graphify. Credits in [THIRD_PARTY.md](THIRD_PARTY.md).

<a id="nj-font"></a>

## 🔤 NJ-Font

A typeface by Nader Alzghoul, installed from this repo in one go. 🚧 Coming soon: star the repo to hear when it ships.

**macOS / Linux:**

```bash
git clone https://github.com/NJ-Burrito/NJ-Kit
cd NJ-Kit
cp NJ-Font/ttf/*.ttf ~/Library/Fonts/                                                  # macOS
mkdir -p ~/.local/share/fonts && cp NJ-Font/ttf/*.ttf ~/.local/share/fonts/ && fc-cache -f   # Linux
```

**Windows (PowerShell, no admin needed):**

```powershell
git clone https://github.com/NJ-Burrito/NJ-Kit
cd NJ-Kit
$dir = "$env:LOCALAPPDATA\Microsoft\Windows\Fonts"; New-Item -ItemType Directory -Force $dir | Out-Null
Get-ChildItem NJ-Font\ttf\*.ttf | ForEach-Object {
  Copy-Item $_ $dir
  New-ItemProperty "HKCU:\Software\Microsoft\Windows NT\CurrentVersion\Fonts" -Name "$($_.BaseName) (TrueType)" -Value "$dir\$($_.Name)" -Force | Out-Null
}
```

**Web:**

```css
@font-face { font-family: "NJ-Font"; src: url("NJ-Font/woff2/NJ-Font-Regular.woff2") format("woff2"); font-display: swap; }
```

Fonts land in your user font folder, so no admin rights are needed. Restart open apps to see them. Details: [NJ-Font/README.md](NJ-Font/README.md).

## Is it safe?

🔒 No credentials in the repo: every key and URL is read from an environment variable or `~/.claude/secrets/`

🗑️ Deletions go to the recycle bin (`safe-delete`), never `rm -rf`

🧪 Gates are scripts: a skill can't report PASS without the check running

🛡️ A guard hook blocks reads of secret paths by sub-agents

## Questions

**Is it free?**
Yes. MIT licence.

**Do I need all of it?**
No. Copy one skill folder into `~/.claude/skills/` and it works on its own.

**Arabic?**
Yes. Arabic and English are both first-class, RTL included.

**Paths?**
Nothing is tied to one machine. Set `NJ_PLUGIN_ROOT`, `JIRA_BASE_URL`, `PORTAL_URL` and the other variables a skill names, or keep the defaults under your home folder.

## Creator and contributors

| | Who | Contact |
|---|---|---|
| 🛠️ **Creator** | **Nader Alzghoul** ([@NJ-Burrito](https://github.com/NJ-Burrito)) | naderalzghoulbusiness@gmail.com · [Portfolio](https://nj-burrito.github.io/) · [LinkedIn](https://www.linkedin.com/in/nader-alzghoul) |

Want to be listed here? See [CONTRIBUTING.md](CONTRIBUTING.md).

<br>

[Contributing](CONTRIBUTING.md) · [Security](SECURITY.md) · [Changelog](CHANGELOG.md) · [Third-party credits](THIRD_PARTY.md)

Free and open source under the [MIT licence](LICENSE). Not affiliated with or endorsed by Anthropic.
