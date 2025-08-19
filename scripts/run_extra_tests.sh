#!/usr/bin/env bash
set -euo pipefail
if [ -f ".venv/bin/activate" ]; then
  source .venv/bin/activate
fi
pytest -q tests_extra
