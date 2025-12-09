"""Test configuration.

Ensure the project root is importable so tests can import the local package
without installing it first.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if SRC.exists():
    sys.path.insert(0, str(SRC))
elif str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
