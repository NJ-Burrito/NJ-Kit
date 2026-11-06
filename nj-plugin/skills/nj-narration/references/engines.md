# Engines: the decision table (research 2026-11-07)

The engine is the owner's recorded decision per project. This table is evidence for that decision, not the decision.
Order of criteria: licence of weights and of output (commercial use), training-data provenance, local and free over paid,
language and register (MSA with vowelled input, or a named dialect), fits the GPU, then the owner's ear on one throwaway line
per engine. Paid TTS is used only on the owner's word. Vendors a project has banned stay banned and are listed in its engine
record. Prices are as printed on the cited page on the fetch date; many pages are undated; an aggregator is a third-party
blog or tracker, not the vendor.

## 1. Local engines

| Engine | Licence | Arabic | Cost | Status and notes |
|---|---|---|---|---|
| Chatterbox Multilingual | MIT, local GPU (about 3.6 GB VRAM measured on 0.1.7) | one of 23 languages, clones from a reference | free | **README notice, fetched 2026-11-07: "As of August 2026, Chatterbox is retired research and is no longer maintained. The code stays public as an archive under the MIT license, with no support, updates, or paid tier."** It names no successor, the same README still calls "Multilingual V3" the latest release, and a web search did not confirm the notice (one primary statement, unconfirmed). **Staying on it or leaving it is an owner decision**, not a silent switch; an engine change re-opens reference preparation, the generation caps and the owner's ear. The archive stays usable under MIT |
| SILMA TTS v1 | Apache-2.0 weights, MIT code | MSA with vowelled input, 150 M parameters, 3 GB VRAM | free | rated "bad" by the owner's ear in the earlier casting: dropped |
| Habibi-TTS | MSA variant Apache-2.0, Gulf variants CC-BY-NC-SA | yes | free | base weights non-commercial: dropped |
| XTTS-v2, MMS-TTS, OmniVoice, Fish S1-mini | non-commercial | various | free | dropped |
| Open alternatives surveyed from secondary sources only | not verified | not verified | free | VibeVoice (up to 90 min, 4 speakers; MIT claimed in a secondary source, check the repo; arXiv:2508.19205), Dia (1.6 B, 2 speakers via `[S1]` `[S2]`, Apache-2.0 code, Arabic unverified), Qwen3-TTS (local, in a Windows skill; not tested). A dedicated open-models survey was not available when this table was written |

## 2. Paid engines (owner's word only)

| Provider | Arabic | Expressive | Price (source, fetched 2026-11-07) | Commercial and cloning |
|---|---|---|---|---|
| ElevenLabs | Multilingual v2 and Flash v2.5 list Arabic (Saudi Arabia, UAE); v3 claims 70+ languages, Arabic unverified | v3 audio tags | elevenlabs.io/pricing (undated): Free $0 (10k credits, no commercial use); Starter $6/mo (30k); Creator $22/mo (121k); Pro $99/mo (600k); Scale $299/mo (1.8M) | terms "last updated 09 October 2026": paid subscribers use commercially; Voice Library voices carry per-voice terms; cloning only a voice you are authorised to use; Professional cloning needs 30+ min of clean audio per voice |
| Microsoft Azure Neural | 32 voices, 16 locales (one female, one male each) | no styles or roles on Arabic voices | learn.microsoft.com: 0.5M characters a month free (F0); USD rates were placeholders in the fetch; aggregators (unverified): Neural about $15-16 per 1M characters, HD about $22-30 | terms not checked; Custom Neural Voice exists, not checked for Arabic or consent |
| MiniMax Speech 2.8 | Arabic listed among about 38-40 languages (aggregators); voice names unverified | emotion controls claimed, not verified | official page showed no TTS figures; aggregators conflict: $60 (Turbo) to $100 (HD) per 1M characters; rapid clone about $1.50 per voice | not verified; provisional |
| Amazon Polly | 3 Arabic voices (Zeina standard; Hala and Zayd neural, Gulf) | limited | aws.amazon.com/polly/pricing (undated): Standard $4, Neural $16, Generative $30 per 1M characters | not checked |
| Cartesia Sonic | Arabic listed by one third-party source; official list not shown | not verified | cartesia.ai/pricing (undated): Pro $5/mo (100k credits), Startup $49/mo (1.25M), Scale $299/mo (8M); 1 credit = 1 character | commercial licence from Pro; instant cloning from Pro |
| OpenAI TTS | Arabic voices not documented on the pages read | steered by instructions | developers.openai.com pricing (undated): `gpt-4o-mini-tts` $0.60 per 1M text tokens + $12 per 1M audio tokens; `tts-1` $15, `tts-1-hd` $30 per 1M characters | not checked; `gpt-4o-mini-tts` shutdown announced 2027-01-06 |

Not shortlisted or unverified: ReadSpeaker, Acapela (quote only), Murf, Play.ht, Fish Audio, Hume, Resemble, Speechify, Gulf-built
engines (CNTXT, Wittify), Telnyx, Hakim: pages blocked, empty or price-less on the fetch. No Arabic listening test was run on any
paid engine; quality claims come from vendor and press pages.

**Cost example, for scale:** 6,000 Arabic characters a day is about 180,000 a month. ElevenLabs Pro $99/mo covers it (600k
credits); Creator's 121k credits do not. Azure fits inside the free 0.5M characters. Polly Neural is about $2.88. MiniMax
about $11-18 at the aggregator rates. Check the vendor page again before committing: several prices above are aggregator
figures.

**Disclosure:** EU AI Act Article 50 has applied since 2 August 2026 and Meta requires an AI label on realistic AI audio
(secondary sources; statute and policy text not fetched). Budget for a label on every episode and check the platform's own
rule.

## 3. Where the industry differs from our rules

ElevenLabs' audiobook suite regenerates single passages until they are right (secondary source, 2026), and its MCP server
advises offering several variations. That is a re-voice and a best-of-N. We keep one take per line.

## 4. Commissioned talent (clean cloning data)

Recommended route: commission Arabic voice actors directly with a written consent record per speaker
(`templates/consent-record.md`, `templates/recording-spec.md`), then clone on the chosen engine only after the signed file
is saved. Marketplace talent (read their terms first), or a studio-data vendor that documents per-talent consent in writing
(confirm Arabic and cloning rights), are the alternatives. Rejected for cloning: voice libraries whose per-voice terms are
unread, consumer cloning apps with unverified consent terms, gig marketplaces, research-only corpora (an open MSA corpus is
non-commercial), telephone-quality catalogues. Professional cloning (30+ min per voice) multiplies recording time: fifteen
voices is about 7.5 hours of recording, the main cost driver. Actor fees, direction, legal review and a vendor quote are
unknown and must be quoted: no total is given here. Child roles: an adult actor, no clone.

## Sources (all fetched 2026-11-07 unless dated)

github.com/resemble-ai/chatterbox; elevenlabs.io/pricing and /terms-of-use (updated 2026-10-09); learn.microsoft.com Speech
language support (ms.date 2026-10-28); aws.amazon.com/polly/pricing; cartesia.ai/pricing; developers.openai.com pricing;
arXiv:2508.19205 (VibeVoice); aggregator price pages as marked.
