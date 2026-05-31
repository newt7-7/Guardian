#!/usr/bin/env python3
"""
Guardian Email Sender — Send emails to contacts found by find-people.py.

Uses Gmail SMTP. You need a Gmail app password (NOT your regular password).

Setup:
  1. Enable 2-factor authentication on your Google account
  2. Go to https://myaccount.google.com/apppasswords
  3. Generate an app password for "Mail"
  4. Set it below or as env var: export SMTP_PASSWORD="your_app_password"

Usage:
  python3 send-email.py list                              # Show logged contacts
  python3 send-email.py send example.com                  # Send to all contacts at a domain
  python3 send-email.py send example.com --subject "..."   # Custom subject
  python3 send-email.py send all                           # Send to ALL logged contacts
"""

import sys
import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SMTP_USER = os.environ.get("SMTP_USER", "YOUR_EMAIL@gmail.com")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "YOUR_APP_PASSWORD")
LOG_FILE = os.path.join(os.path.dirname(__file__), "logs", "emails.json")

DEFAULT_SUBJECT = "Introduction — Guardian Data Protection Services"
DEFAULT_BODY = """Hi {name},

I came across your profile and wanted to reach out regarding data protection and cybersecurity services.

At Guardian, we specialize in helping organizations prevent data leaks, respond to security incidents, and maintain compliance with regulations like GDPR and HIPAA.

I'd love to connect and explore how we might be able to help your organization strengthen its security posture.

Would you be open to a brief call sometime this week?

Best regards,
{from_name}
Guardian Security Team
{from_email}
"""


def load_contacts():
    if not os.path.exists(LOG_FILE):
        print("No contacts found. Run find-people.py emails <domain> --export first.")
        return {}
    with open(LOG_FILE) as f:
        return json.load(f)


def list_contacts():
    log = load_contacts()
    if not log:
        print("No contacts logged.")
        return

    total = 0
    for domain, entries in sorted(log.items()):
        print(f"\n{domain}:")
        for e in entries:
            print(f"  {e['email']:40s} {e.get('context', '')[:40]}")
            total += 1
    print(f"\nTotal: {total} contacts")


def send_email(to_addr, subject, body, from_name="Ian"):
    msg = MIMEMultipart()
    msg["From"] = f"{from_name} <{SMTP_USER}>"
    msg["To"] = to_addr
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"  FAILED: {e}")
        return False


def send_to_domain(domain, subject, body, dry_run=False, from_name="Ian"):
    log = load_contacts()
    entries = []
    if domain == "all":
        for d_entries in log.values():
            entries.extend(d_entries)
    elif domain in log:
        entries = log[domain]
    else:
        print(f"No contacts found for domain: {domain}")
        return

    name_guesses = {}
    for e in entries:
        local = e["email"].split("@")[0]
        parts = re.split(r"[._-]", local)
        name = " ".join(p.capitalize() for p in parts[:2])
        name_guesses[e["email"]] = name

    print(f"\nSending to {len(entries)} contact(s)...\n")

    for i, e in enumerate(entries, 1):
        name = name_guesses.get(e["email"], "there")
        personalized_body = body.replace("{name}", name).replace(
            "{from_name}", from_name
        ).replace("{from_email}", SMTP_USER)

        print(f"  [{i}/{len(entries)}] {e['email']} ({name})")

        if not dry_run:
            ok = send_email(e["email"], subject, personalized_body, from_name)
            print(f"    {'✓ Sent' if ok else '✗ Failed'}")
        else:
            print(f"    (dry run, skipped)")

    print(f"\nDone. Sent to {len(entries)} contact(s).")


if __name__ == "__main__":
    import re

    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help", "help"):
        print(__doc__)
        sys.exit(0)

    if args[0] == "list":
        list_contacts()
        sys.exit(0)

    if args[0] == "send" and len(args) >= 2:
        target = args[2] if len(args) > 2 else ""
        domain = target
        subject = DEFAULT_SUBJECT
        body = DEFAULT_BODY
        dry_run = "--dry-run" in args
        from_name = "Ian"

        for i, a in enumerate(args):
            if a == "--subject" and i + 1 < len(args):
                subject = args[i + 1]
            if a == "--body" and i + 1 < len(args):
                body = args[i + 1]
            if a == "--from" and i + 1 < len(args):
                from_name = args[i + 1]

        send_to_domain(domain, subject, body, dry_run, from_name)
    else:
        print("Usage: python3 send-email.py send <domain|all> [--subject \"...\"] [--dry-run]")
