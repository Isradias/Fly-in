"""Tests for graph and drone domain invariants."""

import unittest

from flyin.domain import Connection, Drone, DroneState, Graph, Zone, ZoneType
from flyin.errors import GraphError


class DomainTests(unittest.TestCase):
    """Verify local domain behavior independently of parsing."""

    def test_terminals_have_unbounded_capacity(self) -> None:
        """Start and end capacities are ignored by design."""
        start = Zone("start", 0, 0, max_drones=1, is_start=True)
        end = Zone("end", 1, 0, max_drones=1, is_end=True)
        self.assertIsNone(start.capacity)
        self.assertIsNone(end.capacity)

    def test_restricted_zone_has_two_turn_arrival_cost(self) -> None:
        """Restricted zones take two turns to enter."""
        zone = Zone("restricted", 0, 0, ZoneType.RESTRICTED)
        self.assertEqual(zone.arrival_cost, 2)

    def test_graph_rejects_reversed_duplicate_connection(self) -> None:
        """Links are bidirectional and therefore orientation-independent."""
        graph = Graph()
        graph.add_zone(Zone("first", 0, 0))
        graph.add_zone(Zone("second", 1, 0))
        graph.add_connection(Connection("first", "second"))
        with self.assertRaises(GraphError):
            graph.add_connection(Connection("second", "first"))

    def test_drone_transit_state_clears_on_arrival(self) -> None:
        """A completed restricted crossing leaves no occupied link state."""
        drone = Drone(1, zone_name="first")
        connection = Connection("first", "second")
        drone.begin_transit(connection, "second")
        self.assertEqual(drone.state, DroneState.IN_TRANSIT)
        self.assertEqual(drone.remaining_turns, 1)
        drone.arrive("second")
        self.assertEqual(drone.state, DroneState.AT_ZONE)
        self.assertEqual(drone.zone_name, "second")
        self.assertIsNone(drone.connection)
