#!/bin/bash
set -euo pipefail
if [ -d .venv ]; then
  source .venv/bin/activate
fi
pytest tests_extra -v
