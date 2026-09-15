"""Tests for drone and zone parsing."""

import unittest

from flyin.domain import ZoneType
from flyin.errors import ParseError
from flyin.parser import MapParser


class ZoneParserTests(unittest.TestCase):
    """Cover declarations that do not need links yet."""

    def test_parses_terminals_and_metadata(self) -> None:
        """Zones retain their optional metadata and terminal roles."""
        definition = MapParser().parse_lines(
            [
                "# a comment\n",
                "nb_drones: 3\n",
                "start_hub: start 0 0 [color=green max_drones=9]\n",
                "hub: gate 1 -2 [zone=restricted color=red max_drones=2]\n",
                "end_hub: end 2 0\n",
            ]
        )
        self.assertEqual(definition.drone_count, 3)
        self.assertTrue(definition.graph.zones["start"].is_start)
        self.assertEqual(definition.graph.zones["gate"].zone_type, ZoneType.RESTRICTED)
        self.assertEqual(definition.graph.zones["gate"].max_drones, 2)

    def test_first_meaningful_line_must_be_drone_count(self) -> None:
        """A map must begin with the prescribed count declaration."""
        with self.assertRaisesRegex(ParseError, "line 2"):
            MapParser().parse_lines(["# note\n", "hub: a 0 0\n"])

    def test_invalid_zone_type_has_line_number(self) -> None:
        """Semantic metadata errors are understandable to map authors."""
        with self.assertRaisesRegex(ParseError, "line 3: invalid zone type"):
            MapParser().parse_lines(
                ["nb_drones: 1\n", "start_hub: a 0 0\n", "hub: b 1 0 [zone=x]\n"]
            )

    def test_duplicate_zone_is_rejected(self) -> None:
        """Zone names must be unique."""
        with self.assertRaisesRegex(ParseError, "line 3: duplicate zone"):
            MapParser().parse_lines(
                ["nb_drones: 1\n", "start_hub: a 0 0\n", "hub: a 1 0\n"]
            )
