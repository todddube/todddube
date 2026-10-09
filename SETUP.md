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

## Weekly high score

The "High score" section is an arcade scoreboard computed by the same daily run from real commit data (no AI-written text, so it can't drift from the facts):

- **Score** is commits this week, one point each. Weeks run Monday to Sunday in the `timezone` set in `key-projects.json` (default `America/New_York`). Merge commits and bot commits don't count.
- **HI-SCORE** is the best week on record. `weekly.json` stores one entry per week and is never trimmed, so the record outlives the 12-week window the API provides. A week is final once the following Monday's run has written it.
- **With Claude** is the share of commits carrying a Claude Code trailer (`Co-Authored-By: Claude`). It's a floor: commits made without the trailer count as unassisted.
- **Streak** is consecutive days with a commit, counting back from today (or yesterday if today has none).
- Only public repos that appear on the site are counted. To change the timezone, edit `timezone` in `key-projects.json`.

## Where do I edit...?

| I want to change | Edit |
|---|---|
| Which projects are spotlighted or featured, their order, taglines, screenshots | `key-projects.json` |
| A project's description in "Everything else" | The repo's description on GitHub |
| The intro paragraph | `.hero-about` in `index.html` and the blockquote in `README.md` (keep them in sync) |
| Layout, colors, copy around the lists | `index.html` |
| What data is collected, how the weekly score is computed, or how the README tables look | `.github/scripts/update_projects.py` |
| Fonts, colors, scanlines | The `<style>` block in `index.html` (palette tokens at the top, font tokens in `:root`) |
| Timezone for the weekly score | `timezone` in `key-projects.json` |
| Update schedule | `.github/workflows/update-projects.yml` |

Never hand-edit `projects.json` or the content between `<!-- NAME:START/END -->` markers in `README.md`; the daily run overwrites them. A featured repo that was renamed, made private or archived is dropped from the site, and the run logs a warning annotation naming it.

## Choosing what's featured

Edit `key-projects.json`:

| Field | Purpose |
|---|---|
| `featured` | Repos shown above "Everything else", in this order. `title`, `tagline`, `platform` and `image` (a path inside that repo) are optional. |
| `featured[].spotlight` / `why` | `"spotlight": true` shows the repo as a large card in the Spotlight grid (in `featured` order); `why` is its one-line pitch. Unflagged repos appear under "More projects". |
| `featured[].path` | Optional folder inside the repo (e.g. `spritemove`). The card links to that folder instead of the repo root. |
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
- `statusline/` is an unrelated backup of the Claude Code statusline config.
- `claude.yml` and `claude-code-review.yml` hook Claude Code into issues and PRs.
