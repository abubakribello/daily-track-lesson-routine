#!/usr/bin/env bash
# Install everything the lesson run needs and report what works.
# Usage: bash setup.sh            (install + quick capability check)
# Writes work/capabilities.json: {"diagram": bool, "tts": bool, "anim2d": bool, "anim3d": bool, "notes": [...]}
set -u
cd "$(dirname "$0")"
mkdir -p work voices
NOTES=()
log() { echo "[setup] $*"; }

# ---- Python packages ----
PIP="pip install -q --disable-pip-version-check"
python3 -c "import matplotlib, numpy" 2>/dev/null || $PIP matplotlib numpy 2>/dev/null || $PIP --break-system-packages matplotlib numpy
python3 -c "import kokoro_onnx, soundfile" 2>/dev/null || $PIP kokoro-onnx soundfile 2>/dev/null || $PIP --break-system-packages kokoro-onnx soundfile || NOTES+=("pip install kokoro-onnx failed")

# ---- Kokoro voice files (GitHub release; Hugging Face is blocked) ----
REL=https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0
for f in kokoro-v1.0.int8.onnx voices-v1.0.bin; do
  if [ ! -s "voices/$f" ]; then
    log "downloading $f"
    curl -sSL --retry 3 --max-time 600 -o "voices/$f" "$REL/$f" || { NOTES+=("download $f failed"); rm -f "voices/$f"; }
  fi
done

# ---- Node: three.js (+ Playwright if missing) ----
if [ ! -d node_modules/three ]; then npm install --silent --no-audit --no-fund >/dev/null 2>&1 || NOTES+=("npm install three failed"); fi
node -e "require('playwright')" 2>/dev/null || {
  log "playwright missing, installing"
  npm install --silent --no-audit --no-fund playwright >/dev/null 2>&1 && npx playwright install chromium >/dev/null 2>&1 || NOTES+=("playwright install failed")
}

command -v ffmpeg >/dev/null || NOTES+=("ffmpeg missing")

# ---- capability checks ----
DIAGRAM=false; TTS=false; A2D=false; A3D=false
python3 - <<'PY' && DIAGRAM=true
import sys; sys.path.insert(0, "lib")
from style import *
fig, ax = new_diagram("setup check", xlim=(0, 4), ylim=(0, 2)); valve(ax, 2, 1); save_diagram(fig, "work/_check.png")
PY
cat > work/_check_script.json <<'J'
{"lines":[{"scene":"a","title":"Check","text":"Setup check."}]}
J
python3 lib/narrate.py work/_check_script.json work/_check >/dev/null 2>&1 && TTS=true
if $TTS && command -v ffmpeg >/dev/null; then
  python3 - <<'PY' >/dev/null 2>&1 && A2D=true
import sys; sys.path.insert(0, "lib")
from style import *
from anim2d import Anim2D
A = Anim2D("work/_check/timeline.json", "work/_check/narration.wav", "work/_check/a2d.mp4", xlim=(0, 4), ylim=(0, 2), max_seconds=1)
A.run(lambda t, line: None)
PY
  cat > work/_check3d.html <<'H'
<!doctype html><html><head><meta charset="utf-8"><script type="importmap">{"imports":{"three":"/node_modules/three/build/three.module.js"}}</script></head><body>
<script type="module">
import * as THREE from "three"; import { createStage, C } from "/lib/stage3d.js";
const S = createStage({ title: "check" }); S.box([1, 1, 1], [0, 0, 0], C.oil); S.cam("a", [3, 2, 4], [0, 0, 0]); S.start();
</script></body></html>
H
  timeout 180 node lib/render3d.js work/_check3d.html work/_check work/_check/a3d.mp4 10 1 >/dev/null 2>&1 && [ -s work/_check/a3d.mp4 ] && A3D=true
fi
$DIAGRAM || NOTES+=("diagram check failed")
$TTS || NOTES+=("tts check failed")
python3 - "$DIAGRAM" "$TTS" "$A2D" "$A3D" "${NOTES[@]+"${NOTES[@]}"}" <<'PY'
import json, sys
b = lambda s: s == "true"
caps = {"diagram": b(sys.argv[1]), "tts": b(sys.argv[2]), "anim2d": b(sys.argv[3]), "anim3d": b(sys.argv[4]), "notes": sys.argv[5:]}
json.dump(caps, open("work/capabilities.json", "w"))
print("[setup] capabilities:", json.dumps(caps))
PY
