---
name: nj-listen
description: 'Give Claude ears: turn a meeting recording (audio or video, multitrack, minutes to hours) into who said what and when, locally, free and open source, no cloud. Built for Arabic dialects (Jordanian, Levantine) with MSA and English words mid-sentence, people talking over each other on one table mic. Speakers named from their self-introductions. Use for: transcribe a meeting, UAT or sprint recording, minutes from a recording, who said what, speaker names, voice notes to text. Arabic: فرّغ التسجيل، تفريغ اجتماع، تحويل الصوت إلى نص، من قال ماذا، محضر من تسجيل.'
---

# nj-listen

Claude cannot hear audio. This skill is the ear: a local engine that turns a recording into a timed,
speaker-labelled transcript, which Claude then reads (dialect clean-up, English terms, facts, decisions).

**Rules it keeps:** Claude models only for every AI step; speech-to-text is a local open model, not an API.
Free of charge, open source. Client audio never leaves the machine.

## Run it

```
PYTHONUTF8=1 uv run --no-project --with openvino-genai --with sherpa-onnx --with soundfile --with numpy --with huggingface_hub \
  python scripts/listen.py run <media> <out_dir> [--prompt "terms the meeting uses: Docker, sprint, payment gateway"] [--enroll enroll.json]
```

- `<out_dir>` gets one checkpoint per stage: `probe.json` → `track-<n>.wav` → `sweep.json` → `transcript.json` ∥ `speakers.json`
  → `named.json` (with `--enroll`) → `result.json`. A re-run resumes at the first missing checkpoint.
- Progress is one JSON line per event on stdout. `touch <out_dir>/PAUSE` pauses, `<out_dir>/STOP` stops (exit 3).
- `--prompt`: name the English terms and the topic. It is what keeps `Kubernetes` in Latin script instead of `كبرنتيس`.
- `--enroll`: `{"name": [[start, end], ...]}`, the seconds where each person introduced themselves. Without it, speakers are
  clusters (`t0s3`); with it, names, and a voice that matches nobody stays `Unknown`.
- `python scripts/listen.py --selftest` checks the pure logic with no models (CI).

## The engines and why

| Stage | Engine | Licence | Why this one (measured 2026-11-12, i5-1334U + Iris Xe, no GPU card) |
|---|---|---|---|
| Speech regions | Silero VAD (sherpa-onnx) | MIT | skips silence; 49.8 min in 31 s |
| Speech-to-text | Whisper large-v3-turbo int8, OpenVINO GenAI, **Intel iGPU** | MIT / Apache-2.0 | RTF 0.42 on the iGPU vs 0.97 OpenVINO-CPU, 1.33 faster-whisper-CPU; keeps dialect. `medium` turned dialect into MSA and invented words |
| Speakers | pyannote-segmentation-3.0 + CAM++ (sherpa-onnx) | MIT / Apache-2.0 | RTF 0.17; runs as **its own process** (sherpa holds the GIL; as a thread it serialised the whole run) |
| Names | ERes2Net base voiceprints | Apache-2.0 | 15/15 on a labelled 3-person test (CAM++ 7/15, WeSpeaker 10/15); threshold 0.53 sits between other-person max 0.45 and same-person min 0.61 |

Whole pipeline: 49.8 min of Jordanian-dialect podcast in 18.8 min wall (RTF 0.38), so 2 h ≈ 45 min.

## What Claude does with `result.json`

1. Read `segments` (`start`, `end`, `speaker`, `text`, `loop`, `mixed`).
2. Fix English terms written in Arabic script or misheard (`word of math` → `word of mouth`) from context, never inventing content.
3. Treat `loop: true` (a decoding loop, collapsed) and `mixed: true` (two voices in one chunk) as low confidence: show them, do not quote them as facts.
4. Extract decisions, requirements, open questions, each with its timestamp and speaker.

## Recording protocol that makes it work

The leader opens with the meeting title, purpose and type; every attendee says name and role (Arabic, English too if they like);
after each stage, the client summarises what was agreed without interruption. The intros become the `--enroll` windows; the
summaries are the high-value spans. Several people on one mic: each still introduces themselves.

## Limits, stated plainly

- Same-mic voices separate less cleanly than the labelled test (which used different recordings); the preview lets a person re-assign a name.
- Overlapping talk is flagged, not separated.
- No timestamps inside a chunk (chunks are ≤ 28 s).
- Source of truth for the code: Business-Wrap `engine/listen/listen.py`; this copy is synced from it.
