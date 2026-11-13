#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ]; then
  python3 -m venv .venv
fi
if ! .venv/bin/python -c 'import flask, openpyxl, docx, pypdf, waitress' 2>/dev/null; then
  .venv/bin/python -m pip install -r requirements.txt
fi
exec .venv/bin/python scripts/run.py "$@"
