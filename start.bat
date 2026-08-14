@echo off
REM Launch the GL rating engine UI (Stage 6 interface).
REM Usage:  start.bat            -- serves on http://127.0.0.1:8765 and opens a browser
REM         start.bat 9000       -- serves on port 9000
REM         start.bat --no-browser
setlocal
cd /d "%~dp0"

REM Prefer the Windows launcher, fall back to python on PATH.
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

%PY% app.py %*
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" pause
exit /b %RC%
