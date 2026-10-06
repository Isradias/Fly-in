"""Regression tests for core simultaneous movement rules."""

import unittest

from flyin.parser import MapParser
from flyin.simulation import Simulator


class SimulationTests(unittest.TestCase):
    """Exercise capacity release and restricted transit."""

    def test_single_file_column_advances_each_turn(self) -> None:
        """A vacated capacity-one zone is reusable in the same turn."""
        definition = MapParser().parse_lines(
            ["nb_drones: 2\n", "start_hub: s 0 0\n", "hub: a 1 0\n", "end_hub: e 2 0\n", "connection: s-a\n", "connection: a-e\n"]
        )
        turns = Simulator(definition.graph, definition.drone_count).run()
        self.assertEqual([turn.render() for turn in turns], ["D1-a", "D1-e D2-a", "D2-e"])

    def test_restricted_link_is_reported_before_arrival(self) -> None:
        """A restricted destination keeps the drone on the connection for one turn."""
        definition = MapParser().parse_lines(
            ["nb_drones: 1\n", "start_hub: s 0 0\n", "hub: r 1 0 [zone=restricted]\n", "end_hub: e 2 0\n", "connection: s-r\n", "connection: r-e\n"]
        )
        turns = Simulator(definition.graph, definition.drone_count).run()
        self.assertEqual([turn.render() for turn in turns], ["D1-s-r", "D1-r", "D1-e"])

    def test_link_capacity_applies_in_either_direction(self) -> None:
        """A capacity-one link cannot pass two simultaneous reverse travelers."""
        definition = MapParser().parse_lines(
            [
                "nb_drones: 2\n",
                "start_hub: s 0 0\n",
                "hub: a 1 0 [max_drones=2]\n",
                "end_hub: e 2 0\n",
                "connection: s-a [max_link_capacity=1]\n",
                "connection: a-e\n",
            ]
        )
        turns = Simulator(definition.graph, definition.drone_count).run()
        self.assertEqual([turn.render() for turn in turns], ["D1-a", "D1-e D2-a", "D2-e"])
