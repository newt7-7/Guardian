#!/usr/bin/env python3
"""
Guardian People Finder — Find people and emails. No API keys needed.

Modes:
  linkedin  Find LinkedIn profiles matching a keyword
  emails    Find publicly listed emails for a domain
  full      Find people on LinkedIn + check for socials

Usage:
  python3 find-people.py linkedin "security engineer" --limit 20
  python3 find-people.py emails example.com --export
  python3 find-people.py emails example.com --limit 50
"""

import sys
import re
import time
import json
import os
from datetime import datetime

try:
    from ddgs import DDGS
except ImportError:
    print("Missing library. Run: pip3 install ddgs")
    sys.exit(1)

SOCIAL_PATTERNS = {
    "Twitter/X": r"(?:twitter\.com|x\.com)/([A-Za-z0-9_]+)",
    "GitHub": r"github\.com/([A-Za-z0-9_-]+)",
    "YouTube": r"youtube\.com/@([A-Za-z0-9_-]+)",
    "Bluesky": r"bsky\.app/profile/([A-Za-z0-9.]+)",
}

EMAIL_PATTERN = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")


def ensure_log_dir():
    os.makedirs(LOG_DIR, exist_ok=True)


def load_log():
    path = os.path.join(LOG_DIR, "emails.json")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}


def save_log(data):
    ensure_log_dir()
    path = os.path.join(LOG_DIR, "emails.json")
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"\n  Saved to {path}")


def find_socials(text):
    found = {}
    for name, pattern in SOCIAL_PATTERNS.items():
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            found[name] = [f"{name.split('/')[0]}/{m}" for m in matches]
    return found


def search_linkedin(query, limit=15):
    dork = f'site:linkedin.com/in "{query}"'
    results = []
    seen = set()

    print(f"\n  Searching LinkedIn for: \"{query}\"\n")
    print(f"  {'Name':35s} {'Link'}")
    print(f"  {'-'*35} {'-'*60}")

    try:
        with DDGS() as ddgs:
            for i, r in enumerate(ddgs.text(dork)):
                if i >= limit:
                    break
                link = r.get("href", "")
                title = r.get("title", "")
                body = r.get("body", "")

                if not link or link in seen or not re.search(r"linkedin\.com/in/", link):
                    continue
                seen.add(link)

                name = re.sub(r"\s*[-|].*$", "", title).strip() or title[:40]
                socials = find_socials(body + " " + title)
                results.append({"name": name, "link": link, "socials": socials})

                social_str = ", ".join([f"{s}({','.join(u)})" for s, u in socials.items()]) if socials else ""
                print(f"  {name[:33]:35s} {link}")
                if social_str:
                    print(f"  {'':35s} socials: {social_str}")

                time.sleep(0.3)
    except Exception as e:
        print(f"\n  Error: {e}")

    print(f"\n  Found {len(results)} profiles")
    return results


def search_emails(domain, limit=20, export=False):
    dork = f'site:{domain} "{domain}" email OR contact'
    found_emails = set()
    results = []

    print(f"\n  Searching for emails at: {domain}\n")

    try:
        with DDGS() as ddgs:
            for i, r in enumerate(ddgs.text(dork)):
                if i >= limit:
                    break
                body = r.get("body", "") + " " + r.get("title", "")
                emails = re.findall(EMAIL_PATTERN, body)

                for e in emails:
                    if e.endswith(domain) and e not in found_emails:
                        found_emails.add(e)
                        entry = {
                            "email": e,
                            "source": r.get("href", ""),
                            "context": r.get("title", ""),
                            "found_at": datetime.now().isoformat(),
                        }
                        results.append(entry)
                        print(f"  {e:40s} {r.get('title', '')[:50]}")

                time.sleep(0.3)
    except Exception as e:
        print(f"\n  Error: {e}")

    print(f"\n  Found {len(results)} email addresses")

    if export and results:
        log = load_log()
        if domain not in log:
            log[domain] = []
        existing = {e["email"] for e in log[domain]}
        new_count = 0
        for e in results:
            if e["email"] not in existing:
                log[domain].append(e)
                new_count += 1
        save_log(log)
        print(f"  ({new_count} new, {len(log[domain])} total for {domain})")

    return results


def list_log():
    log = load_log()
    if not log:
        print("\n  No emails logged yet.")
        return
    total = 0
    print(f"\n  {'Domain':25s} {'Count':6s} {'Last found'}")
    print(f"  {'-'*25} {'-'*6} {'-'*20}")
    for domain, entries in sorted(log.items()):
        total += len(entries)
        last = entries[-1]["found_at"][:10] if entries else "—"
        print(f"  {domain:25s} {len(entries):6d}  {last}")
    print(f"\n  Total: {total} emails across {len(log)} domains")


if __name__ == "__main__":
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        sys.exit(1)

    if args[0] == "list":
        list_log()
        sys.exit(0)

    mode = args[0]
    limit = 20
    export = "--export" in args

    if "--limit" in args:
        idx = args.index("--limit")
        if idx + 1 < len(args):
            try:
                limit = int(args[idx + 1])
            except ValueError:
                pass

    if mode == "linkedin" and len(args) >= 2:
        search_linkedin(args[1], limit=limit)
    elif mode == "emails" and len(args) >= 2:
        search_emails(args[1], limit=limit, export=export)
    elif mode == "full" and len(args) >= 2:
        search_linkedin(args[1], limit=limit)
    else:
        print(f"Usage: python3 find-people.py <mode> <query> [--limit N] [--export]")
        print("Modes: linkedin, emails, full, list")
