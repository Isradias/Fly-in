"""Command-line entry point for Fly-in."""

from __future__ import annotations

import argparse
from collections.abc import Sequence


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="flyin",
        description="Route drones through a constrained zone network.",
    )
    parser.add_argument("map_file", help="Path to a Fly-in map file.")
    parser.add_argument(
        "--visual",
        action="store_true",
        help="Render an auxiliary terminal visualization on standard error.",
    )
    return parser


def main(arguments: Sequence[str] | None = None) -> int:
    """Run the Fly-in command-line application.

    Args:
        arguments: Optional command-line arguments excluding the program name.

    Returns:
        Process exit status.
    """
    parser = build_parser()
    parser.parse_args(arguments)
    print("Fly-in is being initialized; routing is not available yet.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
