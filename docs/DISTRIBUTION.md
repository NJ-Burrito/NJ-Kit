# NJ-Kit distribution: where it is listed and who does each step

NJ-Kit is a skills pack for AI agents. Skill markets only: no MCP server, no MCP listings (owner decision, 2026-10-22).
It is independent and not affiliated with Anthropic. No listing name contains "claude-" or "anthropic-".
Ready-to-paste texts: `docs/listings/`. Privacy statement for every listing: `docs/PRIVACY.md`. Website: https://nj-burrito.github.io/NJ-Kit/ (built by the site lane; live once GitHub Pages is on).

Who: **Lead/CI** = the build session; **The maintainer** = needs his own login or click.
Status values: `todo`, `ready` (files done, waiting for a step), `submitted`, `live`. Update the dated row after each step.

## Order

1. Merge and push `njkit-markets` (Lead). 2. Switch on GitHub Pages so the homepage URL works (maintainer or Lead).
3. Self-hosted install works at once, no review. 4. Smithery skills. 5. Anthropic plugin directory (review).

## Status

| Directory | Needs first | Who | Status | Date | Link |
|---|---|---|---|---|---|
| Own marketplace (`/plugin marketplace add NJ-Burrito/NJ-Kit`) | repo public | none | live (already in README) | | https://github.com/NJ-Burrito/NJ-Kit |
| Smithery Agent Skills | merge and push; Smithery login | The maintainer | ready | 2026-10-22 | smithery.ai/skills/naderalzghoulbusiness (account page, as for Profile-Wrap) |
| Anthropic plugin directory | merge and push; Pages live; `claude plugin validate --strict nj-plugin` passes; paid claude.ai plan | The maintainer | ready | 2026-10-22 | https://claude.ai/directory/manage |
| Official MCP Registry, mcp.so, Glama | | | not applicable (no MCP server) | 2026-10-22 | |

## 1. Own marketplace (works now)

`/plugin marketplace add NJ-Burrito/NJ-Kit`, then `/plugin install nj-kit@nj-kit`. The marketplace file is `.claude-plugin/marketplace.json`;
the plugin folder is `nj-plugin`, whose manifest is `nj-plugin/.claude-plugin/plugin.json`. Bump `version` in both files each release.

## 2. Smithery (Agent Skills)

Needs: a Smithery account (the maintainer's, `naderalzghoulbusiness`); the repo public with the skills on `main`.
Files: each skill is `nj-plugin/skills/<name>/SKILL.md` with `name` and `description` frontmatter (all 23 parse as YAML; `nj-rank` was
fixed because its unquoted description broke the parser). Text to paste: `docs/listings/smithery.md`.
Smithery's screens can change, so where a label differs follow the screen. Steps, as done for Profile-Wrap:

1. [ ] Open https://smithery.ai and sign in (GitHub login is fine).
2. [ ] Go to the Skills area and choose to add or publish a skill from a GitHub repository.
3. [ ] Pick `NJ-Burrito/NJ-Kit`, branch `main`, and the folder `nj-plugin/skills`. Add skills one folder at a time if it asks for a single skill folder.
4. [ ] Paste the one line and long description from `docs/listings/smithery.md` where it asks for a description.
5. [ ] Confirm each skill shows its own name and description, then publish.
6. [ ] Put the resulting link and the date in the status table above.

Not verified: how Smithery reads a folder of many skills (one import or one per skill). Do not choose the MCP form: it takes hosted MCP URLs only, and NJ-Kit has none.

## 3. Anthropic plugin directory (Claude Code)

Needs: paid claude.ai plan; `njkit-markets` merged and pushed; the website URL live; `claude plugin validate --strict nj-plugin` passing.
Files: `nj-plugin/.claude-plugin/plugin.json` (homepage, repository, license, documentation, support, privacy and terms URLs),
`nj-plugin/SUBMISSION.md` (the click-by-click checklist, followed as written), `docs/listings/anthropic-plugin-directory.md`, `docs/PRIVACY.md`.
Only the maintainer submits: open https://claude.ai/directory/manage and follow `nj-plugin/SUBMISSION.md` sections A to D.

## Open points

- `claude plugin validate --strict` could not be run by the build agent (no `claude` command on its shell). The Lead or the maintainer runs it before submitting.
- The plugin folder holds about 465 files, including bundled CC0 audio in `bg-music`. Whether the directory's size limits accept that is not verified.
- Six Jira skills are in the pack. They are generic REST users, but their reference files name a PROJ project; check `nj-plugin/skills/nj-jira/references/PROJ.md` is something you want public before submitting.
