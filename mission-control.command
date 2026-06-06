#!/bin/sh
# Double-clickable launcher for mission-control (macOS .command / Linux).
#
# Delegates to mission-control.cmd to start the server, then (macOS) counts down
# and closes the Terminal window. serve.py opens the browser itself and no-ops if
# a server already owns the port, so double-clicking again just reopens the tab.
#
# One-time niceties (optional):
#   - Drag this file onto the Dock (right/documents side) for a one-click icon;
#     set a custom icon via Finder > Get Info > paste an image onto the icon.
#   - If the window ever prompts before closing, set Terminal > Settings >
#     Profiles > Shell > "When the shell exits: Close if the shell exited cleanly".
DIR="$(cd "$(dirname "$0")" && pwd)"

# Bigger window (rows;cols) so all the startup output is visible (Terminal.app / xterm).
printf '\033[8;40;100t'

sh "$DIR/mission-control.cmd"

# macOS: count down, then close this Terminal window. The server is detached, so
# nothing is left running here. Other OSes: just exit (auto-closing a terminal is
# emulator-specific; the window stays unless your terminal closes on exit).
if [ "$(uname)" = "Darwin" ]; then
  printf '\nAutoclose in 3..\n'; sleep 1
  printf '2..\n'; sleep 1
  printf '1..\n'; sleep 1
  osascript -e 'tell application "Terminal" to close (first window whose frontmost is true)' >/dev/null 2>&1 &
fi
exit 0
