"""Module entry point for ``python -m conways_physics``."""

from __future__ import annotations

from .app import ConwaysPhysics


def main() -> None:
    """Run the Textual application."""
    ConwaysPhysics().run()


if __name__ == "__main__":
    main()
