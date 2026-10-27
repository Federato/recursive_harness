#!/bin/bash
# Launch the GL rating engine UI (Stage 6 interface).
# macOS: double-click this file in Finder, or run ./start.command from a terminal.
# Usage:  ./start.command            -- serves on http://127.0.0.1:8765 and opens a browser
#         ./start.command 9000       -- serves on port 9000
#         ./start.command --no-browser
cd "$(dirname "$0")" || exit 1

if command -v python3 >/dev/null 2>&1; then
  PY=python3
elif command -v python >/dev/null 2>&1; then
  PY=python
else
  echo "Python 3 was not found on PATH. Install it from https://www.python.org/downloads/"
  exit 1
fi

exec "$PY" app.py "$@"
