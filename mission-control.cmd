:<<"___BAT___"
@echo off
REM ===== Windows: bigger window, probe first, else start detached + countdown-close =====
mode con: cols=100 lines=35 >nul 2>&1
chcp 65001 >nul 2>&1
echo mission-control
echo ------------------------------------------------------------
python "%~dp0src\serve.py" --osinfo 2>nul
REM Already running? Don't start a second server or open a second tab.
curl -s -m 2 http://127.0.0.1:8787/api/status 2>nul | find "mission-control" >nul 2>&1
if %errorlevel%==0 (
  echo Already running at http://127.0.0.1:8787
  echo Use the tab you already have open.
  echo.
  pause
  exit
)
echo ^> pythonw src\serve.py --detached
start "" pythonw "%~dp0src\serve.py" --detached
echo.
echo Running at http://127.0.0.1:8787
echo Background process - stop it with the dashboard's "Kill ^& Close".
echo Logs: logs\server.log
echo.
echo Autoclose in 3..
timeout /t 1 /nobreak >nul
echo 2..
timeout /t 1 /nobreak >nul
echo 1..
timeout /t 1 /nobreak >nul
exit
___BAT___
# ===== macOS / Linux / Omarchy: probe first, else start detached + return =====
ROOT="$(cd "$(dirname "$0")" && pwd)"
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
exit 0
