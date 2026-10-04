# How this repo works

This repo is both the GitHub profile README and the site at **www.thedubes.com** (GitHub Pages, custom domain via `CNAME`, `.nojekyll` so `index.html` is served as-is). Both are about the projects, and both are generated from the same data.

## Data flow

```
key-projects.json ──┐
                    ├─► .github/scripts/update_projects.py ─┬─► projects.json ─► index.html (fetched in the browser)
GitHub API ─────────┘                                       └─► README.md (sections between <!-- NAME:START/END --> markers)
```

`.github/workflows/update-projects.yml` runs the script daily at 9:00 UTC, on manual dispatch, and whenever `key-projects.json` or the script changes on `main`.

For each public, non-fork repo the script collects:

- the latest commit (message, sha, date) and commits per week for the last 12 weeks
- commits in the last 30 days, excluding bots
- the latest release, if any
- whether the repo has a `CLAUDE.md`, shown as "Built with Claude Code"
- stars, language, topics, description

It also builds the "Latest commits" feed: newest first, at most 2 per project, merge commits skipped.

## Choosing what's featured

Edit `key-projects.json`:

| Field | Purpose |
|---|---|
| `featured` | Repos shown under "Now building", in this order. `title`, `tagline`, `platform` and `image` (a path inside that repo) are optional. |
| `exclude` | Repos never shown. |
| `include_forks` | Forks to treat as your own work (forks are hidden by default). |
| `activity_items` / `activity_weeks` | Length of the commit feed and the activity strip. |

Every other public, non-fork repo appears automatically under "Everything else". Private and archived repos are never listed.

## Running locally

```bash
GITHUB_TOKEN=$(gh auth token) python3 .github/scripts/update_projects.py
python3 -m http.server 8000   # then open http://localhost:8000
```

`index.html` has to be served over HTTP (not opened as a file) because it fetches `projects.json`.

## Other workflows

- `snake.yml` builds the contribution-snake SVGs into the `output` branch (used in the README).
- `claude.yml` and `claude-code-review.yml` hook Claude Code into issues and PRs.
