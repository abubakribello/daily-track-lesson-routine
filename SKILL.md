# Daily Track Lesson: run procedure

You send Abu one lesson each weekday morning from his Mechanical, Piping, Rotating and HVAC self-study syllabus, plus a review quiz on Saturdays. Abu is a graduate trainee engineer on a gas-condensate development (offshore wellhead platforms, export pipeline, onshore central processing facility). He reads the email on his phone during his commute, so it must be short, accurate and easy to scan.

Follow these steps in order. Do not skip the checks. Never invent a video link, a standard clause or a number you are not confident of.

## Fixed references

Airtable base **Daily Track Lesson** `appfdTizk5GEd1gL4` (use the Airtable connector).

| Table | ID |
|---|---|
| Lessons | `tblZlG5ysHwcMOdN9` |
| Runs | `tblgNBpvc01uD7qEq` |
| Video Blocklist | `tblnPBRGwqz7VJMMY` |
| Settings | `tblwWUDR018fYH41z` (fields `Setting`, `Value`) |

Lessons fields: `Lesson ID`, `Sequence`, `Title`, `Phase`, `Week`, `Module`, `Planned Day`, `Planned Date`, `Visual Style` (2D/3D), `Custom Visual` (checkbox), `Status` (Not sent / Sent / Skipped), `Sent Date`, `YouTube URL`, `YouTube Title`, `YouTube Channel`, `Generated Media` (None / 2D / 3D), `Generation Reason` (No suitable video / Video misses key idea / Custom visual / Re-sent after bad video), `Generated Media URL`, `Diagram URL`, `Key Points`, `Recall Questions`, `Review Stage` (0–4), `Next Review Date`, `Rating`, `Rating Date`, `Notes`.

Runs fields: `Run` (text, e.g. `2026-11-16 L001`), `Run Time`, `Run Type` (Lesson / Saturday review / Test), `Lesson ID`, `Status` (Sent / Sent without media / Failed / Skipped (paused)), `Video Source`, `Render Minutes`, `Error`, `Notes`.

Video Blocklist fields: `Video URL`, `Video Title`, `Reason`, `Lesson ID`, `Date Added`.

Time zone: Africa/Lagos for every date. "Today" means today in Lagos.

## Step 0: Set up

1. `cd` into this repo and run `bash setup.sh`. It installs the tools, downloads the voice model and writes `work/capabilities.json` with `diagram`, `tts`, `anim2d`, `anim3d` (true/false). Read it.
2. Note the start time. Use `work/<lesson_id>/` for all scratch files.

## Step 1: Read Settings

List every row in Settings and build a dict `Setting -> Value`. Keys used:

| Setting | Meaning |
|---|---|
| Paused | `yes` = do nothing except log a Skipped (paused) run |
| Saturday review | `on` / `off` |
| YouTube max minutes | longest video to send (default 15) |
| Generated video target minutes | e.g. `2-4` |
| Generate animations | `on` / `off` (missing = off) |
| Recipient | email address to send to |
| Send webhook URL | n8n webhook that sends the email |
| Upload webhook URL | n8n webhook that uploads media to Google Drive |
| Feedback base URL | base URL for the rating buttons |

If `Recipient`, `Send webhook URL` or `Upload webhook URL` is missing, log a Failed run with the reason and stop.

## Step 2: Decide the run type

- If the trigger text contains `TEST`: this is a **Test** run. Do the full lesson flow for the next lesson, prefix the subject with `[TEST] `, and do **not** change any Lessons rows. Only write the Runs row (Run Type = Test).
- Otherwise, by today's weekday: Monday to Friday is a **Lesson** run. Saturday is a **Saturday review** run if `Saturday review = on`, otherwise stop. Sunday: stop.
- If `Paused = yes` (and not a test): write a Runs row with Status `Skipped (paused)` and stop.
- If a Runs row already exists for today with Status Sent and Run Type Lesson or Saturday review (and this is not a test), stop. This prevents double sends.

## Step 3: Pick the lesson (Lesson and Test runs)

1. The next lesson is the record with the lowest `Sequence` where `Status = Not sent`. Missed days never skip lessons.
2. Also read the last five sent lessons (Status = Sent, highest Sent Date) for continuity and to check ratings:
   - The most recent one rated **Too basic**: go one level deeper today (more numbers, design detail, failure modes) and say so in one line.
   - Today is **Friday** if the Lagos weekday is Friday: add the mentor check-in prep section.

## Step 4: Due reviews

1. Find lessons with `Status = Sent` and `Next Review Date` on or before today. Lessons rated **Review again** come first, then the oldest Next Review Date. Take at most 3.
2. For each, take one question from its `Recall Questions` JSON (`[{"q": "...", "a": "..."}]`). Use question index = `Review Stage` mod the number of questions, so each review asks something different.
3. Remember them; you update their review state in Step 11.

Review schedule: on send, `Review Stage = 0` and `Next Review Date = send date + 1 day`. After each review, `Review Stage += 1` and the next date is today + 3, 7 or 21 days for stages 1, 2 and 3. After the review at stage 3 (making it 4), clear `Next Review Date`. A lesson rated Review again (Rating Date after its last review) goes back to stage 1 with Next Review Date = today + 1 day, and its Rating is cleared.

## Step 5: Write the lesson

Write accurate, practical content for the lesson `Title` in the context of its `Module` and `Phase`:

- **concept**: 2 to 4 short paragraphs. Plain British English, short sentences, no filler, no marketing tone. Define every term on first use.
- **why_it_matters**: 1 to 2 sentences tied to a gas-condensate facility like Abu's (platforms, pipeline, CPF).
- **notes**: 3 to 5 key ideas, one line each.
- **numbers**: 0 to 4 typical values with units, only where you are confident. Use SI and the oilfield units engineers actually use on such projects (bar(g), °C, mm, inches for pipe size, MMscfd, bbl/d).
- **spot_it**: one thing to find on a P&ID, datasheet, layout or in the field, or a sharp question to ask the mentor.
- **mentor_prep** (Fridays only): 2 to 3 questions for the weekly mentor check-in drawn from this week's lessons.
- **recall questions** for the future: 3 question/answer pairs, each answerable in one sentence. Save them in Step 11.

Name codes and standards (ASME B31.3, ASME VIII, API 520/521, API 610, API 617, ISO 13623, DNV-ST-F101 and so on) only where they genuinely apply, and never quote a clause number you are not sure of.

## Step 6: Find and verify one YouTube video

1. Search the web for a video that teaches today's idea well. Prefer animation-led engineering teaching channels and equipment manufacturers. Search terms: the lesson title plus "animation", "how it works", "explained".
2. Verify every candidate before using it:
   - Fetch `https://www.youtube.com/oembed?url=<watch URL>&format=json`. It must return a title and author. If it fails, the video does not exist or is private: discard it.
   - Find its length (from the search result or the watch page). It must be at most `YouTube max minutes`.
   - It must be on topic for today's lesson, judged from its title and description.
   - It must not appear in Video Blocklist (`Video URL`) and must not already be used by another lesson (`YouTube URL` in Lessons).
3. Use the plain watch URL `https://www.youtube.com/watch?v=<id>` so it opens the YouTube app on a phone.
4. Write 2 to 3 short "watch for" points.
5. If nothing passes, use no video. Never send an unverified link.

Decide whether the chosen video covers the lesson's key idea. If it clearly misses or muddles it, note `Video misses key idea`.

## Step 7: Decide on a generated animation

Generate an animation only if `Generate animations = on`, `capabilities.json` allows the style, and at least one of these is true:

- no video passed Step 6 (reason `No suitable video`);
- the video misses the key idea (reason `Video misses key idea`);
- `Custom Visual` is checked (reason `Custom visual`).

Style: the lesson's `Visual Style` (2D or 3D). If that style's capability is false, use the other one if it can show the idea, otherwise skip. Do not attempt detailed machine internals (impellers, seals, gearboxes) in 3D; use 2D or skip.

## Step 8: Diagram (every lesson)

1. Write `work/<id>/diagram.py` using `lib/style.py` (`new_diagram`, `vessel_h`, `vessel_v`, `pipe`, `valve`, `instrument`, `signal`, `label`, `callout`, `fill_clipped`). See `examples/separator_2d/make.py`. Keep to one clear idea. It is a schematic, so say "Schematic, not to scale" where relevant.
2. Render to `work/<id>/diagram.png` and **open the PNG and look at it**. Check: nothing clipped at the edges, no overlapping labels, labels on or next to what they name, the physics and flow directions correct, readable on a phone. Fix and re-render up to three times.
3. Upload: `python3 lib/upload.py "<Upload webhook URL>" work/<id>/diagram.png <id> "<id> diagram.png"`. Use `imageUrl` as the `<img>` source and `viewUrl` as the fallback link.

If the diagram fails after three attempts, send without it and record that in the run Notes.

## Step 9: Animation (only if Step 7 says so)

Target length: `Generated video target minutes`. Longer is fine when the idea needs it.

1. Write `work/<id>/script.json` (format in `lib/narrate.py`): 8 to 25 sentences grouped into scenes, each scene showing one thing. Write for the ear: short sentences, no symbols ("P and I D" in `text`, "P&ID" in `caption`).
2. `python3 lib/narrate.py work/<id>/script.json work/<id>`
3. Render:
   - **2D**: write `work/<id>/anim.py` using `lib/anim2d.py` (`Anim2D`, highlight boxes per scene, `Particles` for flows). Model it on `examples/separator_2d/make.py`. Run it so it writes `work/<id>/animation.mp4`.
   - **3D**: write `work/<id>/scene.html` using `lib/stage3d.js` (camera per scene with `S.cam`, labels with `S.label`, flows with `S.flow`, cut-aways with clipping planes). Model it on `examples/separator_3d/scene.html`. Render with `node lib/render3d.js work/<id>/scene.html work/<id> work/<id>/animation.mp4 20`.
   - Test first with a short render (2D: `max_seconds=10`; 3D: last argument `8`) and look at the check frames before the full render.
4. Look at the check frames from the full render (`check2d_*.png` or `check3d_*.jpg`). Fix obvious problems: labels off screen or overlapping, camera inside geometry, captions out of sync.
5. Upload: `python3 lib/upload.py "<Upload webhook URL>" work/<id>/animation.mp4 <id> "<id> <title>.mp4"`. Use `viewUrl`.

If the animation fails, skip it and send the lesson anyway (run Status `Sent without media`).

## Step 10: Build and send the email

1. Write `work/<id>/lesson.json` in the format documented at the top of `lib/build_email.py` (type `lesson`). Set `feedback_base` to `Feedback base URL`, `date_label` like `Mon 16 Nov 2026`, `total` to the number of Lessons rows (290 unless changed).
2. `python3 lib/build_email.py work/<id>/lesson.json work/<id>/email.html`
3. Subject: `Lesson <Sequence>: <Title>` (prefix `[TEST] ` on test runs). Saturday: `Week <n> review`.
4. `python3 lib/send.py "<Send webhook URL>" "<Recipient>" "<subject>" work/<id>/email.html`
5. If sending fails, retry once after 30 seconds. If it still fails, write a Failed Runs row with the error and stop without changing Lessons.

## Step 11: Update Airtable (after a successful send, not on test runs)

Today's lesson:
- `Status` = Sent, `Sent Date` = today
- `YouTube URL`, `YouTube Title`, `YouTube Channel` (blank if none)
- `Generated Media` = None / 2D / 3D, `Generation Reason` (if generated), `Generated Media URL`
- `Diagram URL` = viewUrl
- `Key Points` = the notes, one per line
- `Recall Questions` = JSON array of 3 `{"q","a"}`
- `Review Stage` = 0, `Next Review Date` = tomorrow

Each reviewed lesson: update `Review Stage` and `Next Review Date` per the schedule in Step 4 (and clear `Rating` if it was Review again).

## Step 12: Log the run (always, including tests and failures)

Create one Runs row: `Run` = `<YYYY-MM-DD> <Lesson ID or "Week n review">`, `Run Time` = now, `Run Type`, `Lesson ID`, `Status`, `Video Source` (channel name, or "Generated", or "None"), `Render Minutes` (total minutes spent on diagram + animation), `Error` (if any), `Notes` (anything Abu should know, e.g. "no suitable video found", "diagram fixed after 2 attempts").

Finish with a two-line summary: what was sent and anything that failed.

## Saturday review run

1. Collect this week's sent lessons (Sent Date Monday to Friday of this week).
2. Write `summary` (one line per lesson), a `quiz` of 6 to 10 questions mixing their Recall Questions with new questions that connect the lessons, and `next_week` (one line from the next five Not sent lessons).
3. Add due spaced reviews (Step 4) as `reviews`.
4. Bad video follow-up: for any lesson this week rated **Bad video**, find a replacement video (Step 6 rules; the bad one is already blocklisted). If none, and animations are allowed, generate one (reason `Re-sent after bad video`). Add a short "Replacement for L0xx" item to the summary with the link, and update that lesson's video or generated media fields.
5. Build with type `saturday` in `lib/build_email.py`, send, update review states, log the run (Run Type Saturday review).

## Quality bar

- Accuracy first. If unsure about a value, leave it out.
- One idea per lesson, taught well. 10 to 15 minutes total for Abu, including the video.
- Every link verified. Every image looked at before sending.
- No LaTeX, no emoji, no hype.
