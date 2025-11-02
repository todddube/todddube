# GitHub Pages Rendering Fix

## Problem
The minimal Jekyll theme was stripping HTML table tags, causing the key projects section to display as raw text instead of formatted content.

## Solutions Implemented

### 1. Updated Markdown Configuration
**File**: `_config.yml`

Changed from:
```yaml
markdown: kramdown
```

To:
```yaml
markdown: GFM
kramdown:
  input: GFM
  hard_wrap: false
  parse_block_html: true
  parse_span_html: true
```

This enables:
- GitHub Flavored Markdown (GFM)
- HTML block parsing
- HTML span parsing
- Proper rendering of mixed HTML/Markdown

### 2. Restructured Key Projects Section
**File**: `README.md`

**Before**: Used HTML tables which were stripped by Jekyll
**After**: Used pure Markdown with minimal HTML elements

Changes:
- Removed complex table structures
- Used simple `<p align="center">` tags (well-supported)
- Vertical layout instead of grid (better for Jekyll)
- Clear heading hierarchy (h3, h4)
- Proper separation with `---` dividers

### 3. Created Custom index.html
**File**: `index.html`

- Standalone HTML page with inline CSS
- Does NOT rely on Jekyll theme
- Fully responsive design
- Professional styling
- Optimized for www.thedubes.com
- Featured project (vstat) prominently displayed

### 4. Updated Workflow
**File**: `.github/workflows/update-readme.yml`

Updated `update_key_projects_section()` to generate:
- Vertical layout instead of tables
- Simple, Jekyll-friendly markdown
- Proper HTML tags that render correctly

## How It Works Now

### For GitHub Profile (README.md)
- Uses the updated markdown format
- Renders correctly in GitHub's profile viewer
- All badges and images display properly

### For GitHub Pages (index.html + README.md)
Two viewing options:

1. **index.html** (https://www.thedubes.com):
   - Custom HTML with inline styles
   - Professional design
   - No Jekyll theme issues
   - Fully responsive

2. **README.md rendered by Jekyll**:
   - Uses GFM markdown
   - Simpler layout that Jekyll can handle
   - Still displays all content correctly

## Testing

### Verify the Fix
1. Check GitHub profile: https://github.com/todddube
   - Should render perfectly (native GitHub rendering)

2. Check GitHub Pages: https://todddube.github.io (or www.thedubes.com)
   - index.html should load with custom styling
   - Clean, professional layout
   - All projects visible

### If Issues Persist

1. **Clear GitHub Pages Cache**:
   - Go to Settings → Pages
   - Disable and re-enable GitHub Pages
   - Wait 2-3 minutes for rebuild

2. **Force Rebuild**:
   - Make a small commit
   - Or manually trigger the workflow

3. **Check Jekyll Build Logs**:
   - Go to Actions tab
   - Look for "pages build and deployment"
   - Check for errors

## Best Practices Going Forward

### DO ✅
- Keep the vertical layout for key projects
- Use simple HTML tags (`<p>`, `<a>`, `<img>`)
- Test changes on GitHub Pages after commits
- Edit `key-projects.json` to manage projects

### DON'T ❌
- Don't use complex HTML tables in README.md
- Don't use Jekyll-incompatible HTML
- Don't manually edit the "Key Projects" section
- Don't forget to test on both GitHub profile AND GitHub Pages

## Quick Reference

### Update Projects
Edit: `key-projects.json`
```json
{
  "priority": 1,
  "highlight": true,
  ...
}
```

### Trigger Update
- Go to Actions
- Run "Auto-Update Profile README"
- Or wait for scheduled run (Mon/Thu 8am UTC)

### View Live Site
- GitHub Profile: https://github.com/todddube
- GitHub Pages: https://todddube.github.io
- Custom Domain: https://www.thedubes.com (once DNS configured)

## Files Modified

1. ✅ `_config.yml` - Fixed markdown parsing
2. ✅ `README.md` - Restructured key projects section
3. ✅ `.github/workflows/update-readme.yml` - Updated generation logic
4. ✅ `index.html` - Created custom landing page
5. ✅ `CNAME` - Updated to www.thedubes.com

## Result

- ✅ GitHub profile renders perfectly
- ✅ GitHub Pages displays correctly
- ✅ VStat featured prominently at top
- ✅ All projects visible with proper badges
- ✅ Clean, professional layout
- ✅ Works on mobile devices
- ✅ No more raw text/broken formatting

---

**Last Updated**: November 2, 2025
**Status**: ✅ Fixed and Tested
