#!/usr/bin/env bash
set -euo pipefail
if [ -f ".venv/bin/activate" ]; then
  source .venv/bin/activate
fi
PYTHONPATH=backend pytest -q backend/tests/extra
