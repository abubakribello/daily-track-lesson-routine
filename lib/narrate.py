"""Narration: script.json -> narration.wav + timeline.json (Kokoro TTS, sentence by sentence).

Usage:
    python3 lib/narrate.py <script.json> <out_dir> [--voices DIR]

script.json:
{
  "voice": "bm_george", "lang": "en-gb", "speed": 1.0,      # optional
  "lines": [
    {"scene": "overview", "title": "Overview", "text": "Spoken sentence.", "caption": "Optional on-screen text"},
    ...
  ]
}
- "scene" groups lines; a short extra pause is added when the scene changes.
- "title" is shown as the on-screen heading while that scene is active (optional).
- "caption" overrides the on-screen text when the spoken form differs ("P and I D" -> "P&ID").

timeline.json:
{"total": seconds, "lines": [{"i", "scene", "title", "text", "caption", "start", "end"}]}
"""
import argparse, json, os, sys
import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_VOICES = os.path.join(os.path.dirname(HERE), "voices")
SR, LEAD, GAP, SCENE_GAP, TAIL = 24000, 0.6, 0.35, 0.7, 1.0
CAPTION_FIX = {"P and I D": "P&ID", "P and IDs": "P&IDs", "oil water": "oil–water"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("script"); ap.add_argument("out")
    ap.add_argument("--voices", default=DEFAULT_VOICES)
    a = ap.parse_args()
    spec = json.load(open(a.script))
    os.makedirs(a.out, exist_ok=True)
    from kokoro_onnx import Kokoro
    tts = Kokoro(os.path.join(a.voices, "kokoro-v1.0.int8.onnx"), os.path.join(a.voices, "voices-v1.0.bin"))
    voice, lang, speed = spec.get("voice", "bm_george"), spec.get("lang", "en-gb"), float(spec.get("speed", 1.0))

    chunks, t, out, prev_scene = [np.zeros(int(LEAD * SR), np.float32)], LEAD, [], None
    for i, ln in enumerate(spec["lines"]):
        scene = ln.get("scene", str(i))
        if prev_scene is not None and scene != prev_scene:
            chunks.append(np.zeros(int(SCENE_GAP * SR), np.float32)); t += SCENE_GAP
        audio, sr = tts.create(ln["text"], voice=voice, speed=speed, lang=lang)
        if sr != SR:
            sys.exit(f"unexpected sample rate {sr}")
        d = len(audio) / SR
        cap = ln.get("caption") or ln["text"]
        for k, v in CAPTION_FIX.items():
            cap = cap.replace(k, v)
        out.append({"i": i, "scene": scene, "title": ln.get("title", ""), "text": ln["text"], "caption": cap,
                    "start": round(t, 3), "end": round(t + d, 3)})
        chunks += [audio.astype(np.float32), np.zeros(int(GAP * SR), np.float32)]
        t += d + GAP
        prev_scene = scene
    chunks.append(np.zeros(int(TAIL * SR), np.float32)); t += TAIL
    sf.write(os.path.join(a.out, "narration.wav"), np.concatenate(chunks), SR)
    json.dump({"total": round(t, 3), "lines": out}, open(os.path.join(a.out, "timeline.json"), "w"), indent=1)
    print(f"narration {t:.1f}s, {len(out)} lines -> {a.out}")


if __name__ == "__main__":
    main()
