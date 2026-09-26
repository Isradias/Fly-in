"""Atomic discrete-turn simulation with capacity-aware movements."""

from __future__ import annotations

from dataclasses import dataclass

from flyin.domain import Connection, Drone, DroneState, Graph, ZoneType
from flyin.errors import SimulationError
from flyin.routing import RouteFinder


@dataclass(frozen=True, slots=True)
class Turn:
    """One rendered simulation turn."""

    movements: tuple[str, ...]

    def render(self) -> str:
        """Render the mandatory space-separated output line."""
        return " ".join(self.movements)


class Simulator:
    """Schedule drones with atomic decisions based on each turn's initial state."""

    def __init__(self, graph: Graph, drone_count: int) -> None:
        """Create drones at the start zone and validate reachability."""
        if graph.start_name is None or graph.end_name is None:
            raise SimulationError("graph needs start and end zones")
        self.graph = graph
        self.routes = RouteFinder(graph)
        self.routes.assert_solvable()
        self.drones = [Drone(identifier, zone_name=graph.start_name) for identifier in range(1, drone_count + 1)]

    def run(self) -> list[Turn]:
        """Run until every drone reaches the end or no valid progress is possible."""
        turns: list[Turn] = []
        max_turns = max(100, len(self.drones) * max(1, len(self.graph.zones)) * 8)
        while any(drone.state is not DroneState.DELIVERED for drone in self.drones):
            turn = self.step()
            if not turn.movements:
                raise SimulationError("scheduler made no progress; map may be deadlocked")
            turns.append(turn)
            if len(turns) > max_turns:
                raise SimulationError("simulation exceeded its safe progress limit")
        return turns

    def step(self) -> Turn:
        """Apply one simultaneous turn and return only movements that occurred."""
        forced = [drone for drone in self.drones if drone.state is DroneState.IN_TRANSIT]
        proposals: dict[int, Connection] = {}
        for drone in self.drones:
            if drone.state is not DroneState.AT_ZONE or drone.zone_name is None:
                continue
            choices = self.routes.ordered_choices(drone.zone_name)
            if choices:
                proposals[drone.identifier] = choices[0]
        selected = self._select_moves(proposals, forced)
        movements: list[str] = []
        for drone in forced:
            if drone.destination is None:
                raise SimulationError("in-transit drone has no destination")
            delivered = drone.destination == self.graph.end_name
            drone.arrive(drone.destination, delivered)
            movements.append(f"D{drone.identifier}-{self.graph.end_name if delivered else drone.zone_name}")
        for drone in self.drones:
            connection = selected.get(drone.identifier)
            if connection is None or drone.zone_name is None:
                continue
            destination = connection.other(drone.zone_name)
            destination_zone = self.graph.zones[destination]
            if destination_zone.zone_type is ZoneType.RESTRICTED:
                drone.begin_transit(connection, destination)
                movements.append(f"D{drone.identifier}-{connection.name}")
            else:
                drone.arrive(destination, destination == self.graph.end_name)
                movements.append(f"D{drone.identifier}-{destination}")
        return Turn(tuple(movements))

    def _select_moves(
        self,
        proposals: dict[int, Connection],
        forced: list[Drone],
    ) -> dict[int, Connection]:
        """Remove lower-priority proposals until final occupancies are valid.

        Departures are subtracted before arrivals, which implements same-turn reuse.
        """
        selected = dict(proposals)
        while True:
            invalid = self._first_invalid(selected, forced)
            if invalid is None:
                return selected
            candidates = [
                drone_id
                for drone_id, connection in selected.items()
                if connection.other(self._drone(drone_id).zone_name or "") == invalid
            ]
            if not candidates:
                return selected
            del selected[max(candidates)]

    def _first_invalid(
        self,
        selected: dict[int, Connection],
        forced: list[Drone],
    ) -> str | None:
        """Return a zone whose final occupancy would exceed capacity, if any."""
        occupancy = {
            name: sum(
                drone.state is DroneState.AT_ZONE and drone.zone_name == name
                for drone in self.drones
            )
            for name in self.graph.zones
        }
        for drone_id, connection in selected.items():
            drone = self._drone(drone_id)
            if drone.zone_name is None:
                continue
            occupancy[drone.zone_name] -= 1
            occupancy[connection.other(drone.zone_name)] += 1
        for drone in forced:
            if drone.destination is not None:
                occupancy[drone.destination] += 1
        for name, count in occupancy.items():
            capacity = self.graph.zones[name].capacity
            if capacity is not None and count > capacity:
                return name
        return self._invalid_connection(selected, forced)

    def _invalid_connection(
        self,
        selected: dict[int, Connection],
        forced: list[Drone],
    ) -> str | None:
        """Return one overloaded link key, or ``None`` when all are valid."""
        usage: dict[frozenset[str], int] = {}
        for connection in selected.values():
            usage[connection.key] = usage.get(connection.key, 0) + 1
        for key, count in usage.items():
            if count > self.graph.connections[key].max_capacity:
                return next(iter(key))
        return None

    def _drone(self, identifier: int) -> Drone:
        """Return the drone with ``identifier``."""
        return self.drones[identifier - 1]
