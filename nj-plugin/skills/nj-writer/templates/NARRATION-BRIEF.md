<!-- Fill this, then: PYTHONUTF8=1 python scripts/narration_brief.py <this-file> -->
<!-- REQUIRED slots have no fallback — narration_brief.py exits 1 if any is missing. -->
<!-- Optional slots fall back per NARRATION.md's OPTIONAL_FALLBACKS table. -->

genre: <!-- REQUIRED: commercial | educational | walkthrough | podcast | event_promo | recruitment | investor_partnership -->
language: <!-- REQUIRED: en | ar -->
destination: <!-- REQUIRED: social_video | podcast_audio | elearning_video | screen_capture_video -->
length_s: <!-- REQUIRED: target length in seconds (or use the matching words_budget_ field's suffix) -->
audience: <!-- REQUIRED: who hears this -->
listener_action: <!-- REQUIRED: the ONE thing the listener does or knows after -->
kb_ids: <!-- optional: kb:12, kb:15 — every factual line needs one or narration_check.py FAILS if sourcing is required -->
lexicon_terms: <!-- optional: terms from templates/LEXICON.md this script uses -->
tone_words: <!-- optional: falls back to the matrix row's register -->
bans: <!-- optional: banned words/claims/phrasing -->
