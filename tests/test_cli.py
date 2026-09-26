"""Tests for the command-line entry point."""

import tempfile
import unittest
from pathlib import Path

from flyin.__main__ import main


class CommandLineTests(unittest.TestCase):
    """Exercise the public command-line interface."""

    def test_main_runs_a_valid_map(self) -> None:
        """The public command runs a complete simulation."""
        content = "\n".join(
            ["nb_drones: 1", "start_hub: s 0 0", "end_hub: e 1 0", "connection: s-e"]
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "map.txt"
            path.write_text(content, encoding="utf-8")
            self.assertEqual(main([str(path)]), 0)
