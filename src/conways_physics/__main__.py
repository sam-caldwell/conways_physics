"""Module entry point for ``python -m conways_physics``."""

from __future__ import annotations

from .app import ConwaysApp


def main() -> None:
    """Run the Textual application."""
    ConwaysApp().run()


if __name__ == "__main__":
    main()
