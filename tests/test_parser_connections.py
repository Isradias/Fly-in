"""Tests for connection parsing and semantic link validation."""

import unittest

from flyin.errors import ParseError
from flyin.parser import MapParser


class ConnectionParserTests(unittest.TestCase):
    """Verify the bidirectional link grammar."""

    def test_parses_connection_capacity(self) -> None:
        """Connection metadata sets traversal capacity."""
        definition = MapParser().parse_lines(
            [
                "nb_drones: 2\n",
                "start_hub: start 0 0\n",
                "end_hub: end 1 0\n",
                "connection: start-end [max_link_capacity=2]\n",
            ]
        )
        connection = definition.graph.connection_between("start", "end")
        self.assertEqual(connection.max_capacity, 2)

    def test_connection_requires_existing_endpoints(self) -> None:
        """Forward references are rejected with their source line."""
        with self.assertRaisesRegex(ParseError, "line 3: connection references"):
            MapParser().parse_lines(
                [
                    "nb_drones: 1\n",
                    "start_hub: start 0 0\n",
                    "connection: start-end\n",
                    "end_hub: end 1 0\n",
                ]
            )

    def test_reversed_duplicate_connection_is_rejected(self) -> None:
        """A link cannot be redeclared in its opposite orientation."""
        with self.assertRaisesRegex(ParseError, "line 5: duplicate connection"):
            MapParser().parse_lines(
                [
                    "nb_drones: 1\n",
                    "start_hub: start 0 0\n",
                    "end_hub: end 1 0\n",
                    "connection: start-end\n",
                    "connection: end-start\n",
                ]
            )

    def test_rejects_unknown_connection_metadata(self) -> None:
        """Only the documented link capacity key is accepted."""
        with self.assertRaisesRegex(ParseError, "line 4: invalid connection metadata"):
            MapParser().parse_lines(
                [
                    "nb_drones: 1\n",
                    "start_hub: start 0 0\n",
                    "end_hub: end 1 0\n",
                    "connection: start-end [color=blue]\n",
                ]
            )
