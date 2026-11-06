#!/usr/bin/env python3
"""Record a site version in versions.json and print the git commands to tag it.

    python3 .github/scripts/release.py minor "One or two lines on what changed."
    python3 .github/scripts/release.py notes 1.2.0     # print one version's notes (used by the release workflow)

The version changes only when the site, scripts or config are changed by hand. The daily data
update never bumps it. Bump kinds: major (redesign or breaking config change), minor (new
feature), patch (fix or copy tweak).
"""
import json
import re
import sys
from datetime import date
from pathlib import Path

PATH = Path(__file__).resolve().parents[2] / "versions.json"
SEMVER = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


def bump(version, kind):
    major, minor, patch = map(int, SEMVER.match(version).groups())
    if kind == "major":
        return f"{major + 1}.0.0"
    if kind == "minor":
        return f"{major}.{minor + 1}.0"
    if kind == "patch":
        return f"{major}.{minor}.{patch + 1}"
    raise ValueError(f"unknown bump kind {kind!r}; use major, minor or patch")


def add_release(data, kind, notes, today):
    version = bump(data["current"], kind)
    data = {**data, "current": version,
            "releases": [{"version": version, "date": today, "notes": notes.strip()}] + data["releases"]}
    return data, version


def main(argv):
    data = json.loads(PATH.read_text())
    if len(argv) == 3 and argv[1] == "notes":
        entry = next((r for r in data["releases"] if r["version"] == argv[2].lstrip("v")), None)
        if not entry:
            sys.exit(f"no entry for {argv[2]} in versions.json")
        print(entry["notes"])
        return
    if len(argv) != 3:
        sys.exit(__doc__)
    data, version = add_release(data, argv[1], argv[2], date.today().isoformat())
    PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    print(f"versions.json is now {version}. Commit it, then:\n  git tag -a v{version} -m \"v{version}\" && git push origin main --follow-tags")


if __name__ == "__main__":
    main(sys.argv)
