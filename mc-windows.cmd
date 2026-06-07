@echo off
REM mission-control launcher (Windows). Preflight checks, then start serve.py detached if :8787 is free.
mode con: cols=100 lines=35 >nul 2>&1
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

echo.
echo   mission-control
echo   ================================================
echo.

REM --- system identified (standout) ---
set "OSINFO="
for /f "delims=" %%i in ('python "%~dp0src\serve.py" --osinfo 2^>nul') do set "OSINFO=%%i"
if not defined OSINFO set "OSINFO=unknown system"
echo   [ SYSTEM ]   !OSINFO!
echo.

REM --- preflight checks (standout) ---
echo   PREFLIGHT
set "FAIL=0"
where python >nul 2>&1
if %errorlevel%==0 (
  for /f "delims=" %%v in ('python --version 2^>^&1') do echo   [ OK ]   python   %%v
) else (
  echo   [FAIL]   python - not found on PATH
  set "FAIL=1"
)
where git >nul 2>&1
if %errorlevel%==0 (
  for /f "delims=" %%v in ('git --version 2^>^&1') do echo   [ OK ]   git      %%v
) else (
  echo   [FAIL]   git - not found on PATH
  set "FAIL=1"
)
if "!FAIL!"=="1" (
  echo.
  echo   Preflight failed - install the missing tool^(s^) and relaunch.
  echo.
  pause
  exit
)

REM --- already running? don't start a second server or open a second tab ---
curl -s -m 2 http://127.0.0.1:8787/api/status 2>nul | find "mission-control" >nul 2>&1
if %errorlevel%==0 (
  echo.
  echo   [ OK ]   already running at http://127.0.0.1:8787 - use the tab you have open.
  echo.
  pause
  exit
)

REM --- start ---
echo.
echo   ^> starting server   pythonw src\serve.py --detached
start "" pythonw "%~dp0src\serve.py" --detached

REM --- success (SWE-style) ---
echo.
echo   [ OK ]   all checks passed - mission-control is online
echo            http://127.0.0.1:8787   (logs: logs\server.log)

REM hold a beat so the success line is read, then count down and close.
timeout /t 1 /nobreak >nul
echo.
echo   Autoclose in 3..
timeout /t 1 /nobreak >nul
echo   2..
timeout /t 1 /nobreak >nul
echo   1..
timeout /t 1 /nobreak >nul
exit
