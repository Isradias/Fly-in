"""Strict parser for the Fly-in map language."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from flyin.domain import Graph, Zone, ZoneType
from flyin.errors import GraphError, ParseError


_DRONES = re.compile(r"nb_drones:\s*([1-9][0-9]*)\s*$")
_ZONE = re.compile(
    r"(start_hub|end_hub|hub):\s+([^\s-]+)\s+([-+]?\d+)\s+([-+]?\d+)"
    r"(?:\s+(\[[^]]*\]))?\s*$"
)
_METADATA = re.compile(r"\[([^\[\]]*)\]$")


@dataclass(frozen=True, slots=True)
class MapDefinition:
    """The parsed map state required to begin a simulation."""

    drone_count: int
    graph: Graph


class MapParser:
    """Parse textual map declarations while reporting precise failures."""

    def parse_file(self, path: str | Path) -> MapDefinition:
        """Read and parse a map file.

        Raises:
            ParseError: If the file cannot be read or its content is invalid.
        """
        try:
            with Path(path).open(encoding="utf-8") as source:
                return self.parse_lines(source.readlines())
        except OSError as error:
            message = f"cannot read map file {path!s}: {error.strerror}"
            raise ParseError(message) from error

    def parse_lines(self, lines: list[str]) -> MapDefinition:
        """Parse already-loaded lines, mainly to support deterministic tests."""
        meaningful = [
            (number, line.strip())
            for number, line in enumerate(lines, start=1)
            if line.strip() and not line.lstrip().startswith("#")
        ]
        if not meaningful:
            raise ParseError("line 1: expected nb_drones declaration")
        first_number, first_line = meaningful[0]
        count_match = _DRONES.fullmatch(first_line)
        if count_match is None:
            raise ParseError(f"line {first_number}: expected positive nb_drones value")
        graph = Graph()
        for line_number, line in meaningful[1:]:
            self._parse_zone(line, line_number, graph)
        if graph.start_name is None:
            raise ParseError("missing start_hub declaration")
        if graph.end_name is None:
            raise ParseError("missing end_hub declaration")
        return MapDefinition(int(count_match.group(1)), graph)

    def _parse_zone(self, line: str, line_number: int, graph: Graph) -> None:
        """Parse one zone declaration and add it to ``graph``."""
        match = _ZONE.fullmatch(line)
        if match is None:
            raise ParseError(f"line {line_number}: expected a zone declaration")
        kind, name, x_text, y_text, metadata_text = match.groups()
        metadata = self._zone_metadata(metadata_text, line_number)
        type_text = metadata.get("zone", ZoneType.NORMAL.value)
        try:
            zone_type = ZoneType(type_text)
        except ValueError as error:
            message = f"line {line_number}: invalid zone type {type_text!r}"
            raise ParseError(message) from error
        capacity_text = metadata.get("max_drones", "1")
        capacity = self._positive_integer(capacity_text, "max_drones", line_number)
        try:
            graph.add_zone(
                Zone(
                    name=name,
                    x=int(x_text),
                    y=int(y_text),
                    zone_type=zone_type,
                    color=metadata.get("color"),
                    max_drones=capacity,
                    is_start=kind == "start_hub",
                    is_end=kind == "end_hub",
                )
            )
        except GraphError as error:
            raise ParseError(f"line {line_number}: {error}") from error

    def _zone_metadata(self, text: str | None, line_number: int) -> dict[str, str]:
        """Validate and decode a zone metadata block."""
        metadata = self._metadata(text, line_number)
        allowed = {"zone", "color", "max_drones"}
        invalid = set(metadata) - allowed
        if invalid:
            message = f"line {line_number}: invalid zone metadata {invalid.pop()!r}"
            raise ParseError(message)
        return metadata

    def _metadata(self, text: str | None, line_number: int) -> dict[str, str]:
        """Decode unique ``key=value`` metadata entries."""
        if text is None:
            return {}
        match = _METADATA.fullmatch(text)
        if match is None or not match.group(1).strip():
            raise ParseError(f"line {line_number}: invalid metadata block")
        metadata: dict[str, str] = {}
        for item in match.group(1).split():
            if item.count("=") != 1:
                raise ParseError(f"line {line_number}: invalid metadata item {item!r}")
            key, value = item.split("=", maxsplit=1)
            if not key or not value or key in metadata:
                raise ParseError(f"line {line_number}: invalid metadata item {item!r}")
            metadata[key] = value
        return metadata

    def _positive_integer(self, value: str, label: str, line_number: int) -> int:
        """Return a positive integer or raise a line-aware parsing failure."""
        if not value.isdecimal() or int(value) < 1:
            raise ParseError(f"line {line_number}: {label} must be a positive integer")
        return int(value)
