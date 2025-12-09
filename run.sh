#!/usr/bin/env bash
set -Eeuo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="$DIR/venv/bin/python3"

if [[ ! -x "$PY" ]]; then
  PY="$(command -v python3 || true)"
fi

if [[ -z "${PY:-}" ]]; then
  echo "python3 not found. Create a venv and install deps:" >&2
  echo "  python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt" >&2
  exit 1
fi

# Check runtime deps are installed
if ! "$PY" -c 'import textual, rich' >/dev/null 2>&1; then
  echo "Missing dependencies. Install with:" >&2
  echo "  $PY -m pip install -r requirements.txt" >&2
  exit 2
fi

export PYTHONPATH="$DIR/src:${PYTHONPATH:-}"
exec "$PY" -m conways_physics "$@"

