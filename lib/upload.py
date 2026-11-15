"""Upload a media file to Google Drive through the n8n upload webhook and print the links as JSON.

Usage:
    python3 lib/upload.py <upload_webhook_url> <file> <lesson_id> [drive_file_name]

Prints: {"lesson_id", "fileId", "viewUrl", "imageUrl"} (exit code 1 on failure).
- viewUrl  -> link for videos ("Play animation")
- imageUrl -> inline <img> src for diagrams
"""
import json, os, subprocess, sys

url, path, lesson = sys.argv[1], sys.argv[2], sys.argv[3]
name = sys.argv[4] if len(sys.argv) > 4 else os.path.basename(path)
r = subprocess.run(["curl", "-sS", "--max-time", "300", "-X", "POST", url,
                    "-F", f"file=@{path}", "-F", f"filename={name}", "-F", f"lesson_id={lesson}"],
                   capture_output=True, text=True)
try:
    data = json.loads(r.stdout)
    if not data.get("fileId"):
        raise ValueError("no fileId")
except Exception:
    sys.stderr.write(f"upload failed (curl exit {r.returncode}): {r.stdout[:500]} {r.stderr[:500]}\n")
    sys.exit(1)
print(json.dumps(data))
