# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

Todd Dube's GitHub profile repository and the GitHub Pages site at www.thedubes.com. Both showcase his current open-source projects (not a personal bio): what's being built, recent commits, and activity, generated daily from the GitHub API.

## Repository Structure

- `key-projects.json` - Curation: featured repos (in order), their taglines/platform/screenshot, `top_count` (auto-picked highlight tiles for the most active repos), and exclusions
- `.github/scripts/update_projects.py` - Pulls repo data from the GitHub API, writes `projects.json`, and rewrites README sections between `<!-- NAME:START/END -->` markers
- `.github/scripts/` also has `validate_config.py`, `health_check.py` and `weekly_recap.py`; tests are in `.github/scripts/tests/` (stdlib `unittest`, run by the Validate workflow)
- `projects.json` - Generated data (including the weekly `week` block); do not hand-edit
- `weekly.json` - Generated week-by-week history behind the HI-SCORE; created by the first workflow run, never hand-edit
- `README.md` - Profile README; TOP / FEATURED / ACTIVITY / MORE / UPDATED sections are generated
- `index.html` - Single-file site that fetches `projects.json` client-side; follows the system light/dark setting by default; the toggle saves an override in localStorage (`td-theme-choice`)
- `CNAME`, `.nojekyll` - Custom domain; serve `index.html` as-is
- `versions.json` - Site version history (newest first, one or two lines each), shown in the page footer; edited only by `.github/scripts/release.py`
- `SETUP.md` - How the data flow and curation work
- `.github/workflows/`:
  - `update-projects.yml` - Daily: validates `key-projects.json`, runs the script, commits `projects.json`, `weekly.json` + `README.md`
  - `health-check.yml` - Daily: checks the live site is up and fresh and its links/screenshots load
  - `weekly-recap.yml` - Mondays: posts last week's recap as a closed issue labelled `weekly-recap`
  - `release.yml` - On a pushed `vX.Y.Z` tag: creates the GitHub release with notes from `versions.json`
  - `validate.yml` - On pull requests: API-checks the config, runs the tests, syntax-checks the page JavaScript
  - `.github/dependabot.yml` - Weekly grouped PR to bump the pinned Action versions
  - `snake.yml` - Daily: contribution snake SVGs on the `output` branch
  - `claude.yml`, `claude-code-review.yml` - Claude Code for issues/PRs
- `statusline/` - Backup/restore of the author's Claude Code statusline (not part of the site). `./statusline/backup-statusline.sh` refreshes it.
- `.claude/settings.local.json` - Local-only, gitignored

## Working in this repo

- No Jekyll: `.nojekyll` is set, so `index.html` is served as-is. Don't add `_config.yml` or SCSS.
- No build system. Tests cover the scripts only: `python3 -m unittest discover -s .github/scripts/tests`. Run the generator locally with `GITHUB_TOKEN=$(gh auth token) python3 .github/scripts/update_projects.py`, then serve with `python3 -m http.server`.
- Look and feel is 8-bit on purpose: Sixtyfour (C64 scanlines) for the h1, Press Start 2P for labels, titles and scores, VT323 for all text, plus faint CRT scanlines in dark mode only. Keep square corners and hard offset shadows. VT323 has no bold, so emphasize with color, not weight.
- To change what's featured, edit `key-projects.json` rather than the README or HTML.
- The page has a random Pac-Man run (canvas `#pac`) and an opt-in sound toggle (`td-sound`); keep audio opt-in and respect reduced motion.
- Versioning: the daily Actions run never changes the version. When you change the site, scripts or config by hand here, finish with `python3 .github/scripts/release.py <major|minor|patch> "one or two lines"` (major = redesign or breaking config change, minor = new feature, patch = fix or copy tweak), commit `versions.json` with the change, then `git tag -a vX.Y.Z -m vX.Y.Z` and push with `--follow-tags`. The release workflow publishes the release. Never force-move a tag without asking.
- Keep the focus on projects. The only personal content is a short intro paragraph (`.hero-about` in index.html, the blockquote in README.md); don't expand it into a bio.
