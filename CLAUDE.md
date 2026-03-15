# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is Todd Dube's personal GitHub profile repository, serving as both a profile README showcase and a GitHub Pages portfolio website at www.thedubes.com.

## Repository Structure

- `README.md` - Main GitHub profile page with bio, tech stack, and project showcases
- `index.html` - Full portfolio website (GitHub Pages), supports light/dark themes
- `_config.yml` - Jekyll/GitHub Pages configuration
- `CNAME` - Custom domain (www.thedubes.com)
- `key-projects.json` - Featured projects data used by workflows
- `.nojekyll` - Bypasses Jekyll processing for index.html
- `images/` - SVG assets for profile branding
- `assets/css/style.scss` - Custom SCSS for Jekyll theme overrides
- `.github/workflows/` - Automated workflows:
  - `update-profile.yml` - Daily: updates index.html with stats, news ticker, AI models, LinkedIn posts
  - `update-readme.yml` - Weekly: updates README featured projects from GitHub API
  - `snake.yml` - Daily: generates contribution snake SVG animations
  - `claude.yml` - Claude Code integration for issues/PRs
  - `claude-code-review.yml` - Automated PR code review

## Key Information

- **Repository Type**: GitHub profile repository (same name as username)
- **Website**: www.thedubes.com (GitHub Pages with custom domain)
- **Theme System**: index.html supports light/dark mode via CSS custom properties with system preference detection and manual toggle
- **No Build System**: No package.json, build scripts, or development dependencies
- **No Testing Framework**: No test configuration or test files
- **Static Content**: HTML, markdown, and SVG assets

## Repository Maintenance

- Updating personal information in README.md
- Modifying project showcases and links in README.md or key-projects.json
- Updating the portfolio website (index.html)
- Theme/styling changes via CSS custom properties in index.html `:root`
- Workflow updates in .github/workflows/
