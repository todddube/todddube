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
