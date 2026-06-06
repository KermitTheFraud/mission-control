@echo off
REM mission-control launcher (Windows). Probes :8787; starts serve.py detached if free.
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
echo Autoclose in 2..
timeout /t 1 /nobreak >nul
echo Autoclose in 1..
timeout /t 1 /nobreak >nul
exit
