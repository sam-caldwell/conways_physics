"""Conways Physics Python package scaffold (src-layout).

This is an initial scaffold to enable pytest discovery and coverage. The real simulation will
live in additional modules as we port the C++ implementation to Python/Textual.
"""

from __future__ import annotations

__all__ = ["__version__", "get_version"]

__version__ = "0.0.0"


def get_version() -> str:
    """Return the package version string."""
    return __version__

