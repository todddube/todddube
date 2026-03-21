#!/bin/bash
# Claude Code multi-line statusLine
# Displays: header, context, git, weather, memory

# ── ANSI ────────────────────────────────────────────────────────────────────
RST='\033[0m'
B='\033[1m'
DIM='\033[2m'
CY='\033[36m'
BCY='\033[96m'
YL='\033[33m'
BYL='\033[93m'
MG='\033[35m'
GR='\033[32m'
RD='\033[31m'
WH='\033[97m'
GY='\033[90m'
BL='\033[34m'

# ── Read JSON from stdin ────────────────────────────────────────────────────
input=$(cat)
cwd=$(echo "$input" | jq -r '.workspace.current_dir // empty')
model=$(echo "$input" | jq -r '.model.display_name // "—"')
used=$(echo "$input" | jq -r '.context_window.used_percentage // "0"')
turns=$(echo "$input" | jq -r '.session.turns // "0"')
[ -z "$cwd" ] && cwd="$PWD"

# ── Weather cache (10-min TTL) ──────────────────────────────────────────────
CACHE="/tmp/claude_statusline_weather"
TTL=600

_stale=0
if [ ! -f "$CACHE" ]; then
  _stale=1
else
  _age=$(( $(date +%s) - $(stat -f %m "$CACHE" 2>/dev/null || echo 0) ))
  [ "$_age" -gt "$TTL" ] && _stale=1
fi

if [ "$_stale" -eq 1 ]; then
  _ip=$(curl -s --max-time 3 ipinfo.io/json 2>/dev/null)
  _city=$(echo "$_ip" | jq -r '.city // empty' 2>/dev/null)
  _region=$(echo "$_ip" | jq -r '.region // empty' 2>/dev/null)

  if [ -n "$_city" ]; then
    _wj=$(curl -s --max-time 5 "wttr.in/${_city}?format=j1" 2>/dev/null)
    if echo "$_wj" | jq -e '.current_condition' >/dev/null 2>&1; then
      _ct=$(echo "$_wj" | jq -r '.current_condition[0].temp_F // empty')
      _cd=$(echo "$_wj" | jq -r '.current_condition[0].weatherDesc[0].value // empty')
      _hi=$(echo "$_wj" | jq -r '.weather[0].maxtempF // empty')
      _lo=$(echo "$_wj" | jq -r '.weather[0].mintempF // empty')
      printf '%s\n%s\n%s\n%s\n%s\n%s\n' "$_city" "$_region" "$_ct" "$_cd" "$_hi" "$_lo" > "$CACHE"
    else
      printf '%s\n%s\n\nN/A\n\n\n' "$_city" "$_region" > "$CACHE"
    fi
  else
    printf '\n\n\nN/A\n\n\n' > "$CACHE"
  fi
fi

_w_city=$(sed -n '1p' "$CACHE" 2>/dev/null)
_w_region=$(sed -n '2p' "$CACHE" 2>/dev/null)
_w_temp=$(sed -n '3p' "$CACHE" 2>/dev/null)
_w_desc=$(sed -n '4p' "$CACHE" 2>/dev/null)
_w_hi=$(sed -n '5p' "$CACHE" 2>/dev/null)
_w_lo=$(sed -n '6p' "$CACHE" 2>/dev/null)

# Weather emoji
_wx_emoji() {
  local d=$(echo "$1" | tr '[:upper:]' '[:lower:]')
  case "$d" in
    *thunder*|*storm*|*lightning*) echo "⛈️ " ;;
    *snow*|*blizzard*|*sleet*)     echo "❄️ " ;;
    *rain*|*drizzle*|*shower*)     echo "🌧️" ;;
    *cloud*|*overcast*)            echo "☁️ " ;;
    *fog*|*mist*|*haze*)           echo "🌫️" ;;
    *sunny*|*clear*)               echo "☀️ " ;;
    *partly*)                      echo "⛅" ;;
    *)                             echo "🌤️" ;;
  esac
}

# ── Git info ────────────────────────────────────────────────────────────────
_branch="—"
_commit_age="—"
_mod=0
_untracked=0
_ahead=0
_behind=0
_staged=0

if git -C "$cwd" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  _branch=$(git -C "$cwd" symbolic-ref --short HEAD 2>/dev/null || echo "detached")

  _raw_age=$(git -C "$cwd" log -1 --format="%cr" 2>/dev/null)
  _commit_age=$(echo "$_raw_age" | sed \
    -e 's/ seconds\{0,1\} ago/s/' \
    -e 's/ minutes\{0,1\} ago/m/' \
    -e 's/ hours\{0,1\} ago/h/' \
    -e 's/ days\{0,1\} ago/d/' \
    -e 's/ weeks\{0,1\} ago/w/' \
    -e 's/ months\{0,1\} ago/mo/' \
    -e 's/ years\{0,1\} ago/y/')

  _mod=$(git -C "$cwd" diff --name-only 2>/dev/null | wc -l | tr -d ' ')
  _staged=$(git -C "$cwd" diff --cached --name-only 2>/dev/null | wc -l | tr -d ' ')
  _untracked=$(git -C "$cwd" ls-files --others --exclude-standard "$cwd" 2>/dev/null | wc -l | tr -d ' ')
  _ahead=$(git -C "$cwd" rev-list --count HEAD@{upstream}..HEAD 2>/dev/null || echo 0)
  _behind=$(git -C "$cwd" rev-list --count HEAD..HEAD@{upstream} 2>/dev/null || echo 0)
fi

# ── Context bar ─────────────────────────────────────────────────────────────
_pct=0
[ -n "$used" ] && [ "$used" != "null" ] && _pct=$(printf "%.0f" "$used" 2>/dev/null || echo 0)

BAR_W=30
_filled=$(( BAR_W * _pct / 100 ))
[ "$_filled" -gt "$BAR_W" ] && _filled=$BAR_W
_empty=$(( BAR_W - _filled ))

if [ "$_pct" -lt 50 ]; then
  _bc="${GR}"
elif [ "$_pct" -lt 80 ]; then
  _bc="${YL}"
else
  _bc="${RD}"
fi

_bar_f=""
_bar_e=""
[ "$_filled" -gt 0 ] && _bar_f=$(printf '%0.s█' $(seq 1 "$_filled"))
[ "$_empty" -gt 0 ] && _bar_e=$(printf '%0.s░' $(seq 1 "$_empty"))

# ── Memory stats ────────────────────────────────────────────────────────────
_mem_dir="$HOME/.claude/projects/-Users-todddube-Documents-Github-macOSMCP/memory"
_mem_files=0
_mem_lines=0

if [ -d "$_mem_dir" ]; then
  _mem_files=$(find "$_mem_dir" -name "*.md" -maxdepth 1 2>/dev/null | wc -l | tr -d ' ')
  _mem_lines=$(cat "$_mem_dir"/*.md 2>/dev/null | wc -l | tr -d ' ')
fi

# CC version
_cc_ver=$(claude --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
[ -z "$_cc_ver" ] && _cc_ver="—"

# ── LINE 1 ─ Header ────────────────────────────────────────────────────────
_time=$(date "+%a %b %-d · %H:%M")
_emoji=$(_wx_emoji "$_w_desc")

_loc=""
[ -n "$_w_city" ] && _loc="${_w_city}"
[ -n "$_w_region" ] && _loc="${_loc}, ${_w_region}"

_wx_str=""
if [ -n "$_w_temp" ]; then
  _wx_str="${_w_temp}°F ${_w_desc}"
  [ -n "$_w_hi" ] && [ -n "$_w_lo" ] && _wx_str="${_wx_str}  ↑${_w_hi}° ↓${_w_lo}°"
fi

printf "${B}${BCY}━━━ CLAUDE CODE ━━━${RST}  ${GY}${_time}${RST}\n"

# ── LINE 2 ─ Model + Context ───────────────────────────────────────────────
printf "  ${CY}🤖 ${WH}${model}${RST}  ${GY}·${RST}  ${CY}🔧 ${WH}CC ${_cc_ver}${RST}  ${GY}·${RST}  ${CY}💬 ${WH}${turns} turns${RST}  ${GY}·${RST}  📊 ${_bc}${_bar_f}${GY}${_bar_e}${RST} ${BYL}${_pct}%%${RST}\n"

# ── LINE 3 ─ Weather + Location ────────────────────────────────────────────
if [ -n "$_w_temp" ]; then
  printf "  ${_emoji}${YL}${_wx_str}${RST}  ${GY}·${RST}  ${BL}📍 ${WH}${_loc}${RST}\n"
fi

# ── LINE 4 ─ Git ───────────────────────────────────────────────────────────
_dir=$(basename "$cwd")

_sync=""
[ "$_ahead" -gt 0 ] && _sync="${GR}↑${_ahead}${RST}"
[ "$_behind" -gt 0 ] && _sync="${_sync}${RD}↓${_behind}${RST}"
[ -z "$_sync" ] && _sync="${GR}✓${RST}"

_changes=""
[ "$_mod" -gt 0 ] && _changes="${YL}~${_mod}${RST}"
[ "$_staged" -gt 0 ] && _changes="${_changes} ${GR}+${_staged}${RST}"
[ "$_untracked" -gt 0 ] && _changes="${_changes} ${GY}?${_untracked}${RST}"
[ -z "$_changes" ] && _changes="${GR}clean${RST}"

printf "  ${BYL}📁 ${WH}${_dir}${RST}  ${GY}·${RST}  ${MG}🌿 ${_branch}${RST}  ${GY}·${RST}  ⏱️  ${WH}${_commit_age}${RST}  ${GY}·${RST}  ${_changes}  ${GY}·${RST}  🔄 ${_sync}\n"

# ── LINE 5 ─ Memory ───────────────────────────────────────────────────────
printf "  ${CY}🧠 ${DIM}Memory:${RST} ${WH}${_mem_files}${RST}${DIM} files${RST} ${GY}/${RST} ${WH}${_mem_lines}${RST}${DIM} lines${RST}\n"
