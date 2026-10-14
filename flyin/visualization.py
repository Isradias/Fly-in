"""ANSI terminal visualization kept separate from the official output."""

from __future__ import annotations

import sys

from flyin.domain import Connection, Graph
from flyin.simulation import Turn


class TerminalVisualizer:
    """Render every turn with colored movements and zone occupancy states."""

    _ANSI_COLORS = {
        "black": "30",
        "red": "31",
        "green": "32",
        "yellow": "33",
        "blue": "34",
        "magenta": "35",
        "purple": "35",
        "cyan": "36",
        "white": "37",
        "gray": "90",
        "grey": "90",
        "orange": "38;5;208",
    }
    _RESET = "\033[0m"

    def render(self, graph: Graph, drone_count: int, turns: list[Turn]) -> None:
        """Render colored turn movements and resulting zone states to standard error.

        Standard output remains reserved for the evaluator's movement-only format.
        """
        if graph.start_name is None:
            return
        positions = {identifier: graph.start_name for identifier in range(1, drone_count + 1)}
        in_flight: dict[int, str] = {}
        print("Fly-in visualization", file=sys.stderr)
        print(f"zones: {len(graph.zones)}, links: {len(graph.connections)}", file=sys.stderr)
        for number, turn in enumerate(turns, start=1):
            colored_movements = [
                self._color_movement(graph, movement, positions, in_flight)
                for movement in turn.movements
            ]
            print(f"turn {number}: {' '.join(colored_movements)}", file=sys.stderr)
            self._render_zone_states(graph, positions, in_flight)
        print(f"completed in {len(turns)} turns", file=sys.stderr)

    def _color_movement(
        self,
        graph: Graph,
        movement: str,
        positions: dict[int, str],
        in_flight: dict[int, str],
    ) -> str:
        """Apply a move to the display state and color it by its destination zone."""
        drone_text, destination_text = movement.split("-", maxsplit=1)
        identifier = int(drone_text[1:])
        if destination_text in graph.zones:
            positions[identifier] = destination_text
            in_flight.pop(identifier, None)
            destination = destination_text
        else:
            connection = self._connection_named(graph, destination_text)
            origin = positions.pop(identifier)
            destination = connection.other(origin)
            in_flight[identifier] = destination
        if destination == graph.end_name:
            positions.pop(identifier, None)
        return self._color(graph.zones[destination].color, movement)

    def _render_zone_states(
        self,
        graph: Graph,
        positions: dict[int, str],
        in_flight: dict[int, str],
    ) -> None:
        """Write the post-turn occupants of every zone and every active transit."""
        for name, zone in graph.zones.items():
            occupants = sorted(
                identifier for identifier, position in positions.items() if position == name
            )
            drones = ", ".join(f"D{identifier}" for identifier in occupants) or "empty"
            print(
                f"  {self._color(zone.color, name)} ({zone.zone_type.value}): {drones}",
                file=sys.stderr,
            )
        if in_flight:
            flights = ", ".join(
                f"D{identifier}->{destination}"
                for identifier, destination in sorted(in_flight.items())
            )
            print(f"  in flight: {flights}", file=sys.stderr)

    def _connection_named(self, graph: Graph, name: str) -> Connection:
        """Return the declared connection whose output name is ``name``."""
        for connection in graph.connections.values():
            if connection.name == name:
                return connection
        raise ValueError(f"unknown connection in movement output: {name}")

    def _color(self, color: str | None, text: str) -> str:
        """Wrap text in an ANSI color sequence when the map defines a color."""
        if color is None:
            return text
        code = self._ANSI_COLORS.get(color.lower())
        if code is None:
            code = f"38;5;{16 + sum(ord(character) for character in color) % 216}"
        return f"\033[{code}m{text}{self._RESET}"
