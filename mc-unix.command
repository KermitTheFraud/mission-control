#!/bin/sh
# mission-control launcher (macOS .command double-click / Linux / Omarchy).
# Probes :8787; starts serve.py detached if free. serve.py opens the browser and
# no-ops if a server already owns the port, so launching again just reopens the tab.
#
# One-time niceties (optional):
#   - Drag this file onto the Dock (documents side) for a one-click icon;
#     set a custom icon via Finder > Get Info > paste an image onto the icon.
#   - Terminal > Settings > Profiles > Shell > "When the shell exits: Close if the
#     shell exited cleanly" lets the window close itself.
ROOT="$(cd "$(dirname "$0")" && pwd)"

# Bigger window (rows;cols) so the startup output is visible (Terminal.app / xterm).
printf '\033[8;40;100t'

echo "mission-control"
echo "------------------------------------------------------------"
python3 "$ROOT/src/serve.py" --osinfo 2>/dev/null

# Already running? Don't start a second server or open a second tab.
if curl -s -m 2 http://127.0.0.1:8787/api/status 2>/dev/null | grep -q mission-control; then
  echo "Already running at http://127.0.0.1:8787"
  echo "Use the tab you already have open."
  echo ""
  printf "Press any key to close... "
  read -n1 -r _ 2>/dev/null || read -r _
  echo ""
  exit 0
fi

echo "> python3 src/serve.py --detached"
nohup python3 "$ROOT/src/serve.py" --detached >/dev/null 2>&1 &
echo ""
echo "Running at http://127.0.0.1:8787  (logs: logs/server.log)"

# macOS: count down, then close this Terminal window (the server is detached).
if [ "$(uname)" = "Darwin" ]; then
  printf '\nAutoclose in 3..\n'; sleep 1
  printf 'Autoclose in 2..\n'; sleep 1
  printf 'Autoclose in 1..\n'; sleep 1
  osascript -e 'tell application "Terminal" to close (first window whose frontmost is true)' >/dev/null 2>&1 &
fi
exit 0
