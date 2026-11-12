# BRIEF: {film id}

Fill from the user's message and the product's own files. `REQUIRED` slots
block stage 1 until filled (`mm.py gate <project> 1`). An empty `fallback:`
slot is not a question: use the fallback and note it under *Fallbacks used*.

## Product
- product: REQUIRED
- one-line what it does: REQUIRED
- truth sources (README, CHANGELOG, site, UI strings): REQUIRED
- brand files (logo, tokens, fonts, sounds): fallback: none, crew derives from the site
- brand names to keep Latin and pronounce as in English: fallback: the product name

## Film
- kind (commercial / launch / brand film / teaser): fallback: commercial
- length seconds: REQUIRED
- audience: REQUIRED
- why this film (verbatim owner words, e.g. what was wrong with the last one): REQUIRED
- what to emphasise: fallback: the crew decides from claims.md
- references (videos, sites, owner's portfolio, posts): REQUIRED
- call to action: REQUIRED
- end-card lines (site, repo, maker, chips): REQUIRED

## Deliverables matrix
- aspects: fallback: 16:9 1920x1080 + 9:16 1080x1920
- languages: fallback: en + ar
- destinations (site folder, desktop copy, repo release): fallback: <project>/out only

## House (defaults from SKILL.md; write changes under overrides)
- voice: Kore, google/gemini-3.1-flash-tts-preview via OpenRouter, one take per line
- pace: en 150 wpm, ar 115 wpm, tempo cap 1.7
- type: Thmanyah only, house sizes -2
- crew model: fallback: session model
- overrides: fallback: none

## Fallbacks used
