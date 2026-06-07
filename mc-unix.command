#!/bin/sh
# mission-control launcher (macOS .command double-click / Linux / Omarchy).
# Probes :8787; runs preflight checks; starts serve.py detached if free. serve.py
# opens the browser and no-ops if a server already owns the port, so launching
# again just reopens the tab.
#
# One-time niceties (optional):
#   - Drag this file onto the Dock (documents side) for a one-click icon;
#     set a custom icon via Finder > Get Info > paste an image onto the icon.
#   - Terminal > Settings > Profiles > Shell > "When the shell exits: Close if the
#     shell exited cleanly" lets the window close itself.
ROOT="$(cd "$(dirname "$0")" && pwd)"

# Bigger window (rows;cols) so the startup output is visible (Terminal.app / xterm).
printf '\033[8;40;100t'

# ANSI styling (Terminal.app / xterm).
ESC=$(printf '\033')
B="${ESC}[1m"; D="${ESC}[2m"; RST="${ESC}[0m"
GRN="${ESC}[32m"; CYN="${ESC}[36m"; RED="${ESC}[31m"

printf '\n  %smission-control%s\n' "$B" "$RST"
printf '  %s════════════════════════════════════════════════%s\n\n' "$D" "$RST"

# --- system identified (standout) ---
OS=$(python3 "$ROOT/src/serve.py" --osinfo 2>/dev/null)
[ -z "$OS" ] && OS="unknown system"
printf '  %s SYSTEM %s   %s%s%s\n\n' "${B}${CYN}" "$RST" "$B" "$OS" "$RST"

# --- preflight checks (standout) ---
printf '  %sPREFLIGHT%s\n' "$B" "$RST"
fail=0
if command -v python3 >/dev/null 2>&1; then
  printf '  %s✓%s  python3   %s%s%s\n' "$GRN" "$RST" "$D" "$(python3 --version 2>&1)" "$RST"
else
  printf '  %s✗  python3 — not found on PATH%s\n' "$RED" "$RST"; fail=1
fi
if command -v git >/dev/null 2>&1; then
  printf '  %s✓%s  git       %s%s%s\n' "$GRN" "$RST" "$D" "$(git --version 2>&1)" "$RST"
else
  printf '  %s✗  git — not found on PATH%s\n' "$RED" "$RST"; fail=1
fi

if [ "$fail" = "1" ]; then
  printf '\n  %sPreflight failed — install the missing tool(s) and relaunch.%s\n\n' "$RED" "$RST"
  printf '  Press any key to close... '
  read -n1 -r _ 2>/dev/null || read -r _
  exit 1
fi

# --- already running? don't start a second server or open a second tab ---
if curl -s -m 2 http://127.0.0.1:8787/api/status 2>/dev/null | grep -q mission-control; then
  printf '\n  %s✓ already running%s at %shttp://127.0.0.1:8787%s — use the tab you have open.\n\n' "$GRN" "$RST" "$CYN" "$RST"
  printf '  Press any key to close... '
  read -n1 -r _ 2>/dev/null || read -r _
  exit 0
fi

# --- start ---
printf '\n  %s→ starting server%s   %spython3 src/serve.py --detached%s\n' "$D" "$RST" "$D" "$RST"
nohup python3 "$ROOT/src/serve.py" --detached >/dev/null 2>&1 &

# --- success (SWE-style) ---
printf '\n  %s✓ all checks passed — mission-control is online%s\n' "${B}${GRN}" "$RST"
printf '    %shttp://127.0.0.1:8787%s   %s(logs: logs/server.log)%s\n' "$CYN" "$RST" "$D" "$RST"

# hold a beat so the success line is read, then count down + close (macOS only).
sleep 1
if [ "$(uname)" = "Darwin" ]; then
  printf '\n  %sAutoclose in 3..%s\n' "$D" "$RST"; sleep 1
  printf '  %s2..%s\n' "$D" "$RST"; sleep 1
  printf '  %s1..%s\n' "$D" "$RST"; sleep 1
  osascript -e 'tell application "Terminal" to close (first window whose frontmost is true)' >/dev/null 2>&1 &
fi
exit 0
