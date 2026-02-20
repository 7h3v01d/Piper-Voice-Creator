#!/usr/bin/env bash
set -euo pipefail

python -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
echo "✅ venv ready. Activate with: . .venv/bin/activate"