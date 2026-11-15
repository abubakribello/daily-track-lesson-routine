"""Send the email through the n8n send webhook.

Usage:
    python3 lib/send.py <send_webhook_url> <to> <subject> <email.html>

Exit code 0 only when n8n answers with HTTP 2xx.
"""
import json, subprocess, sys

url, to, subject, path = sys.argv[1:5]
payload = json.dumps({"to": to, "subject": subject, "html": open(path).read()})
r = subprocess.run(["curl", "-sS", "--max-time", "120", "-o", "/dev/stderr", "-w", "%{http_code}", "-X", "POST", url,
                    "-H", "Content-Type: application/json", "--data-binary", "@-"],
                   input=payload, capture_output=True, text=True)
code = r.stdout.strip()
print(f"send webhook HTTP {code}")
if not code.startswith("2"):
    sys.stderr.write(r.stderr[:800] + "\n")
    sys.exit(1)
