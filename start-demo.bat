@echo off
REM Demo the filing-packet upload (B-20) on a separate, empty carrier store, so a packet already in the real store
REM can be uploaded again and again. The real store (CARRIERS_ROOT, default C:\FederatoProjects\Carriers) is not used.
REM Usage:  start-demo.bat           -- serves the console on http://127.0.0.1:8766 against the demo store
REM         start-demo.bat --reset   -- empties the demo store and its impact previews first
setlocal
cd /d "%~dp0"
set "DEMO=%~dp0results\demo"
if /i "%~1"=="--reset" (
  if exist "%DEMO%" rmdir /s /q "%DEMO%"
  shift
)
if not exist "%DEMO%\carriers" mkdir "%DEMO%\carriers"
if not exist "%DEMO%\impact" mkdir "%DEMO%\impact"
set "CARRIERS_ROOT=%DEMO%\carriers"
set "IMPACT_DIR=%DEMO%\impact"
set "FILINGS_LOG=%DEMO%\FILINGS-LOG.md"

set "PY="
where py >nul 2>&1 && set "PY=py -3"
if not defined PY (
  where python >nul 2>&1 && set "PY=python"
)
if not defined PY (
  echo Python 3 was not found on PATH. Install it from https://www.python.org/downloads/
  pause
  exit /b 1
)
echo Demo store: %CARRIERS_ROOT%
echo Packets to upload: %~dp0results\packets
%PY% app.py 8766
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" pause
exit /b %RC%
