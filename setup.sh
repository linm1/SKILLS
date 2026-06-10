#!/usr/bin/env bash
set -euo pipefail
PY="${PYTHON:-/bin/python3.8}"
if ! command -v "$PY" >/dev/null 2>&1 && [ ! -x "$PY" ]; then
  echo "Python not found at '$PY'. Set PYTHON=/path/to/python3 and re-run." >&2
  exit 1
fi
echo "Creating virtual environment at ./.venv using $PY ..."
"$PY" -m venv .venv
./.venv/bin/python -m pip install --upgrade pip
echo "Installing sas-schema dependencies ..."
./.venv/bin/python -m pip install -r requirements.txt
echo ""
echo "Setup complete."
echo "  - tabview-to-json needs NO dependencies (pure standard library)."
echo "  - sas-schema uses ./.venv  (run: ./.venv/bin/python .github/skills/sas-schema/scripts/run_sas_schema.py --help)"
