"""Tests for cost-aware route selection."""

import unittest

from flyin.parser import MapParser
from flyin.routing import RouteFinder
from flyin.errors import UnsolvableMapError


class RoutingTests(unittest.TestCase):
    """Verify ties can be distributed while traps are avoided."""

    def test_equal_cost_fork_exposes_both_choices(self) -> None:
        """Equivalent exits remain available to the scheduler."""
        definition = MapParser().parse_lines(
            [
                "nb_drones: 1\n",
                "start_hub: s 0 0\n",
                "hub: a 1 1\n",
                "hub: b 1 -1\n",
                "end_hub: e 2 0\n",
                "connection: s-a\n",
                "connection: s-b\n",
                "connection: a-e\n",
                "connection: b-e\n",
            ]
        )
        choices = RouteFinder(definition.graph).preferred_choices("s")
        self.assertEqual({link.other("s") for link in choices}, {"a", "b"})

    def test_disconnected_map_is_not_a_parse_error(self) -> None:
        """Reachability is validated after syntactic parsing succeeds."""
        definition = MapParser().parse_lines(
            ["nb_drones: 1\n", "start_hub: s 0 0\n", "end_hub: e 1 0\n"]
        )
        with self.assertRaises(UnsolvableMapError):
            RouteFinder(definition.graph).assert_solvable()
