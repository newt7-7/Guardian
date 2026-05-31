#!/usr/bin/env python3
"""
Guardian People Finder — Find people and emails. No API keys needed.

Modes:
  linkedin  Find LinkedIn profiles matching a keyword
  emails    Find publicly listed emails for a domain
  full      Find people on LinkedIn + check for socials

Usage:
  python3 find-people.py linkedin "security engineer" --limit 20
  python3 find-people.py emails example.com
  python3 find-people.py full "data protection officer"
"""

import sys
import re
import time
from urllib.parse import quote_plus

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


def search_emails(domain, limit=20):
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
                        results.append({
                            "email": e,
                            "source": r.get("href", ""),
                            "context": r.get("title", ""),
                        })
                        print(f"  {e:40s} {r.get('title', '')[:50]}")

                time.sleep(0.3)

    except Exception as e:
        print(f"\n  Error: {e}")

    print(f"\n  Found {len(results)} email addresses")
    return results


def full_search(query, limit=15):
    profiles = search_linkedin(query, limit=limit)
    return profiles


if __name__ == "__main__":
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        sys.exit(1)

    mode = args[0]
    limit = 15
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
        search_emails(args[1], limit=limit)
    elif mode == "full" and len(args) >= 2:
        full_search(args[1], limit=limit)
    else:
        print(f"Usage: python3 find-people.py <mode> <query> [--limit N]")
        print("Modes: linkedin, emails, full")
