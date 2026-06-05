:; exec python3 "$(dirname "$0")/src/serve.py" "$@"
@echo off
REM mission-control launcher - one file, runs on Windows (cmd) and Unix (sh).
REM   Windows: double-click or run `mission-control` here.
REM   macOS / Linux / Omarchy: `./mission-control.cmd`  (or `sh mission-control.cmd`)
python "%~dp0src\serve.py" %*
