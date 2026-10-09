#!/usr/bin/env python3
"""Daily health check for www.thedubes.com.

Fails (so GitHub emails you) when:
  - the site is down,
  - the live projects.json is older than 48 hours (the daily update has silently stopped), or
  - a project's repo link or screenshot no longer loads (renamed, made private, file moved).
Dead release or homepage links only warn.
"""
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

SITE = "https://www.thedubes.com"
MAX_AGE_HOURS = 48
HEADERS = {"User-Agent": "todddube-health-check"}


def http_status(url, method="HEAD", timeout=15):
    req = urllib.request.Request(url, method=method, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return 0


def probe(url, status_fn=http_status, sleep=time.sleep):
    """HEAD first, then GET (some hosts reject HEAD), retrying once on a network error or 5xx."""
    status = 0
    for attempt in range(2):
        status = status_fn(url, "HEAD")
        if status != 200:
            status = status_fn(url, "GET")
        if status == 200 or (0 < status < 500):
            return status
        if attempt == 0:
            sleep(2)
    return status


def check(data, status_fn=http_status, now=None, sleep=time.sleep):
    """Returns (errors, warnings) for a parsed projects.json."""
    errors, warnings = [], []
    now = now or datetime.now(timezone.utc)
    age_h = (now - datetime.fromisoformat(data["generated_at"])).total_seconds() / 3600
    if age_h > MAX_AGE_HOURS:
        errors.append(
            f"The live projects.json is {age_h:.0f} hours old (limit {MAX_AGE_HOURS}). "
            "The daily 'Update Projects' workflow has stopped producing fresh data; check the Actions tab."
        )
    todo, seen = [], set()
    for p in data["featured"] + data["others"]:
        entries = [(f"{p['name']} repo link", p["url"], errors)]
        if p.get("image"):
            entries.append((f"{p['name']} screenshot", p["image"], errors))
        if p.get("release"):
            entries.append((f"{p['name']} release link", p["release"]["url"], warnings))
        if p.get("homepage"):
            entries.append((f"{p['name']} homepage", p["homepage"], warnings))
        for label, url, bucket in entries:
            if url not in seen:
                seen.add(url)
                todo.append((label, url, bucket))
    for label, url, bucket in todo:
        status = probe(url, status_fn, sleep)
        if status != 200:
            bucket.append(f"{label} returned {status or 'no response'}: {url}")
    return errors, warnings


def main():
    root_status = probe(SITE + "/")
    errors = [] if root_status == 200 else [f"{SITE}/ returned {root_status or 'no response'}"]
    try:
        req = urllib.request.Request(f"{SITE}/projects.json?cb={int(time.time())}", headers=HEADERS)
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.load(r)
    except Exception as e:
        errors.append(f"Couldn't read {SITE}/projects.json: {e}")
        data = None
    warnings = []
    if data:
        e2, warnings = check(data)
        errors += e2
    for w in warnings:
        print(f"::warning::{w}")
    for e in errors:
        print(f"::error::{e}")
    total = len(data["featured"]) + len(data["others"]) if data else 0
    print(f"Checked {SITE}: {total} projects, {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
