# Third-party credits

## Libraries

| Library | File | Licence |
|---|---|---|
| GSAP 3.15 | `nj-kit/bundled/nj-style-film/templates/vendor/gsap.min.js` | GreenSock Standard "No Charge" License — https://gsap.com/standard-license |
| GSAP 3.15 + ScrollTrigger (website only) | `site/vendor/gsap.min.js`, `site/vendor/ScrollTrigger.min.js` | GreenSock Standard "No Charge" License, https://gsap.com/standard-license |
| transitions.dev UI generation (website only) | `site/vendor/ui-generation.js`, `site/vendor/text-image-generation.js`, `site/vendor/ui-generation.css` | (c) 2026 Jakub Antalik / Transitions.dev, used on this website under https://transitions.dev/terms.html; not part of the kit and not offered as a library |

## Skills by other authors (in `nj-kit/bundled`)

brandkit, design-taste-frontend, high-end-visual-design, minimalist-ui, redesign-existing-projects, hyperframes-studio, general-video and graphify are the work of their original authors and are included with credit; `nj-kit/manifest.json` records each one's source. `install.py` re-fetches them from source so you get the current version. The graphify package itself (Apache-2.0 and MIT, PyPI `graphifyy` 0.9.66) is not stored in this repository: `nj-kit/bundled/graphify` keeps only its `skill.md`, and `python nj-kit/scripts/fetch_assets.py graphify-package` downloads the rest from PyPI and verifies its sha256. If you are an author and want yours removed, open an issue.
