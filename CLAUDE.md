# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

Todd Dube's GitHub profile repository and the GitHub Pages site at www.thedubes.com. Both showcase his current open-source projects (not a personal bio): what's being built, recent commits, and activity, generated daily from the GitHub API.

## Repository Structure

- `key-projects.json` - Curation: which repos are featured (in order), their taglines/platform/screenshot, and exclusions
- `.github/scripts/update_projects.py` - Pulls repo data from the GitHub API, writes `projects.json`, and rewrites README sections between `<!-- NAME:START/END -->` markers
- `projects.json` - Generated data; do not hand-edit
- `README.md` - Profile README; FEATURED / ACTIVITY / MORE / UPDATED sections are generated
- `index.html` - Single-file site that fetches `projects.json` client-side; light/dark via `data-theme` and CSS custom properties on `:root`
- `CNAME`, `.nojekyll` - Custom domain; serve `index.html` as-is
- `SETUP.md` - How the data flow and curation work
- `.github/workflows/`:
  - `update-projects.yml` - Daily: runs the script and commits `projects.json` + `README.md`
  - `snake.yml` - Daily: contribution snake SVGs on the `output` branch
  - `claude.yml`, `claude-code-review.yml` - Claude Code for issues/PRs

## Working in this repo

- No build system or tests. Run the generator locally with `GITHUB_TOKEN=$(gh auth token) python3 .github/scripts/update_projects.py`, then serve with `python3 -m http.server`.
- To change what's featured, edit `key-projects.json` rather than the README or HTML.
- Keep the focus on projects. The only personal content is a short intro paragraph (`.hero-about` in index.html, the blockquote in README.md); don't expand it into a bio.
