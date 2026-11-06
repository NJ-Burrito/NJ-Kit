# Recording spec for a commissioned reference voice

Give this to the speaker or the studio with the consent record. The goal is a reference the gates accept as recorded, so
that no denoise, gate or repair is needed (those are exactly what the gates refuse).

| Item | Spec |
|---|---|
| Script | Written by the writer stage in the language and register of the character (MSA: fully vowelled). It covers: a neutral read, then one block per register the character uses (for example calm, tender, angry, afraid), and a few names and numbers from the lexicon. About 60 s of finished speech per register. The transcript is the script itself, saved beside each file; never produced by ASR |
| Room | A quiet, dry, treated space or a vocal booth; no hard parallel walls close to the mic. Target as recorded: reverb decay (20 dB fall) at most 0.15 s, floor at most -53 dBFS (the REF-QUALITY limits). Switch off fans, AC, fridge, phones. Record 10 s of room tone at the start and end of each session |
| Microphone | One studio microphone (large-diaphragm cardioid condenser or a dynamic suited to voice), pop filter, 15 to 20 cm, same position for every register and session. No USB headset, no phone, no laptop mic |
| Format | WAV, mono, 48 kHz, 24-bit, as recorded. No MP3, no AAC |
| Level | Peaks between -12 and -6 dBFS, no sample at full scale. Gain set once per session |
| Processing | None: no denoise, no noise gate, no compressor, no EQ, no auto-level, no normalise. Hum and clicks are fixed at the source (re-record), not scrubbed |
| Delivery | Original files, untouched, with the transcripts; the producer computes the sha256 of each file on receipt and writes them into the consent record |
| Takes | The speaker may read a block as often as they like; the producer chooses the clip to use at casting. (This is human recording; the one-take rule is for the TTS output.) |
| Mouth and breath | Water at hand; breaths between phrases are fine; no throat clears or lip smacks inside the reference |
| Child register | Never record a child for cloning. An adult actor performs the child lines as ordinary recorded speech or as the reference for an adult-register child voice, with their own consent record |

After delivery: edge clean once (`voice_edges.py clean ... --no-pad`), cut the 5-8 s clips per register
(`references/reference-prep.md`), run `voice_measure.py ref` on the clip you will clone, record everything in the provenance file.
