"""Local graph algorithms used by the scheduler."""

from __future__ import annotations

import heapq

from flyin.domain import Connection, Graph, ZoneType
from flyin.errors import UnsolvableMapError


class RouteFinder:
    """Compute destination costs without external graph libraries."""

    def __init__(self, graph: Graph) -> None:
        """Bind the route finder to one immutable-in-practice graph."""
        self.graph = graph
        self._distances: dict[str, int] | None = None

    def distances_to_end(self) -> dict[str, int]:
        """Return cached minimum travel costs to the end, excluding blocked zones."""
        if self._distances is not None:
            return self._distances
        if self.graph.end_name is None:
            raise UnsolvableMapError("map has no end zone")
        distances: dict[str, int] = {self.graph.end_name: 0}
        pending: list[tuple[int, str]] = [(0, self.graph.end_name)]
        while pending:
            distance, current = heapq.heappop(pending)
            if distance != distances[current]:
                continue
            for connection in self.graph.neighbors(current):
                previous = connection.other(current)
                previous_zone = self.graph.zones[previous]
                current_zone = self.graph.zones[current]
                if previous_zone.zone_type is ZoneType.BLOCKED:
                    continue
                candidate = distance + current_zone.arrival_cost
                if candidate < distances.get(previous, float("inf")):
                    distances[previous] = candidate
                    heapq.heappush(pending, (candidate, previous))
        self._distances = distances
        return distances

    def assert_solvable(self) -> None:
        """Raise a distinct error when start cannot reach end."""
        if self.graph.start_name is None or self.graph.start_name not in self.distances_to_end():
            raise UnsolvableMapError("no route connects start_hub to end_hub")

    def ordered_choices(self, zone_name: str) -> tuple[Connection, ...]:
        """Return useful outgoing links ordered by remaining route cost and priority."""
        distances = self.distances_to_end()
        choices: list[tuple[int, int, str, Connection]] = []
        for connection in self.graph.neighbors(zone_name):
            destination = connection.other(zone_name)
            zone = self.graph.zones[destination]
            if zone.zone_type is ZoneType.BLOCKED or destination not in distances:
                continue
            priority = 0 if zone.zone_type is ZoneType.PRIORITY else 1
            choices.append((zone.arrival_cost + distances[destination], priority, destination, connection))
        return tuple(item[3] for item in sorted(choices))

    def preferred_choices(self, zone_name: str) -> tuple[Connection, ...]:
        """Return equally best next hops, preserving priority-zone preference."""
        choices = self.ordered_choices(zone_name)
        if not choices:
            return ()
        distances = self.distances_to_end()
        first = choices[0]
        first_zone = self.graph.zones[first.other(zone_name)]
        best_cost = first_zone.arrival_cost + distances[first_zone.name]
        return tuple(
            connection
            for connection in choices
            if self.graph.zones[connection.other(zone_name)].arrival_cost
            + distances[connection.other(zone_name)]
            == best_cost
        )
