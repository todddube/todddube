# GitHub Pages Setup Guide

This repository is configured as a GitHub Pages website hosted at **www.thedubes.com**.

## Overview

This is a personal portfolio and profile showcase that uses:
- **GitHub Pages** for hosting
- **Jekyll** for static site generation
- **Custom CSS** for styling
- **Automated workflows** for content updates
- **Key projects JSON** for project management

## Repository Structure

```
todddube/
├── README.md                    # Main profile page (also serves as homepage)
├── _config.yml                  # Jekyll/GitHub Pages configuration
├── CNAME                        # Custom domain configuration
├── key-projects.json            # Featured projects data
├── assets/
│   └── css/
│       └── style.scss          # Custom CSS styling
├── images/
│   ├── ToddDube_Logo.svg       # Personal logo
│   └── profile_banner.svg      # Profile banner
├── .github/
│   └── workflows/
│       ├── update-readme.yml   # Auto-update profile content
│       └── snake.yml           # Contribution snake animation
└── CLAUDE.md                   # Instructions for Claude Code
```

## Key Features

### 1. GitHub Pages Website
- **URL**: www.thedubes.com
- **Theme**: jekyll-theme-minimal
- **Hosting**: GitHub Pages with custom domain

### 2. Key Projects Management
Projects are managed via `key-projects.json` which allows you to:
- Define featured projects with priority ordering
- Categorize projects (AI, IoT, Gaming, etc.)
- Control which projects are highlighted
- Add metadata like emojis, tags, and status

### 3. Automated Content Updates
The `update-readme.yml` workflow automatically:
- Loads key projects from `key-projects.json`
- Updates GitHub statistics
- Refreshes recent activity
- Maintains the "Key Projects" section at the top
- Runs twice weekly (Monday and Thursday at 8:00 UTC)

### 4. Custom Styling
Custom SCSS in `assets/css/style.scss` provides:
- Modern gradient designs
- Responsive layout
- Dark mode support
- Animated elements
- Professional color scheme

## Managing Key Projects

### Adding a New Project

Edit `key-projects.json` and add a new entry:

```json
{
  "name": "project-name",
  "title": "Project Display Title",
  "description": "Brief description of the project",
  "url": "https://github.com/todddube/project-name",
  "category": "category-name",
  "priority": 1,
  "emoji": "🚀",
  "tags": ["tag1", "tag2"],
  "status": "active",
  "highlight": true
}
```

**Fields:**
- `name`: Repository name (used for links)
- `title`: Display title for the project
- `description`: One-line project description
- `url`: Full GitHub URL
- `category`: Project category (ai, iot, gaming, retro, utilities, automation)
- `priority`: Display order (lower = higher priority)
- `emoji`: Icon emoji
- `tags`: Array of relevant tags
- `status`: Project status (active, archived, wip)
- `highlight`: Show in key projects section (true/false)

### Project Priority

The project with `priority: 1` and `highlight: true` will be featured prominently at the top. The next 4 highlighted projects (priority 2-5) will appear in the grid below.

## Updating Content

### Manual Update
Run the workflow manually:
1. Go to Actions tab in GitHub
2. Select "Auto-Update Profile README"
3. Click "Run workflow"

### Automatic Updates
The workflow runs automatically:
- **Schedule**: Monday and Thursday at 8:00 AM UTC
- **What it updates**: Stats, recent activity, key projects section

## Custom Domain Setup

The website uses **www.thedubes.com** as the custom domain.

### DNS Configuration Required
To activate the custom domain, configure DNS records:

1. **CNAME Record** (recommended):
   ```
   Type: CNAME
   Host: www
   Value: todddube.github.io
   TTL: 3600
   ```

2. **Alternative A Records** (if CNAME isn't available):
   ```
   Type: A
   Host: @
   Value: 185.199.108.153
   Value: 185.199.109.153
   Value: 185.199.110.153
   Value: 185.199.111.153
   ```

### Enabling GitHub Pages
1. Go to repository Settings
2. Navigate to Pages section
3. Source: Deploy from branch `main`
4. Custom domain: `www.thedubes.com`
5. Enforce HTTPS: ✓ Enabled

## Theme Customization

### Modifying Styles
Edit `assets/css/style.scss` to customize:
- Colors (`:root` variables)
- Layout and spacing
- Animations
- Dark mode behavior

### Changing Theme
Edit `_config.yml`:
```yaml
theme: jekyll-theme-minimal  # Change to any GitHub-supported theme
```

Supported themes:
- jekyll-theme-minimal
- jekyll-theme-cayman
- jekyll-theme-slate
- jekyll-theme-architect
- And more...

## Workflow Configuration

### Update Frequency
Edit `.github/workflows/update-readme.yml`:
```yaml
schedule:
  - cron: "0 8 * * 1,4"  # Modify this line
```

Cron format: `minute hour day month weekday`

### Workflow Options
Manual trigger supports:
- Update statistics: true/false
- Update projects: true/false

## Best Practices

### Project Management
1. Keep `key-projects.json` organized
2. Use priority 1-10 for highlighted projects
3. Set `highlight: false` for older/less important projects
4. Update project descriptions regularly

### Content Updates
1. Don't manually edit the "Key Projects" section in README.md
2. Let the workflow handle updates
3. Make changes in `key-projects.json` instead

### Website Maintenance
1. Test changes locally with Jekyll if possible
2. Use GitHub's preview before publishing
3. Monitor Actions tab for workflow success
4. Keep custom CSS organized and commented

## Troubleshooting

### Website Not Loading
- Check DNS propagation (can take 24-48 hours)
- Verify CNAME file contains `www.thedubes.com`
- Ensure GitHub Pages is enabled in settings

### Workflow Failures
- Check Actions tab for error logs
- Verify `key-projects.json` is valid JSON
- Ensure Python dependencies are available

### Styling Issues
- Clear browser cache
- Check for SCSS syntax errors
- Verify theme is loading correctly

## Development

### Local Testing (Optional)
Install Jekyll locally to test:

```bash
# Install Ruby and Bundler
gem install bundler jekyll

# Create Gemfile (if not exists)
bundle init

# Add Jekyll
bundle add jekyll

# Serve locally
bundle exec jekyll serve
```

Visit: http://localhost:4000

## Resources

- [GitHub Pages Documentation](https://docs.github.com/en/pages)
- [Jekyll Documentation](https://jekyllrb.com/docs/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Markdown Guide](https://www.markdownguide.org/)

## Support

For issues or questions:
1. Check this documentation
2. Review GitHub Actions logs
3. Consult GitHub Pages documentation
4. Open an issue in this repository

---

**Last Updated**: November 2, 2025
**Maintained By**: Todd Dube
**Website**: www.thedubes.com
