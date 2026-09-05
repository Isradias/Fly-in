"""Tests for the command-line entry point."""

import unittest

from flyin.__main__ import main


class CommandLineTests(unittest.TestCase):
    """Exercise the public command-line interface."""

    def test_main_accepts_a_map_path(self) -> None:
        """The initial entry point accepts the required map path."""
        self.assertEqual(main(["example.map"]), 0)
