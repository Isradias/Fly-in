"""Typed object model for the Fly-in network and drone states."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from flyin.errors import GraphError


class ZoneType(str, Enum):
    """Kinds of zone defined by the Fly-in subject."""

    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"


class DroneState(str, Enum):
    """The lifecycle state of a drone in a simulation."""

    AT_ZONE = "at_zone"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"


@dataclass(frozen=True, slots=True)
class Zone:
    """A named location that may hold drones.

    The parser assigns start and end flags; their capacity is intentionally unlimited.
    """

    name: str
    x: int
    y: int
    zone_type: ZoneType = ZoneType.NORMAL
    color: str | None = None
    max_drones: int = 1
    is_start: bool = False
    is_end: bool = False

    def __post_init__(self) -> None:
        """Check local zone invariants."""
        if not self.name:
            raise GraphError("zone name cannot be empty")
        if "-" in self.name or any(character.isspace() for character in self.name):
            raise GraphError("zone name cannot contain spaces or dashes")
        if self.max_drones < 1:
            raise GraphError("zone capacity must be positive")
        if self.is_start and self.is_end:
            raise GraphError("a zone cannot be both start and end")

    @property
    def capacity(self) -> int | None:
        """Return capacity, or ``None`` for unbounded terminal zones."""
        if self.is_start or self.is_end:
            return None
        return self.max_drones

    @property
    def arrival_cost(self) -> int:
        """Return the number of turns needed to enter this zone."""
        return 2 if self.zone_type is ZoneType.RESTRICTED else 1


@dataclass(frozen=True, slots=True)
class Connection:
    """A bidirectional, capacity-limited link between two zones."""

    first: str
    second: str
    max_capacity: int = 1

    def __post_init__(self) -> None:
        """Check local connection invariants."""
        if not self.first or not self.second or self.first == self.second:
            raise GraphError("connection endpoints must be distinct zone names")
        if self.max_capacity < 1:
            raise GraphError("connection capacity must be positive")

    @property
    def name(self) -> str:
        """Return the stable output name used for in-flight drones."""
        return f"{self.first}-{self.second}"

    @property
    def key(self) -> frozenset[str]:
        """Return an orientation-independent identity for duplicate detection."""
        return frozenset((self.first, self.second))

    def other(self, zone_name: str) -> str:
        """Return the opposite endpoint of ``zone_name``.

        Raises:
            GraphError: If the zone is not an endpoint.
        """
        if zone_name == self.first:
            return self.second
        if zone_name == self.second:
            return self.first
        raise GraphError(f"zone {zone_name!r} is not on connection {self.name!r}")


@dataclass(slots=True)
class Drone:
    """Mutable simulation state for one identified drone."""

    identifier: int
    state: DroneState = DroneState.AT_ZONE
    zone_name: str | None = None
    connection: Connection | None = None
    destination: str | None = None
    remaining_turns: int = 0

    def begin_transit(self, connection: Connection, destination: str) -> None:
        """Place the drone on a restricted connection for its final transit turn."""
        if self.state is not DroneState.AT_ZONE:
            raise GraphError("only a drone at a zone may enter transit")
        self.state = DroneState.IN_TRANSIT
        self.zone_name = None
        self.connection = connection
        self.destination = destination
        self.remaining_turns = 1

    def arrive(self, zone_name: str, delivered: bool = False) -> None:
        """Move the drone to a zone or mark it as delivered."""
        self.state = DroneState.DELIVERED if delivered else DroneState.AT_ZONE
        self.zone_name = None if delivered else zone_name
        self.connection = None
        self.destination = None
        self.remaining_turns = 0


@dataclass(slots=True)
class Graph:
    """Own zones and connections while preserving all network invariants."""

    zones: dict[str, Zone] = field(default_factory=dict)
    connections: dict[frozenset[str], Connection] = field(default_factory=dict)
    adjacency: dict[str, list[Connection]] = field(default_factory=dict)
    start_name: str | None = None
    end_name: str | None = None

    def add_zone(self, zone: Zone) -> None:
        """Add a unique zone and record any terminal role."""
        if zone.name in self.zones:
            raise GraphError(f"duplicate zone {zone.name!r}")
        if zone.is_start:
            if self.start_name is not None:
                raise GraphError("a graph can have only one start zone")
            self.start_name = zone.name
        if zone.is_end:
            if self.end_name is not None:
                raise GraphError("a graph can have only one end zone")
            self.end_name = zone.name
        self.zones[zone.name] = zone
        self.adjacency[zone.name] = []

    def add_connection(self, connection: Connection) -> None:
        """Add a unique connection whose endpoints already exist."""
        if connection.first not in self.zones or connection.second not in self.zones:
            raise GraphError("connection references an undefined zone")
        if connection.key in self.connections:
            raise GraphError(f"duplicate connection {connection.name!r}")
        self.connections[connection.key] = connection
        self.adjacency[connection.first].append(connection)
        self.adjacency[connection.second].append(connection)

    def neighbors(self, zone_name: str) -> tuple[Connection, ...]:
        """Return links adjacent to an existing zone."""
        if zone_name not in self.zones:
            raise GraphError(f"unknown zone {zone_name!r}")
        return tuple(self.adjacency[zone_name])

    def connection_between(self, first: str, second: str) -> Connection:
        """Return the link between two zones.

        Raises:
            GraphError: If no such link exists.
        """
        key = frozenset((first, second))
        try:
            return self.connections[key]
        except KeyError as error:
            raise GraphError(f"no connection from {first!r} to {second!r}") from error
