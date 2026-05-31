#!/usr/bin/env python3
"""
Guardian Email Server — Local web UI for sending emails to logged contacts.

Usage:
  python3 server.py                    # Serve on http://localhost:8000
  python3 server.py --port 9090        # Custom port
  python3 server.py --open             # Auto-open browser

Requires SMTP credentials set in environment:
  export SMTP_USER="your.email@gmail.com"
  export SMTP_PASSWORD="your_16_char_app_password"
"""

import os
import sys
import json
import re
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(TOOLS_DIR, "logs", "emails.json")

SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")


def load_contacts():
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE) as f:
        log = json.load(f)
    contacts = []
    for domain, entries in log.items():
        for e in entries:
            contacts.append(e)
    return contacts


def send_email(to_addr, subject, body):
    msg = MIMEMultipart()
    msg["From"] = SMTP_USER
    msg["To"] = to_addr
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(SMTP_USER, SMTP_PASSWORD)
    server.send_message(msg)
    server.quit()


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.path = "/email-composer.html"
        elif self.path == "/api/contacts":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            contacts = load_contacts()
            self.wfile.write(json.dumps({"contacts": contacts}).encode())
            return
        return super().do_GET()

    def do_POST(self):
        if self.path == "/api/send":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length).decode())
            to = body.get("to", "")
            subject = body.get("subject", "")
            message = body.get("body", "")
            dry_run = body.get("dry_run", False)

            if not to or not subject or not message:
                self._json(400, {"ok": False, "error": "Missing required fields"})
                return

            if dry_run:
                self._json(200, {"ok": True, "dry_run": True, "to": to})
                return

            if not SMTP_USER or not SMTP_PASSWORD:
                self._json(500, {"ok": False,
                    "error": "SMTP not configured. Set SMTP_USER and SMTP_PASSWORD env vars."})
                return

            try:
                send_email(to, subject, message)
                self._json(200, {"ok": True, "to": to})
            except Exception as e:
                self._json(500, {"ok": False, "error": str(e)})
            return

        self._json(404, {"ok": False, "error": "Not found"})

    def _json(self, status, data):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def log_message(self, format, *args):
        msg = format % args
        if "/api/" in msg:
            print(f"  {msg}")


if __name__ == "__main__":
    port = 8000
    open_browser = False

    for i, a in enumerate(sys.argv[1:]):
        if a == "--port" and i + 1 < len(sys.argv) - 1:
            port = int(sys.argv[i + 2])
        if a == "--open":
            open_browser = True

    os.chdir(TOOLS_DIR)
    server = HTTPServer(("", port), Handler)

    url = f"http://localhost:{port}"
    print(f"\n  Guardian Email Composer")
    print(f"  ─────────────────────")
    print(f"  Server: {url}")
    if not SMTP_USER:
        print(f"  ⚠  SMTP not configured. Set SMTP_USER and SMTP_PASSWORD to send.")
    else:
        print(f"  Sending as: {SMTP_USER}")
    print(f"  Quit: Ctrl+C\n")

    if open_browser:
        webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Shutting down.")
        server.server_close()
