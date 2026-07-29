#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$ROOT_DIR/.venv"
PYTHON_BIN="$VENV_DIR/bin/python"
PIP_BIN="$VENV_DIR/bin/pip"
READY_MARKER="$VENV_DIR/.worldclassics-ready"

if [ ! -x "$PYTHON_BIN" ]; then
  python3 -m venv "$VENV_DIR"
fi

if [ ! -f "$READY_MARKER" ]; then
  "$PIP_BIN" install --upgrade pip setuptools wheel
  "$PIP_BIN" install requests pyyaml
  touch "$READY_MARKER"
fi

cd "$ROOT_DIR"
PYTHONPATH=src "$PYTHON_BIN" -m worldclassicsjp.run "$@"
