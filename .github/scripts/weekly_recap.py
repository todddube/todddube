#!/usr/bin/env python3
"""Build last week's recap (issue title and body) from weekly.json and projects.json.

Everything is computed from data, with no generated prose, so it can't drift from the facts.
Run by .github/workflows/weekly-recap.yml every Monday after the daily update.

    python3 .github/scripts/weekly_recap.py OUTDIR      # writes OUTDIR/title.txt and OUTDIR/body.md

Set RECAP_TODAY=YYYY-MM-DD to build the recap as if run on that date (testing).
"""
import json
import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
BLOCKS = "▁▂▃▄▅▆▇█"


def fmt(d):
    return f"{d:%b} {d.day}"


def label(start):
    return f"WK {start.isocalendar().week:02d}"


def spark(values):
    peak = max(values) or 1
    return "".join(BLOCKS[0] if v == 0 else BLOCKS[max(1, round(v / peak * 7))] for v in values)


def plural(n, word):
    return f"{n} {word}{'' if n == 1 else 's'}"


def local_date(iso, tz):
    return datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(tz).date()


def build_recap(weekly, projects, today, tz):
    """Recap for the Monday-to-Sunday week before `today`. Returns (title, body)."""
    weeks = weekly["weeks"]
    start = today - timedelta(days=today.weekday() + 7)
    end = start + timedelta(days=6)
    week = weeks.get(start.isoformat())
    if week is None:
        raise LookupError(f"weekly.json has no entry for the week of {start}")

    prev = weeks.get((start - timedelta(days=7)).isoformat())
    commits = week["commits"]
    title = f"Weekly recap: {label(start)} ({fmt(start)} to {fmt(end)})"

    rows = []
    delta = ""
    if prev is not None:
        diff = commits - prev["commits"]
        delta = f" ({'▲' if diff > 0 else '▼'} {abs(diff)} vs {label(start - timedelta(days=7))})" if diff else f" (same as {label(start - timedelta(days=7))})"
    rows.append(("Score", f"**{commits}** commit{'' if commits == 1 else 's'}{delta}"))
    rows.append(("Projects touched", str(week["projects"])))
    rows.append(("Active days", f"{week['active_days']} of 7"))
    if commits:
        pct = round(100 * week["claude_commits"] / commits)
        rows.append(("With Claude", f"{pct}% ({week['claude_commits']} of {commits} commits)"))
        if week.get("top_project"):
            rows.append(("Top project", f"{week['top_project']['title']} ({plural(week['top_project']['commits'], 'commit')})"))

    # Best week up to and including this one; ties go to the earliest, like an arcade table
    best = None
    for key in sorted(k for k in weeks if k <= start.isoformat() and weeks[k]["commits"] > 0):
        if best is None or weeks[key]["commits"] > weeks[best]["commits"]:
            best = key
    if best == start.isoformat():
        record = "🏆 **New HI-SCORE.** Best week on record."
    elif best:
        b = date.fromisoformat(best)
        record = f"Best week on record: **{plural(weeks[best]['commits'], 'commit')}** ({label(b)}, week of {fmt(b)})."
    else:
        record = ""

    trend = [weeks.get((start - timedelta(days=7 * i)).isoformat(), {}).get("commits", 0) for i in range(11, -1, -1)]

    shipped = [
        f"{p['title']} {p['release']['tag']}"
        for p in projects if p.get("release") and start <= local_date(p["release"]["date"], tz) <= end
    ]
    created = [p["title"] for p in projects if start <= local_date(p["created_at"], tz) <= end]

    lines = [f"## {label(start)}: {fmt(start)} to {fmt(end)}", ""]
    if commits == 0:
        lines += ["A quiet week: no commits.", ""]
    lines += ["| | |", "|---|---|"] + [f"| {k} | {v} |" for k, v in rows] + [""]
    lines += [f"**Last 12 weeks:** `{spark(trend)}` ({' '.join(map(str, trend))})", ""]
    if record:
        lines += [record, ""]
    if shipped:
        lines += [f"**Released:** {', '.join(shipped)}", ""]
    if created:
        lines += [f"**New repos:** {', '.join(created)}", ""]
    lines += [
        "<sub>Built automatically from `weekly.json` by `.github/scripts/weekly_recap.py`. "
        "One point per commit, Monday to Sunday in "
        f"{'Eastern time' if str(tz) == 'America/New_York' else tz}. "
        "With Claude means commits carrying a Claude Code co-author trailer.</sub>",
    ]
    return title, "\n".join(lines) + "\n"


def main(argv):
    if not argv:
        print("usage: weekly_recap.py OUTDIR", file=sys.stderr)
        return 2
    cfg = json.loads((ROOT / "key-projects.json").read_text())
    tz = ZoneInfo(cfg.get("timezone", "America/New_York"))
    weekly = json.loads((ROOT / "weekly.json").read_text())
    data = json.loads((ROOT / "projects.json").read_text())
    today = date.fromisoformat(os.environ["RECAP_TODAY"]) if os.environ.get("RECAP_TODAY") else datetime.now(tz).date()

    # Last week is only final once today's update has run
    generated = local_date(data["generated_at"], tz)
    if generated < today:
        print(f"::error::projects.json was last generated on {generated}, not today ({today}). "
              "The daily update hasn't run yet, so last week's numbers might not be final. Re-run this workflow after it does.")
        return 1
    try:
        title, body = build_recap(weekly, data["featured"] + data["others"], today, tz)
    except LookupError as e:
        print(f"::error::{e}")
        return 1
    out = Path(argv[0])
    out.mkdir(parents=True, exist_ok=True)
    (out / "title.txt").write_text(title + "\n")
    (out / "body.md").write_text(body)
    print(title)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
