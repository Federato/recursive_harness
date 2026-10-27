#!/bin/bash
# Open the engine notebooks in JupyterLab.
#   ./start-notebooks.command        -- opens the notebooks folder in a browser
#   ./start-notebooks.command 05     -- opens straight into 05-resolve-resolver.ipynb
cd "$(dirname "$0")" || exit 1

if command -v python3 >/dev/null 2>&1; then
  PY=python3
elif command -v python >/dev/null 2>&1; then
  PY=python
else
  echo "Python 3 was not found on PATH. Install it from https://www.python.org/downloads/"
  exit 1
fi

# JupyterLab is a notebook-only dependency; the engine itself needs nothing.
if ! "$PY" -c "import jupyterlab" >/dev/null 2>&1; then
  echo "JupyterLab is not installed. Installing it now from notebooks/requirements.txt ..."
  if ! "$PY" -m pip install -r notebooks/requirements.txt; then
    echo
    echo "Install failed. Run this by hand:"
    echo "    $PY -m pip install -r notebooks/requirements.txt"
    exit 1
  fi
fi

if [ -n "$GL_ERC_ROOT" ]; then
  echo "Using GL_ERC_ROOT=$GL_ERC_ROOT"
else
  echo "GL_ERC_ROOT is not set; the notebooks will use the default corpus path."
fi
echo
echo "Cells open blank because outputs are stripped before commit -- use Run All."
echo "Ctrl-C twice in this window to stop the server."
echo

if [ -z "$1" ]; then
  exec "$PY" -m jupyter lab notebooks
fi

target=$(ls notebooks/"$1"*.ipynb 2>/dev/null | head -1)
if [ -z "$target" ]; then
  echo "No notebook starts with \"$1\". Available:"
  ls -1 notebooks/*.ipynb | xargs -n1 basename
  exit 1
fi
exec "$PY" -m jupyter lab "$target"
