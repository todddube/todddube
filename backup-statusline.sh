#!/bin/bash
# backup-statusline.sh
# Backs up Claude Code statusline config into this repo's statusline/ directory.
# Run from the repo root: ./backup-statusline.sh

set -e

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKUP_DIR="$REPO_DIR/statusline"
CLAUDE_DIR="$HOME/.claude"
SETTINGS="$CLAUDE_DIR/settings.json"
SCRIPT="$CLAUDE_DIR/statusline-command.sh"

# Colors
GREEN='\033[32m'
CYAN='\033[36m'
YELLOW='\033[33m'
RESET='\033[0m'

echo -e "${CYAN}▶ Claude Code Statusline Backup${RESET}"
echo "  Destination: $BACKUP_DIR"
echo ""

mkdir -p "$BACKUP_DIR"

# 1. Copy the statusline shell script
if [ -f "$SCRIPT" ]; then
  cp "$SCRIPT" "$BACKUP_DIR/statusline-command.sh"
  echo -e "  ${GREEN}✓${RESET} statusline-command.sh"
else
  echo -e "  ${YELLOW}⚠${RESET}  statusline-command.sh not found at $SCRIPT"
fi

# 2. Extract just the statusLine section from settings.json
if [ -f "$SETTINGS" ]; then
  jq '{statusLine: .statusLine}' "$SETTINGS" > "$BACKUP_DIR/statusline-settings.json"
  echo -e "  ${GREEN}✓${RESET} statusline-settings.json (statusLine config extracted)"
else
  echo -e "  ${YELLOW}⚠${RESET}  settings.json not found at $SETTINGS"
fi

# 3. Write a restore script alongside the backup
cat > "$BACKUP_DIR/restore-statusline.sh" << 'EOF'
#!/bin/bash
# restore-statusline.sh
# Restores statusline config from this backup to ~/.claude/
# Run from the statusline/ directory: ./restore-statusline.sh

set -e
BACKUP_DIR="$(cd "$(dirname "$0")" && pwd)"
CLAUDE_DIR="$HOME/.claude"
SETTINGS="$CLAUDE_DIR/settings.json"
SCRIPT="$CLAUDE_DIR/statusline-command.sh"

GREEN='\033[32m'; YELLOW='\033[33m'; CYAN='\033[36m'; RESET='\033[0m'

echo -e "${CYAN}▶ Restoring Claude Code Statusline${RESET}"

# Restore the script
if [ -f "$BACKUP_DIR/statusline-command.sh" ]; then
  cp "$BACKUP_DIR/statusline-command.sh" "$SCRIPT"
  chmod +x "$SCRIPT"
  echo -e "  ${GREEN}✓${RESET} Restored statusline-command.sh"
else
  echo -e "  ${YELLOW}⚠${RESET}  No statusline-command.sh found in backup"
fi

# Merge statusLine key back into settings.json
if [ -f "$BACKUP_DIR/statusline-settings.json" ] && [ -f "$SETTINGS" ]; then
  _merged=$(jq -s '.[0] * .[1]' "$SETTINGS" "$BACKUP_DIR/statusline-settings.json")
  echo "$_merged" > "$SETTINGS"
  echo -e "  ${GREEN}✓${RESET} Merged statusLine config into settings.json"
elif [ -f "$BACKUP_DIR/statusline-settings.json" ]; then
  cp "$BACKUP_DIR/statusline-settings.json" "$SETTINGS"
  echo -e "  ${GREEN}✓${RESET} Wrote statusline-settings.json to settings.json"
else
  echo -e "  ${YELLOW}⚠${RESET}  No statusline-settings.json found in backup"
fi

echo ""
echo "Done. Restart Claude Code to apply changes."
EOF
chmod +x "$BACKUP_DIR/restore-statusline.sh"
echo -e "  ${GREEN}✓${RESET} restore-statusline.sh (generated)"

echo ""

# 4. Show git status for the backup dir
cd "$REPO_DIR"
if git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
  _changed=$(git diff --name-only HEAD -- statusline/ 2>/dev/null; git ls-files --others --exclude-standard statusline/ 2>/dev/null)
  if [ -n "$_changed" ]; then
    echo -e "${YELLOW}Changes to commit:${RESET}"
    echo "$_changed" | sed 's/^/  /'
    echo ""
    echo -e "  Run: ${CYAN}git add statusline/ && git commit -m 'backup: update statusline config'${RESET}"
  else
    echo -e "${GREEN}No changes${RESET} — backup is up to date with last commit."
  fi
fi
