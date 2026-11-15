"""Build the lesson email (email-safe HTML: tables + inline styles) from a lesson JSON file.

Usage:
    python3 lib/build_email.py work/lesson.json work/email.html

Lesson JSON (type "lesson"):
{
  "type": "lesson",
  "lesson_id": "L001", "sequence": 1, "total": 290,
  "title": "...", "module": "...", "phase": "1 Foundations", "week": 1,
  "date_label": "Mon 16 Nov 2026",
  "concept": ["paragraph", "paragraph"],           # 2-4 short paragraphs
  "why_it_matters": "one or two sentences, on a gas facility like ours",
  "video": {"url": "https://www.youtube.com/watch?v=...", "title": "...", "channel": "...", "minutes": 9,
            "watch_for": ["...", "..."]} | null,
  "animation": {"url": "https://drive.google.com/file/d/.../view", "minutes": 3, "kind": "2D" | "3D",
                "note": "why it was generated / what it shows"} | null,
  "diagram": {"image_url": "https://lh3.googleusercontent.com/d/<id>", "view_url": "...", "caption": "..."} | null,
  "notes": ["key idea", ...],                      # 3-5
  "numbers": ["typical value with units", ...],    # optional
  "spot_it": "one thing to find on a P&ID / datasheet, or a question to ask the mentor",
  "reviews": [{"lesson_id": "L0xx", "title": "...", "q": "...", "a": "..."}],
  "mentor_prep": ["...", ...],                     # Fridays only (optional)
  "feedback_base": "https://n8n.abubells.com/webhook/track-lesson-feedback"
}

Saturday review (type "saturday"):
{
  "type": "saturday", "week": 1, "date_label": "Sat 21 Nov 2026",
  "summary": ["one line per lesson this week", ...],
  "quiz": [{"lesson_id": "L001", "title": "...", "q": "...", "a": "..."}],   # 6-10
  "reviews": [...],                                # due spaced reviews (optional)
  "next_week": "one line on what is coming",
  "feedback_base": "..."                           # unused for now
}
"""
import html, json, sys

BG, CARD, INK, MUTED, TEAL, ACCENT, LINE, TINT = "#EFEBE2", "#FBFAF6", "#1F2328", "#5B6670", "#12332F", "#E4572E", "#D9D4C7", "#EEF2F1"
FONT = "Arial,Helvetica,sans-serif"
RATINGS = [("got_it", "Got it"), ("review_again", "Review again"), ("too_basic", "Too basic"), ("bad_video", "Bad video")]


def e(s):
    return html.escape(str(s or ""), quote=True)


def p(text, size=15, color=INK, margin="0 0 12px"):
    return f'<p style="margin:{margin};font-family:{FONT};font-size:{size}px;line-height:1.55;color:{color}">{text}</p>'


def h(text):
    return (f'<p style="margin:22px 0 8px;font-family:{FONT};font-size:12px;letter-spacing:1px;text-transform:uppercase;'
            f'font-weight:bold;color:{TEAL}">{e(text)}</p>')


def ul(items):
    lis = "".join(f'<li style="margin:0 0 6px">{e(x)}</li>' for x in items)
    return f'<ul style="margin:0 0 12px;padding-left:20px;font-family:{FONT};font-size:15px;line-height:1.5;color:{INK}">{lis}</ul>'


def button(url, label, primary=True):
    bg, fg, bd = (TEAL, "#FFFFFF", TEAL) if primary else ("#FFFFFF", TEAL, TEAL)
    return (f'<a href="{e(url)}" style="display:inline-block;background:{bg};color:{fg};border:1px solid {bd};padding:10px 16px;'
            f'font-family:{FONT};font-size:14px;font-weight:bold;text-decoration:none;margin:0 6px 6px 0">{e(label)}</a>')


def box(inner, fill=TINT):
    return (f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:0 0 12px">'
            f'<tr><td style="background:{fill};padding:14px 16px;border-left:4px solid {TEAL}">{inner}</td></tr></table>')


def reviews_block(reviews, heading="Review"):
    if not reviews:
        return "", ""
    qs = "".join(p(f'<b>{i}.</b> {e(r["q"])} <span style="color:{MUTED}">({e(r["lesson_id"])}: {e(r["title"])})</span>', 15, INK, "0 0 8px")
                 for i, r in enumerate(reviews, 1))
    ans = "".join(p(f'<b>{i}.</b> {e(r["a"])}', 13, MUTED, "0 0 6px") for i, r in enumerate(reviews, 1))
    return h(heading) + p("Answer in your head first. Answers are at the bottom.", 13, MUTED) + qs, ans


def lesson_body(L):
    out = []
    out.append(p(f'{e(L.get("phase"))} &middot; Week {e(L.get("week"))} &middot; {e(L.get("module"))}', 13, MUTED, "0 0 4px"))
    out.append(f'<h1 style="margin:0 0 6px;font-family:{FONT};font-size:24px;line-height:1.25;color:{TEAL}">{e(L["title"])}</h1>')
    out.append(p(f'Lesson {e(L["sequence"])} of {e(L.get("total", 290))} &middot; {e(L["lesson_id"])} &middot; about 10 to 15 minutes', 13, MUTED, "0 0 16px"))
    out.append(h("The idea"))
    out += [p(e(x)) for x in L.get("concept", [])]
    if L.get("why_it_matters"):
        out.append(box(p(f'<b>Why it matters here.</b> {e(L["why_it_matters"])}', 15, INK, "0")))
    v = L.get("video")
    if v:
        out.append(h("Watch"))
        meta = " &middot; ".join(x for x in [e(v.get("channel")), f'{e(v.get("minutes"))} min' if v.get("minutes") else ""] if x)
        out.append(p(f'<a href="{e(v["url"])}" style="color:{TEAL};font-weight:bold">{e(v["title"])}</a><br>'
                     f'<span style="font-size:13px;color:{MUTED}">{meta}</span>'))
        if v.get("watch_for"):
            out.append(p("Watch for:", 14, MUTED, "0 0 4px")); out.append(ul(v["watch_for"]))
        out.append(button(v["url"], "Open on YouTube"))
    a = L.get("animation")
    if a:
        out.append(h(f'Narrated animation ({e(a.get("kind", ""))})'.replace(" ()", "")))
        if a.get("note"):
            out.append(p(e(a["note"])))
        out.append(button(a["url"], f'Play animation{" (" + str(a["minutes"]) + " min)" if a.get("minutes") else ""}', primary=not v))
    d = L.get("diagram")
    if d:
        out.append(h("Diagram"))
        img = (f'<a href="{e(d.get("view_url") or d["image_url"])}"><img src="{e(d["image_url"])}" width="568" alt="{e(d.get("caption") or L["title"])}" '
               f'style="display:block;width:100%;max-width:568px;height:auto;border:1px solid {LINE}"></a>')
        out.append(img)
        if d.get("caption"):
            out.append(p(e(d["caption"]), 13, MUTED, "6px 0 12px"))
        out.append(p(f'Image not showing? <a href="{e(d.get("view_url") or d["image_url"])}" style="color:{TEAL}">Open the diagram</a>.', 12, MUTED))
    out.append(h("Key ideas")); out.append(ul(L.get("notes", [])))
    if L.get("numbers"):
        out.append(h("Typical numbers")); out.append(ul(L["numbers"]))
    if L.get("spot_it"):
        out.append(h("Spot it")); out.append(box(p(e(L["spot_it"]), 15, INK, "0")))
    if L.get("mentor_prep"):
        out.append(h("Friday: mentor check-in prep")); out.append(ul(L["mentor_prep"]))
    rq, ans = reviews_block(L.get("reviews"))
    out.append(rq)
    fb = L.get("feedback_base")
    if fb:
        out.append(h("How was this lesson?"))
        out.append("".join(button(f'{fb}?lesson={L["lesson_id"]}&rating={k}', lab, primary=(k == "got_it")) for k, lab in RATINGS))
        out.append(p("Each button opens a short confirm page, so link scanners can't record a rating by accident.", 12, MUTED, "6px 0 0"))
    if ans:
        out.append(f'<hr style="border:0;border-top:1px solid {LINE};margin:24px 0 12px">')
        out.append(h("Review answers")); out.append(ans)
    return "".join(out)


def saturday_body(S):
    out = []
    out.append(p(f'Week {e(S.get("week"))} review &middot; {e(S.get("date_label"))}', 13, MUTED, "0 0 4px"))
    out.append(f'<h1 style="margin:0 0 12px;font-family:{FONT};font-size:24px;color:{TEAL}">This week in review</h1>')
    if S.get("summary"):
        out.append(h("What you covered")); out.append(ul(S["summary"]))
    quiz = S.get("quiz", [])
    out.append(h("Quiz")); out.append(p("Answer in your head or on paper first. Answers are at the bottom.", 13, MUTED))
    out += [p(f'<b>{i}.</b> {e(q["q"])} <span style="color:{MUTED}">({e(q["lesson_id"])})</span>', 15, INK, "0 0 8px")
            for i, q in enumerate(quiz, 1)]
    rq, rans = reviews_block(S.get("reviews"), "Spaced review")
    out.append(rq)
    if S.get("next_week"):
        out.append(h("Next week")); out.append(p(e(S["next_week"])))
    out.append(f'<hr style="border:0;border-top:1px solid {LINE};margin:24px 0 12px">')
    out.append(h("Quiz answers"))
    out += [p(f'<b>{i}.</b> {e(q["a"])}', 13, MUTED, "0 0 6px") for i, q in enumerate(quiz, 1)]
    if rans:
        out.append(h("Spaced review answers")); out.append(rans)
    return "".join(out)


def build(data):
    body = saturday_body(data) if data.get("type") == "saturday" else lesson_body(data)
    pre = e(data.get("preheader") or (data.get("concept") or [""])[0])[:140]
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:{BG}">
<div style="display:none;max-height:0;overflow:hidden">{pre}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{BG}"><tr><td align="center" style="padding:20px 10px">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" style="width:100%;max-width:600px;background:{CARD};border-top:5px solid {TEAL}">
<tr><td style="padding:22px 16px 6px 16px;font-family:{FONT};font-size:12px;letter-spacing:1px;text-transform:uppercase;color:{MUTED}">
Daily Track Lesson &middot; Mechanical, Piping, Rotating and HVAC &middot; {e(data.get("date_label"))}</td></tr>
<tr><td style="padding:6px 16px 24px 16px">{body}</td></tr>
</table>
<p style="font-family:{FONT};font-size:11px;color:{MUTED};margin:12px 0 0">Self-study companion to the SGTP. Generated automatically; diagrams and animations are schematic, not to scale.</p>
</td></tr></table></body></html>"""


if __name__ == "__main__":
    data = json.load(open(sys.argv[1]))
    open(sys.argv[2], "w").write(build(data))
    print("email ->", sys.argv[2])
