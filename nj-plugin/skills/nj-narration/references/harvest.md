# Harvest: voices out of noisy, multi-speaker clips

How a library of reference voices was cut from 12 long recordings (voices, music, effects, overlap) on one 6 GB GPU, free tools only,
nothing sent to a cloud. Run once per source; the result is a folder of 6 to 12 s references with metadata, not finished audio.
Licence and consent come first (`SKILL.md` hard rules): harvest only what you may clone, and record provenance per voice.

## Pipeline

| Stage | Pick | Why / settings |
|---|---|---|
| extract | ffmpeg | mono, 44.1 kHz PCM from m4a/mp4 |
| vocal separation | `audio-separator` with a MelBand-RoFormer vocals checkpoint (Kim, SDR 12.6) | best vocal-versus-music/effects model in the package that fits 6 GB; about 6x realtime on an RTX 2060 (22 min in about 4 min); whole file, so no chunk seams |
| de-reverb | same package, a MelBand-RoFormer de-reverb checkpoint (SDR 19.2) | also leaves digital silence between phrases, which acts as the denoise |
| denoise | none; a 70 Hz high-pass only | the separated stems already have a digital-silence floor; a further spectral denoiser only eats voice |
| VAD | silero-vad | small, accurate, CPU |
| speaker embeddings | SpeechBrain `spkrec-ecapa-voxceleb` (ECAPA-TDNN) on 2 s windows | public, no token (pyannote needs a gated hub token, so it was not used) |
| clustering | scikit-learn agglomerative, cosine distance, average linkage | see below |
| metrics | parselmouth, librosa, pyloudnorm | F0, HNR, formants, centroid, tilt, LUFS |

Keep both stems: the raw vocal stem (before de-reverb) and the cleaned one. Cut references from the cleaned one; keep the
raw one for comparison and for slices where de-reverb smears a transient.

## Clustering

1. VAD, then 2 s windows, one embedding each.
2. Window clusters: agglomerative at cosine distance about 0.7, then a 5-window temporal majority smoothing so a speaker does not flicker between clusters.
3. **Cross-clip merge only on evidence**: merge two cluster centroids when centroid cosine is at least 0.55 inside the same clip or 0.66 across clips, **and** the median F0 differs by less than about 0.35 octave. Clips known to hold a single speaker are never merged with another clip below 0.78.
4. Thresholds were chosen by reading the similarity matrices, not tuned to hit a target voice count.
5. Drop windows that are: low similarity to the cluster centroid (overlap or another voice), F0 outliers, unvoiced, clipped, or buried in bleed (mix more than 9 dB louder than the vocal stem). Never keep a fragment under 1 s. A cluster with under 8 s of surviving windows is not filed.
6. Write a `meta.json` per voice with the counts dropped for each reason.

## Choosing the reference (6 to 12 s)

Pick the longest clean run inside one voice: no overlap, no music bleed, no clipping, full sentences, ends on a breath rather than mid-word.
The engine used in the run reads about 6 s for its language-model prompt, so 6 to 12 s gives a choice without padding.
Edge-clean it once (`scripts/voice_edges.py clean --no-pad`), then measure the cleaned file (`references/reference-prep.md`).
Store a transcript beside it. Slices shorter than 5 s are flagged for the owner's ear.

## Pitfalls we hit

- **DeepFilterNet** (0.5.6) imports `torchaudio.backend`, removed in the torchaudio that the CUDA torch build needs (torch 2.5.1+cu121). It cannot run next to the GPU stack. Not worth a second environment, because separated stems are already clean.
- **Generative enhancers** (Resemble-Enhance and similar) can change timbre: wrong for a cloning reference. Dropped.
- **pyannote** needs a gated token: use ECAPA plus your own clustering, or get a token on the owner's word.
- **Under-segmentation**: sources said to hold about 20 voices yielded 10 and 5 clusters plus fragments. One 366 s voice did not split under 2 or 3-way k-means (silhouette 0.15) but is long enough to hide similar voices. Report counts as lower bounds.
- **A multi-persona performer** (one actor, many ages) does not separate on ECAPA: inter-window similarity near 0.4 everywhere, no contiguous blocks. File it as one voice with a wide F0 range; do not split by guess.
- **The same performer in two clips** (centroid similarity about 0.51) stays two voices, flagged as possible duplicates. Embeddings do not settle identity.
- **No overlap model**: overlap is caught by low speaker similarity, F0 outliers and loudness bleed rules, which is rule-based and imperfect.
- **Labels beat guesses**: where the source gives a gender, age or dialect, keep it; estimate only for unlabelled clips, and store estimates as estimates (`attributes_estimated`) with a confidence.
- **Child check on unlabelled clips**: apply the veto from `references/listening.md`; a tripped clip is filed apart, never cloned, with a note. A labelled teenager counts as a child until provenance says otherwise.
- **Emotion slices from heuristics** (loudness, pitch, voicing, envelope periodicity) are rough: only 7 of 24 voices got any slice, the laugh rule was deliberately strict so real laughs are missed, and crying is not detected. See `references/emotions.md` before conditioning on one.
- A downloaded model file can be corrupt (a protobuf error on load): re-fetch and check it loads before trusting a run.
- Nothing in this chain was listened to. The result is "needs a human ear".
- Caches and models belong on the data drive of your choice; set the cache variables before the first run so the system drive stays clean.
