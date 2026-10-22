# nj-kit — transfer this to another project or machine

The owner Alzghoul's Claude Code toolkit: 52 skills — 45 re-fetched from public
repos, 7 of his own — plus 3 that belong to the `project-tests` repository and are
linked rather than carried. With them, the working method, the MCP
servers, and the house decisions that make the output come out the same.

## Install

```bash
python nj-kit/scripts/install.py --check    # see what it would do, change nothing
python nj-kit/scripts/install.py            # do it
```

That is the whole thing. `--check` first is worth the ten seconds — it reports
missing tools with the exact command to install each.

**Where the skills land, and why it matters:** `~/.claude/skills/` by default.
They are then private to that machine, active in *every* repo you open, and
impossible to commit by accident. Use `--scope project` to put them in one
repo instead; that adds them to `.gitignore` unless you also pass `--commit`.

## What install.py does

1. **Checks tooling** — `pdftotext`, `pandoc`, `node`, `python`, optionally
   `duckdb`. It looks past `PATH` into the usual Windows install locations,
   because a shell opened before an installer ran reports things as missing
   that are installed.
2. **Installs the skills** — the bespoke ones from `bundled/`, the public ones
   re-fetched from source so you get current versions rather than a stale copy,
   and the ones that belong to a repository **linked, never copied** (a junction
   on Windows, a symlink elsewhere). If that repo is not on the machine the link
   is skipped and said so; nothing is copied in its place.
3. **Refills `pdf-typography`** — the font vault and playwright are excluded
   from the zip to keep it ~186 KB, so they are re-fetched here. Without this
   step the PDF pipeline arrives unable to render anything.
4. **Writes `~/.claude/CLAUDE.md`** — the standing instructions that make
   `nj-method` the default. An existing file is never overwritten; it is
   reported so you can merge by hand.
5. **Applies the privacy settings** — see below.
6. **Adds the MCP servers** — playwright, context7 (Figma removed 2026-10-10; credentials are never shipped — env values are exported as `<set your own>`).
   **Installs the hooks** (2026-10-10) into user settings.json, backup first; paths are rewritten to this machine's home, and a hook whose script is not on this machine is skipped and named.
7. **Audits everything it fetched** for prompt injection, concealment,
   permission bypass and exfiltration, and prints what it found.

Backups are written beside anything it modifies.

## Prerequisites

Only `pdftotext` is genuinely required — everything else degrades gracefully.

| tool | why | install |
| --- | --- | --- |
| **pdftotext** | the only extractor that reads Arabic correctly | `winget install XpdfReader.XpdfTools` |
| pandoc | reads `.docx` sources | `winget install JohnMacFarlane.Pandoc` |
| node | renderers and the skills CLI | — |
| python | the audit and scan scripts | — |
| duckdb | reads `.xlsx` directly | `winget install DuckDB.cli` |

**On Windows, set `PYTHONUTF8=1`.** cp1252 cannot read or print a single Arabic
character, and several scripts crash rather than degrade.

## Privacy

The settings it applies are **user scope — this machine only**. They do not
change anything for anyone else, which matters on a shared Claude account:
Remote Control off, cross-session messages refused, sessions not uploaded to
claude.ai, account skill-sync off.

Be clear about the limit: these stop *your machine* participating. They do not
make a shared login private — anyone with the credentials can sign in elsewhere.
If work must be inaccessible to others, that needs a separate login.

## After installing

Restart Claude Code so the MCP servers and settings load. Then:

```bash
python ~/.claude/skills/nj-security-review/scripts/audit.py --baseline
```

That records what you have accepted, so `--changed` afterwards reviews only what
moves when a skill updates.

## Keeping it current

On the source machine a Stop hook re-exports after every turn, so the manifest,
the bundled skills and `nj-kit.zip` stay current without anyone remembering.
To do it by hand: `python nj-kit/scripts/export.py --zip`.

The parts no hook can derive — `KNOWN_SOURCES`, `house_style`, `tooling`,
`project_skills`, and every `why` note — are updated by whoever changes a skill,
in the same turn. `SKILL.md` says which is which.

A skill that belongs to one repository stays there and is reached by a link. The
exporter scans exactly one directory, so it never sees those; `project_skills`
in the manifest is their record, kept by hand.

## What is in here

| | |
| --- | --- |
| `SKILL.md` | the full guide, including the maintenance rule |
| `manifest.json` | the roster, the house style, the privacy block, the tooling |
| `bundled/` | the skills no registry has, plus `CLAUDE.md` |
| `scripts/install.py` | reproduce the setup |
| `scripts/export.py` | re-snapshot it |
