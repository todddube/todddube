#!/usr/bin/env python3
"""Build projects.json and refresh the README project sections from GitHub.

Reads curation from key-projects.json, pulls live data for every public repo
(recent commits, weekly activity, latest release, whether it's built with
Claude Code), then writes:
  - projects.json            consumed by index.html (www.thedubes.com)
  - README.md                sections between <!-- NAME:START/END --> markers

Run locally with:  GITHUB_TOKEN=$(gh auth token) python3 .github/scripts/update_projects.py
"""
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

ROOT = Path(__file__).resolve().parents[2]
API = "https://api.github.com"
NOW = datetime.now(timezone.utc)

session = requests.Session()
session.headers["Accept"] = "application/vnd.github+json"
if os.environ.get("GITHUB_TOKEN"):
    session.headers["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
# Retry transient GitHub errors so one blip doesn't fail the whole daily run
session.mount("https://", HTTPAdapter(max_retries=Retry(
    total=4, backoff_factor=2, status_forcelist=(500, 502, 503, 504), allowed_methods=("GET",),
)))


def get(path, **params):
    """GET an API path; returns parsed JSON, or None on 404/409 (empty repo)."""
    r = session.get(f"{API}{path}", params=params, timeout=20)
    if r.status_code in (404, 409):
        return None
    r.raise_for_status()
    return r.json()


def all_repos(owner):
    """Every public repo for the owner, following pagination."""
    repos, page = [], 1
    while True:
        batch = get(f"/users/{owner}/repos", type="owner", per_page=100, page=page) or []
        repos += batch
        if len(batch) < 100:
            return repos
        page += 1


def parse_date(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def is_bot(commit):
    login = (commit.get("author") or {}).get("login") or ""
    return login.endswith("[bot]")


def recent_commits(repo, branch, since):
    commits, page = [], 1
    while page <= 5:
        batch = get(f"/repos/{repo}/commits", sha=branch, since=since.isoformat(), per_page=100, page=page)
        if not batch:
            break
        commits += batch
        if len(batch) < 100:
            break
        page += 1
    return commits


def status_for(days):
    if days <= 30:
        return "active"
    if days <= 120:
        return "recent"
    return "quiet"


def build_project(r, cfg, curation):
    full = r["full_name"]
    branch = r["default_branch"]
    weeks = cfg.get("activity_weeks", 12)
    since = NOW - timedelta(weeks=weeks)

    commits = recent_commits(full, branch, since)
    human = [c for c in commits if not is_bot(c)]
    latest = commits[0] if commits else ((get(f"/repos/{full}/commits", sha=branch, per_page=1) or [None])[0])

    # Weekly commit counts, oldest week first
    activity = [0] * weeks
    for c in human:
        age = (NOW - parse_date(c["commit"]["author"]["date"])).days
        idx = weeks - 1 - age // 7
        if 0 <= idx < weeks:
            activity[idx] += 1

    release = get(f"/repos/{full}/releases/latest")
    has_claude = get(f"/repos/{full}/contents/CLAUDE.md", ref=branch) is not None

    last_date = parse_date(latest["commit"]["committer"]["date"]) if latest else parse_date(r["pushed_at"])
    days_since = (NOW - last_date).days

    image = curation.get("image")
    if image:
        image = f"https://raw.githubusercontent.com/{full}/{branch}/{requests.utils.quote(image)}"

    project = {
        "name": r["name"],
        "title": curation.get("title") or r["name"],
        "tagline": curation.get("tagline") or r.get("description") or "",
        "description": r.get("description") or "",
        "platform": curation.get("platform"),
        "image": image,
        "url": r["html_url"],
        "homepage": r.get("homepage") or None,
        "language": r.get("language"),
        "topics": r.get("topics", []),
        "stars": r["stargazers_count"],
        "forks": r["forks_count"],
        "open_issues": r["open_issues_count"],
        "created_at": r["created_at"],
        "last_commit": {
            "date": last_date.isoformat(),
            "message": latest["commit"]["message"].split("\n")[0] if latest else None,
            "sha": latest["sha"][:7] if latest else None,
            "url": latest["html_url"] if latest else None,
        },
        "days_since_commit": days_since,
        "status": status_for(days_since),
        "commits_30d": sum(1 for c in human if (NOW - parse_date(c["commit"]["author"]["date"])).days < 30),
        "activity": activity,
        "release": {
            "tag": release["tag_name"],
            "name": release.get("name") or release["tag_name"],
            "date": release["published_at"],
            "url": release["html_url"],
        } if release else None,
        "built_with_claude": has_claude,
    }
    feed = [
        {
            "repo": r["name"],
            "title": project["title"],
            "message": c["commit"]["message"].split("\n")[0],
            "sha": c["sha"][:7],
            "url": c["html_url"],
            "date": c["commit"]["author"]["date"],
        }
        for c in human
        if len(c.get("parents", [])) < 2  # skip merge commits
    ]
    return project, feed


# ---------- README rendering ----------

def rel_days(days):
    if days <= 0:
        return "today"
    if days == 1:
        return "yesterday"
    if days < 30:
        return f"{days} days ago"
    if days < 365:
        return f"{days // 30} mo ago"
    return f"{days // 365} yr ago"


def spark(activity):
    bars = "▁▂▃▄▅▆▇█"
    peak = max(activity) or 1
    return "".join(bars[0 if v == 0 else max(1, round(v / peak * 7))] for v in activity)


def md_escape(s):
    return (s or "").replace("|", "\\|")


def render_featured(projects):
    rows = ["| Project | What it is | Latest | Last 12 weeks |", "|---|---|---|---|"]
    for p in projects:
        tags = [t for t in (p["platform"], p["language"]) if t]
        badges = " · ".join(tags)
        if p["built_with_claude"]:
            badges += " · built with Claude Code"
        latest = f"[{p['release']['tag']}]({p['release']['url']})<br>" if p["release"] else ""
        latest += f"<sub>committed {rel_days(p['days_since_commit'])}</sub>"
        rows.append(
            f"| **[{md_escape(p['title'])}]({p['url']})**<br><sub>{badges}</sub> "
            f"| {md_escape(p['tagline'])} "
            f"| {latest} "
            f"| `{spark(p['activity'])}`"
            + (f"<br><sub>{p['commits_30d']} commits this month</sub>" if p["commits_30d"] else "")
            + " |"
        )
    return "\n".join(rows)


def render_activity(feed):
    lines = []
    for c in feed:
        days = (NOW - parse_date(c["date"])).days
        lines.append(f"- **{c['title']}** · [`{c['sha']}`]({c['url']}) {md_escape(c['message'])} <sub>{rel_days(days)}</sub>")
    return "\n".join(lines) or "_No commits in the last few weeks._"


def render_more(projects):
    rows = ["| Project | Description | Language | Last commit |", "|---|---|---|---|"]
    for p in projects:
        rows.append(
            f"| [{p['name']}]({p['url']}) | {md_escape(p['description']) or '—'} "
            f"| {p['language'] or '—'} | {rel_days(p['days_since_commit'])} |"
        )
    return "\n".join(rows)


def replace_section(content, name, body):
    pattern = re.compile(rf"(<!-- {name}:START -->).*?(<!-- {name}:END -->)", re.DOTALL)
    if not pattern.search(content):
        print(f"warning: {name} markers not found in README.md", file=sys.stderr)
        return content
    return pattern.sub(lambda m: f"{m.group(1)}\n{body}\n{m.group(2)}", content)


def main():
    cfg = json.loads((ROOT / "key-projects.json").read_text())
    owner = cfg["owner"]
    curation = {f["repo"]: f for f in cfg.get("featured", [])}
    exclude = set(cfg.get("exclude", []))
    include_forks = set(cfg.get("include_forks", []))

    repos = [
        r for r in all_repos(owner)
        if not r["private"] and not r["archived"] and r["name"] not in exclude
        and (not r["fork"] or r["name"] in include_forks)
    ]

    projects, feed = [], []
    for r in repos:
        print(f"  {r['name']}")
        p, f = build_project(r, cfg, curation.get(r["name"], {}))
        projects.append(p)
        feed += f

    by_name = {p["name"]: p for p in projects}
    featured = [by_name[f["repo"]] for f in cfg.get("featured", []) if f["repo"] in by_name]
    for f in cfg.get("featured", []):
        if f["repo"] not in by_name:
            # Renamed, made private, archived or a fork: surfaces as an annotation on the Actions run
            print(f"::warning::Featured repo '{f['repo']}' in key-projects.json was not found among public repos")
    others = sorted(
        (p for p in projects if p["name"] not in curation),
        key=lambda p: p["last_commit"]["date"], reverse=True,
    )
    # Newest first, at most 2 per project so one busy repo doesn't fill the feed
    feed.sort(key=lambda c: c["date"], reverse=True)
    per_repo, trimmed = {}, []
    for c in feed:
        per_repo[c["repo"]] = per_repo.get(c["repo"], 0) + 1
        if per_repo[c["repo"]] <= 2:
            trimmed.append(c)
    feed = trimmed[: cfg.get("activity_items", 8)]

    data = {
        "generated_at": NOW.isoformat(timespec="seconds"),
        "owner": owner,
        "totals": {
            "projects": len(projects),
            "active": sum(1 for p in projects if p["status"] == "active"),
            "commits_30d": sum(p["commits_30d"] for p in projects),
            "built_with_claude": sum(1 for p in projects if p["built_with_claude"]),
        },
        "activity": feed,
        "featured": featured,
        "others": others,
    }
    (ROOT / "projects.json").write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    print(f"projects.json: {len(featured)} featured, {len(others)} others, {len(feed)} activity items")

    readme = ROOT / "README.md"
    content = readme.read_text()
    content = replace_section(content, "FEATURED", render_featured(featured))
    content = replace_section(content, "ACTIVITY", render_activity(feed))
    content = replace_section(content, "MORE", render_more(others))
    content = replace_section(content, "UPDATED", f"<sub>Updated {NOW:%b %-d, %Y} from the GitHub API · {data['totals']['active']} projects active in the last 30 days</sub>")
    readme.write_text(content)


if __name__ == "__main__":
    main()
