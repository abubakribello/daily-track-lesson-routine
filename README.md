# Daily Track Lesson routine

Instructions and renderers for a scheduled Claude task that emails one self-study lesson each weekday (Mechanical, Piping, Rotating and HVAC track) plus a Saturday review.

The scheduled task clones this repo, then follows [`SKILL.md`](SKILL.md). Change the behaviour here, not in the task.

| Path | What it does |
|---|---|
| `SKILL.md` | Step-by-step run procedure (lesson pick, spaced review, video verification, media, send, Airtable updates) |
| `setup.sh` | Installs dependencies, downloads the Kokoro voice, writes `work/capabilities.json` |
| `lib/style.py` | Palette and P&ID-style helpers for diagrams and 2D animation |
| `lib/narrate.py` | Narration script to `narration.wav` + `timeline.json` (Kokoro TTS, sentence-synced) |
| `lib/anim2d.py` | 2D narrated animation (matplotlib → ffmpeg) |
| `lib/stage3d.js`, `lib/render3d.js` | 3D narrated animation (three.js in headless Chromium → ffmpeg) |
| `lib/build_email.py` | Email-safe HTML from a lesson JSON |
| `lib/upload.py`, `lib/send.py` | n8n webhooks: upload media to Drive, send the email |
| `examples/` | Separator lesson in 2D and 3D, and a sample lesson JSON |

No secrets live here. Webhook URLs and the recipient come from the Airtable Settings table at run time.

Quick local check:

```bash
bash setup.sh
python3 lib/narrate.py examples/separator_2d/script.json work/sep2d
python3 examples/separator_2d/make.py work/sep2d out/sep2d 20
python3 lib/narrate.py examples/separator_3d/script.json work/sep3d
node lib/render3d.js examples/separator_3d/scene.html work/sep3d out/sep3d/animation.mp4 20 8
python3 lib/build_email.py examples/lesson.sample.json work/email.html
```
