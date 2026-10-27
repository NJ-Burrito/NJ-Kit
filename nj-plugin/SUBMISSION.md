# Submit NJ-Kit to Anthropic's plugin directory (the maintainer, from his own account)

Portal wording can change. Where a label below differs on screen, follow the screen and keep the intent. Everything here is
done by you; nothing is submitted automatically. Model: the Profile-Wrap checklist (same portal).

## A. Before you open the portal

- [ ] You have a paid claude.ai plan and can sign in at https://claude.ai.
- [ ] The branch `njkit-markets` is merged and pushed, so `main` of https://github.com/NJ-Burrito/NJ-Kit contains `nj-plugin/.claude-plugin/plugin.json` and `docs/PRIVACY.md`.
- [ ] These open in a private browser window (they are in `plugin.json`): README, LICENSE, `docs/PRIVACY.md`, the issues page.
- [ ] `https://nj-burrito.github.io/NJ-Kit/` opens (GitHub Pages switched on). It is the `homepage`; do not submit before it does.
- [ ] In the repo folder run `claude plugin validate --strict nj-plugin`. It must say "Validation passed". (Not run by the build agent: the `claude` command was not available there.)
- [ ] Optional dry run: `claude plugin marketplace add NJ-Burrito/NJ-Kit`, then `claude plugin install nj-kit@nj-kit`. It should install version 2.0.1 with 23 skills.

## B. Facts the portal checks

| Check | State |
|---|---|
| `.claude-plugin/plugin.json` in the submitted folder | `nj-plugin/.claude-plugin/plugin.json` |
| Name lowercase, digits, hyphens, not reserved, no "claude-" or "anthropic-" | `nj-kit` |
| README, `LICENSE`, `license` field | repo README, MIT in both |
| No hooks, no MCP launchers | none in the plugin |
| No credentials | none in the repo; `SECURITY.md` and CI keep it so |
| Directory fields | `documentationUrl`, `supportUrl`, `privacyPolicyUrl`, `termsOfServiceUrl`, `homepage`, `repository` set; no `icon` yet (add one only if the portal asks) |

Not verified by the build agent: file counts and sizes against the portal limits (Profile-Wrap's checklist cites under 512 files,
each under 256 KiB, no binaries). `nj-plugin` has about 465 files and carries bundled audio in `bg-music`, so check the portal's
report; if it objects, tell the Lead before changing anything.

## C. Submit, click by click

1. [ ] Open https://claude.ai/directory/manage and sign in with your paid account.
2. [ ] Click the button to submit a new plugin.
3. [ ] Choose GitHub as the source and authorise the connection if asked. Grant access to `NJ-Burrito/NJ-Kit` only.
4. [ ] Select the repository `NJ-Burrito/NJ-Kit`, branch `main`.
5. [ ] For the plugin folder enter `nj-plugin`.
6. [ ] Wait for the automatic checks. If one fails, copy its message and fix the file it names; do not edit portal fields to hide it.
7. [ ] Check the preview: name `nj-kit`, version 2.0.1, MIT, and the links. Paste the texts from `docs/listings/anthropic-plugin-directory.md`.
8. [ ] If asked about MCP servers: there are none. If asked about data: nothing leaves the machine except the calls listed in `docs/PRIVACY.md`.
9. [ ] Accept the Anthropic Software Directory Policy only after you have read it (not read by the build agent).
10. [ ] Press submit. Save the confirmation page or email.

## D. After submitting

- [ ] A scan runs first. If it fails, read its message before resubmitting.
- [ ] A reviewer may ask questions by email. Answer from the README and `docs/PRIVACY.md`.
- [ ] Once approved, record the link and date in `docs/DISTRIBUTION.md`.
- [ ] Each later release: bump `version` in `nj-plugin/.claude-plugin/plugin.json` and in the root `.claude-plugin/marketplace.json`, then resubmit.

## E. No review needed

Users can already install from the repo: `/plugin marketplace add NJ-Burrito/NJ-Kit`, then `/plugin install nj-kit@nj-kit`.
