"""Command-line entry point for Fly-in."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
import sys

from flyin.errors import FlyInError
from flyin.parser import MapParser
from flyin.simulation import Simulator
from flyin.visualization import TerminalVisualizer


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
    options = parser.parse_args(arguments)
    try:
        definition = MapParser().parse_file(options.map_file)
        turns = Simulator(definition.graph, definition.drone_count).run()
    except FlyInError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    for turn in turns:
        print(turn.render())
    if options.visual:
        TerminalVisualizer().render(definition.graph, turns)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
