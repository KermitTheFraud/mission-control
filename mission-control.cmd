:<<"___BAT___"
@echo off
REM ===== Windows: bigger window, show the command, start detached, countdown-close =====
mode con: cols=100 lines=35 >nul 2>&1
echo mission-control
echo ------------------------------------------------------------
echo ^> pythonw src\serve.py --detached
start "" pythonw "%~dp0src\serve.py" --detached
echo.
echo Running at http://127.0.0.1:8787
echo Background process - stop it with the dashboard's "Kill ^& Close".
echo Logs: server.log
echo.
echo Autoclose in 3..
timeout /t 1 /nobreak >nul
echo 2..
timeout /t 1 /nobreak >nul
echo 1..
timeout /t 1 /nobreak >nul
exit
___BAT___
# ===== macOS / Linux / Omarchy: show the command, start detached, return =====
ROOT="$(cd "$(dirname "$0")" && pwd)"
echo "mission-control"
echo "------------------------------------------------------------"
echo "> python3 src/serve.py --detached"
nohup python3 "$ROOT/src/serve.py" --detached >/dev/null 2>&1 &
echo ""
echo "Running at http://127.0.0.1:8787  (logs: server.log)"
exit 0
