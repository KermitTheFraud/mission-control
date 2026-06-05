:<<"___BAT___"
@echo off
REM ===== Windows: start the server detached (windowless), then self-close =====
start "" pythonw "%~dp0src\serve.py" --detached
echo mission-control is running at http://127.0.0.1:8787
echo It runs in the background - stop it from the dashboard's Kill button.
echo Logs: server.log
echo.
echo Closing this window in 3 seconds...
timeout /t 3 /nobreak >nul
exit /b
___BAT___
# ===== macOS / Linux / Omarchy: start detached, log to server.log, return =====
ROOT="$(cd "$(dirname "$0")" && pwd)"
nohup python3 "$ROOT/src/serve.py" --detached >/dev/null 2>&1 &
echo "mission-control is running at http://127.0.0.1:8787 (logs: server.log)"
exit 0
