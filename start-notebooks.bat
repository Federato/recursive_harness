@echo off
REM Open the engine notebooks in JupyterLab.
REM   start-notebooks.bat            -- opens the notebooks folder in a browser
REM   start-notebooks.bat 00         -- opens straight into 00-index.ipynb
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

REM JupyterLab is a notebook-only dependency; the engine itself needs nothing.
%PY% -c "import jupyterlab" >nul 2>&1
if errorlevel 1 (
  echo JupyterLab is not installed. Installing it now from notebooks\requirements.txt ...
  %PY% -m pip install -r notebooks\requirements.txt
  if errorlevel 1 (
    echo.
    echo Install failed. Run this by hand:
    echo     %PY% -m pip install -r notebooks\requirements.txt
    pause
    exit /b 1
  )
)

if not "%GL_ERC_ROOT%"=="" (
  echo Using GL_ERC_ROOT=%GL_ERC_ROOT%
) else (
  echo GL_ERC_ROOT is not set; the notebooks will use the default corpus path.
)
echo.
echo Cells open blank because outputs are stripped before commit -- use Run All.
echo Ctrl-C twice in this window to stop the server.
echo.

if "%~1"=="" goto :openfolder

REM Open the notebook whose filename starts with the number given.
set "TARGET="
for %%F in ("notebooks\%~1*.ipynb") do if not defined TARGET set "TARGET=%%~nxF"
if not defined TARGET goto :nomatch
%PY% -m jupyter lab "notebooks/%TARGET%"
goto :done

:openfolder
%PY% -m jupyter lab notebooks
goto :done

:nomatch
echo No notebook starts with "%~1". Available:
dir /b notebooks\*.ipynb
pause
exit /b 1

:done
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" pause
exit /b %RC%
