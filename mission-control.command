#!/bin/sh
# Double-clickable launcher for mission-control (macOS .command / Linux).
#
# macOS Finder binds a double-click on .command files to Terminal; this just
# delegates to the polyglot mission-control.cmd, whose Unix half starts the
# server detached (nohup) and returns immediately. serve.py opens the browser
# itself and no-ops if a server already owns the port, so double-clicking again
# simply reopens the tab.
#
# One-time niceties (optional):
#   - Drag this file onto the Dock (right/documents side) for a one-click icon;
#     set a custom icon via Finder > Get Info > paste an image onto the icon.
#   - To auto-close the leftover Terminal window after launch:
#     Terminal > Settings > Profiles > Shell > "When the shell exits:
#     Close if the shell exited cleanly".
DIR="$(cd "$(dirname "$0")" && pwd)"
exec sh "$DIR/mission-control.cmd"
