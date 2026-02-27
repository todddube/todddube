#!/bin/bash
# Claude Code statusLine command
# Multi-line AI STATUSLINE display with ANSI colors

# ── ANSI color codes ─────────────────────────────────────────────────────────
RESET='\033[0m'
BOLD='\033[1m'
DIM='\033[2m'
CYAN='\033[36m'
BRIGHT_CYAN='\033[96m'
YELLOW='\033[33m'
BRIGHT_YELLOW='\033[93m'
MAGENTA='\033[35m'
BRIGHT_MAGENTA='\033[95m'
GREEN='\033[32m'
BRIGHT_GREEN='\033[92m'
RED='\033[31m'
WHITE='\033[97m'
GRAY='\033[90m'
BLUE='\033[34m'

# ── Read JSON input from stdin ────────────────────────────────────────────────
input=$(cat)

cwd=$(echo "$input" | jq -r '.workspace.current_dir // .cwd // empty')
model=$(echo "$input" | jq -r '.model.display_name // empty')
used=$(echo "$input" | jq -r '.context_window.used_percentage // empty')
session_turns=$(echo "$input" | jq -r '.session.turns // 0')

[ -z "$cwd" ] && cwd="$PWD"

# ── WEATHER / LOCATION CACHE (10-minute TTL) ─────────────────────────────────
CACHE_FILE="/tmp/claude_weather_cache"
CACHE_TTL=600  # seconds

_refresh_cache=0
if [ ! -f "$CACHE_FILE" ]; then
  _refresh_cache=1
else
  _now=$(date +%s)
  _mtime=$(stat -f %m "$CACHE_FILE" 2>/dev/null || stat -c %Y "$CACHE_FILE" 2>/dev/null || echo 0)
  _age=$(( _now - _mtime ))
  [ "$_age" -gt "$CACHE_TTL" ] && _refresh_cache=1
fi

if [ "$_refresh_cache" -eq 1 ]; then
  # Fetch location and weather in background-friendly manner (with short timeout)
  _ip_json=$(curl -s --max-time 3 ipinfo.io/json 2>/dev/null)
  _city=$(echo "$_ip_json" | jq -r '.city // empty' 2>/dev/null)
  _country=$(echo "$_ip_json" | jq -r '.country // empty' 2>/dev/null)
  _loc_str="${_city}, ${_country}"

  if [ -n "$_city" ]; then
    _weather_raw=$(curl -s --max-time 3 "wttr.in/${_city}?format=%t+%C" 2>/dev/null)
    # Strip leading + from temperature (e.g., +18°C → 18°C)
    _weather=$(echo "$_weather_raw" | sed 's/^+//')
  else
    _weather="N/A"
    _loc_str="Unknown"
  fi

  printf '%s\n%s\n' "$_loc_str" "$_weather" > "$CACHE_FILE"
fi

# Read from cache
_cache_loc=$(sed -n '1p' "$CACHE_FILE" 2>/dev/null || echo "Unknown")
_cache_weather=$(sed -n '2p' "$CACHE_FILE" 2>/dev/null || echo "N/A")

# ── LINE 1: HEADER ────────────────────────────────────────────────────────────
_time=$(date +%H:%M)

# Pick a weather emoji based on the condition string
_weather_lower=$(echo "$_cache_weather" | tr '[:upper:]' '[:lower:]')
if echo "$_weather_lower" | grep -qE 'thunder|storm|lightning'; then
  _wx_emoji="⛈️"
elif echo "$_weather_lower" | grep -qE 'snow|blizzard|sleet'; then
  _wx_emoji="❄️"
elif echo "$_weather_lower" | grep -qE 'rain|drizzle|shower'; then
  _wx_emoji="🌧️"
elif echo "$_weather_lower" | grep -qE 'cloud|overcast|fog|mist|haze'; then
  _wx_emoji="⛅"
elif echo "$_weather_lower" | grep -qE 'sunny|clear|sun'; then
  _wx_emoji="☀️"
elif echo "$_weather_lower" | grep -qE 'partly'; then
  _wx_emoji="🌤️"
else
  _wx_emoji="🌤️"
fi

printf "${BOLD}${BRIGHT_CYAN}▶ AI STATUSLINE${RESET}${CYAN} | 🌍 ${YELLOW}${_cache_loc}${CYAN} | 🕐 ${YELLOW}${_time}${CYAN} | ${_wx_emoji} ${YELLOW}${_cache_weather}${RESET}\n"

# ── LINE 2: ENV ───────────────────────────────────────────────────────────────
_cc_ver=$(claude --version 2>/dev/null | head -1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
[ -z "$_cc_ver" ] && _cc_ver="—"
_pai_ver="v3.0"
_alg_ver="v1.2.0"
_sk_count=$(find ~/.claude -maxdepth 2 -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
_wf_count=$(cat ~/.claude/projects/-Users-todddube-Documents-Github-todddube/memory/*.md 2>/dev/null | wc -l | tr -d ' ')
_hooks_count=$(jq '[.hooks // {} | to_entries[] | .value | length] | add // 0' ~/.claude/settings.json 2>/dev/null || echo 0)

printf "${GRAY}ENV:${RESET} 🤖 ${DIM}CC:${RESET} ${CYAN}${_cc_ver}${RESET} ${GRAY}|${RESET} 🧠 ${DIM}PAI:${RESET} ${CYAN}${_pai_ver}${RESET} ${GRAY}|${RESET} ⚙️  ${DIM}ALG:${RESET} ${CYAN}${_alg_ver}${RESET} ${GRAY}|${RESET} 🎯 ${DIM}SK:${RESET} ${CYAN}${_sk_count}${RESET} ${GRAY}|${RESET} 🔄 ${DIM}WF:${RESET} ${CYAN}${_wf_count}${RESET} ${GRAY}|${RESET} 🪝 ${DIM}Hooks:${RESET} ${CYAN}${_hooks_count}${RESET}\n"

# ── LINE 3: CONTEXT PROGRESS BAR ─────────────────────────────────────────────
BAR_WIDTH=40
_used_pct=0
if [ -n "$used" ] && [ "$used" != "null" ]; then
  _used_pct=$(printf "%.0f" "$used" 2>/dev/null || echo 0)
fi

_filled=$(( BAR_WIDTH * _used_pct / 100 ))
[ "$_filled" -gt "$BAR_WIDTH" ] && _filled=$BAR_WIDTH
_empty=$(( BAR_WIDTH - _filled ))

# Choose bar color based on percentage
if [ "$_used_pct" -lt 50 ]; then
  _bar_color="${GREEN}"
elif [ "$_used_pct" -lt 80 ]; then
  _bar_color="${YELLOW}"
else
  _bar_color="${RED}"
fi

_bar_filled=$(printf '%0.s█' $(seq 1 $_filled 2>/dev/null) 2>/dev/null || python3 -c "print('█' * $_filled, end='')")
_bar_empty=$(printf '%0.s░' $(seq 1 $_empty 2>/dev/null) 2>/dev/null || python3 -c "print('░' * $_empty, end='')")

printf "📊 ${CYAN}• CONTEXT:${RESET} ${_bar_color}[${_bar_filled}${GRAY}${_bar_empty}${_bar_color}]${RESET} ${BRIGHT_YELLOW}${_used_pct}%%${RESET}\n"

# ── LINE 4: USAGE ─────────────────────────────────────────────────────────────
_now_ts=$(date +%H:%M)
printf "⚡ ${CYAN}▪ USAGE:${RESET} ${DIM}5H:${RESET} ${YELLOW}${_used_pct}%%${RESET} ${GRAY}↑${RESET}${WHITE}${_now_ts}${RESET} ${GRAY}|${RESET} ${DIM}WK:${RESET} ${YELLOW}—${RESET} ${GRAY}↓${RESET}${WHITE}—${RESET}\n"

# ── LINE 5: PWD / GIT ─────────────────────────────────────────────────────────
_dirname=$(basename "$cwd")

_branch="—"
_age="—"
_mod_count=0
_ahead=0

if git -C "$cwd" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  _branch=$(git -C "$cwd" -c gc.auto=0 symbolic-ref --short HEAD 2>/dev/null || echo "detached")

  # Parse "X minutes ago" / "X hours ago" / "X days ago" into compact form
  _age_raw=$(git -C "$cwd" -c gc.auto=0 log -1 --format="%cr" 2>/dev/null)
  if [ -n "$_age_raw" ]; then
    _age=$(echo "$_age_raw" \
      | sed 's/ seconds\? ago/s/' \
      | sed 's/ minutes\? ago/m/' \
      | sed 's/ hours\? ago/h/' \
      | sed 's/ days\? ago/d/' \
      | sed 's/ weeks\? ago/w/' \
      | sed 's/ months\? ago/mo/' \
      | sed 's/ years\? ago/y/' \
      | sed 's/^\([0-9]*\) \([smhdwy][a-z]*\)$/\1\2/')
  fi

  _mod_count=$(git -C "$cwd" -c gc.auto=0 diff --name-only 2>/dev/null | wc -l | tr -d ' ')
  _ahead=$(git -C "$cwd" -c gc.auto=0 rev-list --count HEAD@{upstream}..HEAD 2>/dev/null || echo 0)
fi

printf "📁 ${BRIGHT_YELLOW}▲ PWD:${RESET} ${YELLOW}${_dirname}${RESET} ${GRAY}|${RESET} 🌿 ${DIM}Branch:${RESET} ${MAGENTA}${_branch}${RESET} ${GRAY}|${RESET} ⏱️  ${DIM}Age:${RESET} ${WHITE}${_age}${RESET} ${GRAY}|${RESET} ✏️  ${DIM}Mod:${RESET} ${WHITE}${_mod_count}${RESET} ${GRAY}|${RESET} 🔄 ${DIM}Sync:${RESET} ${GREEN}↑${_ahead}${RESET}\n"

# ── LINE 6: MEMORY ────────────────────────────────────────────────────────────
_mem_dir="$HOME/.claude/projects/-Users-todddube-Documents-Github-todddube/memory"
_mem_work=0
_mem_ratings=0
_mem_sessions=0
_mem_research=0

if [ -d "$_mem_dir" ]; then
  # Work: lines in MEMORY.md
  [ -f "$_mem_dir/MEMORY.md" ] && _mem_work=$(wc -l < "$_mem_dir/MEMORY.md" 2>/dev/null | tr -d ' ')

  # Ratings: total lines across all .md files
  _mem_total=$(cat "$_mem_dir"/*.md 2>/dev/null | wc -l | tr -d ' ')
  _mem_ratings=$_mem_total

  # Sessions: use session turns from JSON input, or count project .jsonl files
  if [ "$session_turns" != "0" ] && [ "$session_turns" != "null" ] && [ -n "$session_turns" ]; then
    _mem_sessions=$session_turns
  else
    _mem_sessions=$(find "$HOME/.claude/projects/-Users-todddube-Documents-Github-todddube" -maxdepth 1 -name "*.jsonl" 2>/dev/null | wc -l | tr -d ' ')
  fi

  # Research: lines in any file containing "research" in the name
  _mem_research=$(find "$_mem_dir" -iname "*research*" -exec wc -l {} \; 2>/dev/null | awk '{sum+=$1} END{print sum+0}')
fi

printf "🧠 ${CYAN}○ MEMORY:${RESET} 📂 ${WHITE}${_mem_work}${RESET} ${DIM}Work${RESET} ${GRAY}|${RESET} ⭐ ${WHITE}${_mem_ratings}${RESET} ${DIM}Ratings${RESET} ${GRAY}|${RESET} 💬 ${WHITE}${_mem_sessions}${RESET} ${DIM}Sessions${RESET} ${GRAY}|${RESET} 🔬 ${WHITE}${_mem_research}${RESET} ${DIM}Research${RESET}\n"

# ── LINE 7: LEARNING ─────────────────────────────────────────────────────────
printf "📚 ${CYAN}○ LEARNING:${RESET} ${WHITE}0${RESET}${DIM}IMP${RESET} ${GRAY}|${RESET} ${DIM}15m:${RESET} ${GRAY}—${RESET} ${DIM}60m:${RESET} ${WHITE}0${RESET} ${DIM}1d:${RESET} ${WHITE}0${RESET} ${DIM}1w:${RESET} ${WHITE}0${RESET} ${DIM}1mo:${RESET} ${WHITE}0${RESET}\n"
