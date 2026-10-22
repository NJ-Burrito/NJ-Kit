"""Voice the beats once with Gemini TTS through OpenRouter, place them, write the SRT.

    PYTHONUTF8=1 python voice.py

Reads beats.json. Writes vo/NN.wav (cached per line), narration.wav, narration.srt.
The key is read from ~/.config/qa-wrap/openrouter.env at run time and never written.
"""
import json
import os
import struct
import time
import urllib.request
import wave

HERE = os.path.dirname(os.path.abspath(__file__))
SR = 24000
VOICE = "Aoede"
DIRECTION = ("Read this at a calm, natural, conversational pace, warm and sure, "
             "like one tester talking to another. Fall at the end: ")
GAP = 0.35       # rest between two lines when beats.json names none
END_TAIL = 2.2   # the end card holds this long after the last word


def key():
    with open(os.path.expanduser("~/.config/qa-wrap/openrouter.env"), encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("OPEN_ROUTER_TOKEN"):
                return line.split("=", 1)[1].strip().strip('"')
    raise SystemExit("no OPEN_ROUTER_TOKEN in ~/.config/qa-wrap/openrouter.env")


def speak(text, token, direction=None):
    body = json.dumps({"model": "google/gemini-3.1-flash-tts-preview", "input": (direction or DIRECTION) + text,
                       "voice": VOICE, "response_format": "pcm"}).encode()
    for attempt in range(8):  # the endpoint often answers 200 with an empty stream
        req = urllib.request.Request("https://openrouter.ai/api/v1/audio/speech", data=body, headers={
            "Authorization": "Bearer " + token, "Content-Type": "application/json"})
        try:
            pcm = urllib.request.urlopen(req, timeout=120).read()
        except Exception as err:  # noqa: BLE001 - report and retry
            print("   retry", attempt + 1, type(err).__name__)
            pcm = b""
        if len(pcm) > SR:  # more than half a second of s16le
            return pcm
        time.sleep(1.2)
    raise SystemExit("no audio after 8 attempts: " + text)


def trim(pcm, floor=300):
    """Drop leading and trailing near-silence so placement is by the first word."""
    n = len(pcm) // 2
    s = struct.unpack("<%dh" % n, pcm[:n * 2])
    first = next((i for i, v in enumerate(s) if abs(v) > floor), 0)
    last = next((i for i in range(n - 1, -1, -1) if abs(s[i]) > floor), n - 1)
    first, last = max(0, first - 480), min(n, last + 1200)
    return pcm[first * 2:last * 2]


def stamp(t):
    ms = int(round(t * 1000))
    return "%02d:%02d:%02d,%03d" % (ms // 3600000, ms // 60000 % 60, ms // 1000 % 60, ms % 1000)


def main():
    beats = json.load(open(os.path.join(HERE, "beats.json"), encoding="utf-8"))
    os.makedirs(os.path.join(HERE, "vo"), exist_ok=True)
    token = key()
    clips = []
    for b in beats["beats"]:
        path = os.path.join(HERE, "vo", "%02d.pcm" % b["n"])
        if not os.path.exists(path):
            print("voicing", b["n"])
            # The model sometimes performs a line instead of reading it (a 12-word
            # line came back 14 s long). A take far over its word count is redrawn.
            limit = len(b["line"].split()) / (beats["wpm"] / 60) * 1.45 + 0.6
            # rehearsal-0921 (hole: NARRATION.md #6 said direction from the
            # script, voice.py still read a fixed constant): a beat's own
            # `direction` field, when beats.json carries one, replaces
            # DIRECTION so the writer's per-line direction is what is voiced.
            direction = b.get("direction")
            for draw in range(4):
                pcm = trim(speak(b["line"], token, direction))
                if len(pcm) / 2 / SR <= limit:
                    break
                print("   take %.1f s is over %.1f s, drawing again" % (len(pcm) / 2 / SR, limit))
            with open(path, "wb") as fh:
                fh.write(pcm)
            time.sleep(1.2)
        clips.append(open(path, "rb").read())

    # Lines are placed back to back on the REAL takes, never on the estimate:
    # the estimate left rests of up to 2.2 s (first reel, 20 Sept). The rest
    # between two lines is "gap" in beats.json (per beat, else top level).
    out, srt, t, plan = bytearray(), [], 0.0, 0.0
    for b, pcm in zip(beats["beats"], clips):
        start = t + b.get("gap", beats.get("gap", GAP)) if t else beats["lead_in"]
        out += b"\0\0" * (int(start * SR) - len(out) // 2)
        out += pcm
        t = len(out) / 2 / SR
        srt.append("%d\n%s --> %s\n%s\n" % (b["n"], stamp(start), stamp(t), b["line"]))
        print("%2d  %6.2f -> %6.2f  (%.2f s)" % (b["n"], start, t, t - start))
        plan += b["dur"]
    out += b"\0\0" * int(END_TAIL * SR)
    with wave.open(os.path.join(HERE, "narration.wav"), "wb") as w:
        w.setnchannels(1), w.setsampwidth(2), w.setframerate(SR)
        w.writeframes(bytes(out))
    with open(os.path.join(HERE, "narration.srt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(srt))
    print("TOTAL %.2f s" % (len(out) / 2 / SR))


if __name__ == "__main__":
    main()
