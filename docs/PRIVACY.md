# NJ-Kit privacy statement

Last updated: 2026-10-22. Applies to NJ-Kit (the `nj-kit` plugin and its skills in https://github.com/NJ-Burrito/NJ-Kit).
NJ-Kit is independent open source software (MIT). It is not affiliated with Anthropic.

## Short version

- NJ-Kit is files: skill instructions (Markdown) and small helper scripts. It has no server, no account, no analytics and no telemetry. The maintainer receives nothing.
- The skills run inside your own AI assistant session, on your machine. What your assistant sends to its provider is governed by that provider's terms, not by NJ-Kit.
- NJ-Kit contains no credentials. A skill that needs a login reads it from your environment variables or from `~/.claude/secrets/` on your machine.

## What the scripts do with data

This list comes from reading the scripts in `nj-plugin/skills/`. Anything not listed makes no network call of its own.

| Skill | Network call | What is sent |
|---|---|---|
| `bg-music` (`fetch_music.py`) | `https://api.openverse.org/v1/audio/` | A search query for music or sound effects, and the download of the track you choose. Only when you run the fetch script. |
| `pdf-typography` (`fetch-fonts.mjs`) | `https://fonts.googleapis.com` | A request for the open-licence font family you name. Only when you run the font fetch. |
| `nj-rank`, `nj-jira`, `nj-wrapup`, `nj-qa-pipeline`, `nj-jira-to-automation` | Your own Jira server, at the address you give | The tickets, comments and attachments you tell the skill to file, using the user and password you supply through environment variables or a credentials file on your machine (`~/.claude/secrets/jira.json` for `nj-rank`). The skills are written not to print, log or store the password, and send it only to your Jira server. These skills are for people who run a Jira instance; do not install them if you do not. |
| `nj-agent-ops` (`relay.py`) | None | Writes a run ledger and result files in the project folder you run it in. Nothing leaves the machine. |
| All other skills | None | Instructions and local scripts only (for example proofreading, PDF checks, ffmpeg voice cleaning). |

The plugin has no install hooks: nothing runs when you install it. The repository keeps no project archives or research logs. Heavy optional parts (the graphify package, a researcher source registry, tashkeel evidence runs) are not in the tree: `nj-kit/scripts/fetch_assets.py` downloads them only when you ask, from PyPI or this repository's GitHub release, and checks a sha256 first.

## What stays on your machine

Everything a skill creates (handoff files, ledgers, notes, reports, test folders, audio and PDF output) is a plain file in the folder you work in. NJ-Kit does not upload it anywhere.

## Your AI assistant

Skills are instructions your assistant follows. The text of your requests, and any file the assistant reads while following a skill, goes to the assistant's provider (for example Anthropic for Claude Code). Read that provider's privacy policy; NJ-Kit does not change it and does not add a second recipient.

## Third parties

Openverse, Google Fonts and your Jira server have their own terms and privacy policies. NJ-Kit contacts them only as shown in the table, and only when you run the matching script.

## Update check

NJ-Kit performs no update check. You get new versions when you run `/plugin marketplace update nj-kit` or reinstall.

## Contact

Privacy questions or a vulnerability report: naderalzghoulbusiness@gmail.com, or the issues page at https://github.com/NJ-Burrito/NJ-Kit/issues (see also `SECURITY.md`).

## Changes

A change to this statement is committed to this file with its date at the top.
