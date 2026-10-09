#!/usr/bin/env python3
"""Validate key-projects.json before a typo can break the daily run or the site.

Offline checks always run. With --online it also confirms, via the GitHub API, that every
featured repo is public and that each `path` folder and `image` file exists in it.

    python3 .github/scripts/validate_config.py            # offline (used by the daily update)
    python3 .github/scripts/validate_config.py --online   # also hit the API (used on pull requests)

Exits 1 on errors; warnings never fail the run. Messages are GitHub Actions annotations.
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "key-projects.json"
API = "https://api.github.com"
FEATURED_KEYS = {"repo", "title", "tagline", "platform", "image", "path", "spotlight", "why"}
MAX_WHY = 200


def check_config(cfg):
    """Offline checks. Returns (errors, warnings)."""
    errors, warnings = [], []
    if not isinstance(cfg, dict):
        return ["key-projects.json must be a JSON object"], []

    if not isinstance(cfg.get("owner"), str) or not cfg["owner"].strip():
        errors.append("'owner' must be a non-empty string")

    tz = cfg.get("timezone", "America/New_York")
    try:
        ZoneInfo(tz)
    except Exception:
        errors.append(f"'timezone' {tz!r} is not a valid IANA timezone (e.g. America/New_York)")

    for key in ("exclude", "include_forks"):
        if key in cfg and not (isinstance(cfg[key], list) and all(isinstance(x, str) for x in cfg[key])):
            errors.append(f"'{key}' must be a list of repo names")

    for key, lo, hi in (("activity_weeks", 4, 26), ("activity_items", 1, 20)):
        if key in cfg and not (isinstance(cfg[key], int) and not isinstance(cfg[key], bool) and lo <= cfg[key] <= hi):
            errors.append(f"'{key}' must be a whole number from {lo} to {hi}")

    featured = cfg.get("featured")
    if not isinstance(featured, list) or not featured:
        errors.append("'featured' must be a non-empty list")
        return errors, warnings

    excluded = set(cfg.get("exclude", [])) if isinstance(cfg.get("exclude"), list) else set()
    seen, spotlights = set(), 0
    for i, f in enumerate(featured):
        if not isinstance(f, dict) or not isinstance(f.get("repo"), str) or not f["repo"].strip():
            errors.append(f"featured[{i}]: needs a 'repo' name")
            continue
        where = f"featured[{i}] ({f['repo']})"
        if f["repo"] in seen:
            errors.append(f"{where}: listed more than once")
        seen.add(f["repo"])
        if f["repo"] in excluded:
            errors.append(f"{where}: is also in 'exclude', so it would never appear")
        for key in f:
            if key not in FEATURED_KEYS:
                warnings.append(f"{where}: unknown key '{key}' (typo?)")
        for key in ("title", "tagline", "platform", "image", "path", "why"):
            if key in f and not (isinstance(f[key], str) and f[key].strip()):
                errors.append(f"{where}: '{key}' must be a non-empty string")
        if "spotlight" in f and not isinstance(f["spotlight"], bool):
            errors.append(f"{where}: 'spotlight' must be true or false")
        if f.get("spotlight") is True:
            spotlights += 1
            if not f.get("why"):
                errors.append(f"{where}: a spotlight project needs a 'why' line")
        if isinstance(f.get("why"), str) and len(f["why"]) > MAX_WHY:
            warnings.append(f"{where}: 'why' is {len(f['why'])} characters; over {MAX_WHY} it gets long on a card")
        if isinstance(f.get("path"), str) and (f["path"].startswith("/") or ".." in f["path"].split("/")):
            errors.append(f"{where}: 'path' must be a folder inside the repo, like 'spritemove'")
        if isinstance(f.get("image"), str) and f["image"].startswith(("http://", "https://")):
            errors.append(f"{where}: 'image' is a path inside the repo (like 'docs/shot.png'), not a URL")
    if spotlights == 0:
        warnings.append("No project has \"spotlight\": true, so the Spotlight section will be hidden")
    return errors, warnings


def api_get(path, token=None):
    """GET from the GitHub API. Returns (status, json_or_None); status 0 means no response."""
    req = urllib.request.Request(f"{API}{path}", headers={
        "Accept": "application/vnd.github+json", "User-Agent": "todddube-validate",
        **({"Authorization": f"Bearer {token}"} if token else {}),
    })
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        return e.code, None
    except Exception:
        return 0, None


def check_online(cfg, get=api_get):
    """Confirm featured repos are public and their folders/images exist. Returns (errors, warnings)."""
    errors, warnings = [], []
    owner = cfg["owner"]
    include_forks = set(cfg.get("include_forks", []))
    for f in cfg["featured"]:
        name = f["repo"]
        status, repo = get(f"/repos/{owner}/{name}")
        if status in (403, 429, 0):
            warnings.append(f"{name}: couldn't reach the GitHub API (status {status or 'none'}); online checks skipped")
            continue
        if status == 404 or repo is None:
            errors.append(f"{name}: no public repo {owner}/{name} (renamed, deleted or private?)")
            continue
        if repo.get("private"):
            errors.append(f"{name}: repo is private, so it can't be shown")
        if repo.get("archived"):
            errors.append(f"{name}: repo is archived, so the site skips it")
        if repo.get("fork") and name not in include_forks:
            errors.append(f"{name}: repo is a fork; add it to 'include_forks' to show it")
        branch = repo.get("default_branch", "main")
        for key in ("path", "image"):
            if f.get(key):
                ref = urllib.parse.quote(f[key])
                s, _ = get(f"/repos/{owner}/{name}/contents/{ref}?ref={urllib.parse.quote(branch)}")
                if s == 404:
                    errors.append(f"{name}: '{key}' {f[key]!r} doesn't exist on {branch}")
    return errors, warnings


def annotate(level, message):
    print(f"::{level} file=key-projects.json::{message}")


def main(argv):
    try:
        cfg = json.loads(CONFIG.read_text())
    except json.JSONDecodeError as e:
        annotate("error", f"key-projects.json is not valid JSON: {e}")
        return 1
    errors, warnings = check_config(cfg)
    if not errors and "--online" in argv:
        e2, w2 = check_online(cfg, lambda p: api_get(p, os.environ.get("GITHUB_TOKEN")))
        errors, warnings = errors + e2, warnings + w2
    for w in warnings:
        annotate("warning", w)
    for e in errors:
        annotate("error", e)
    n = len(cfg.get("featured", [])) if isinstance(cfg, dict) and isinstance(cfg.get("featured"), list) else 0
    print(f"key-projects.json: {n} featured, {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
