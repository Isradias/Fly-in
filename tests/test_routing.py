"""Tests for cost-aware route selection."""

import unittest

from flyin.parser import MapParser
from flyin.routing import RouteFinder


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
