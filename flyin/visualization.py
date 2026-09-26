"""Optional terminal feedback kept separate from official simulation output."""

from __future__ import annotations

import sys

from flyin.domain import Graph
from flyin.simulation import Turn


class TerminalVisualizer:
    """Write a concise, color-aware simulation summary to standard error."""

    def render(self, graph: Graph, turns: list[Turn]) -> None:
        """Render zone metadata and turn count without changing standard output."""
        print("Fly-in visualization", file=sys.stderr)
        print(f"zones: {len(graph.zones)}, links: {len(graph.connections)}", file=sys.stderr)
        for name, zone in graph.zones.items():
            color = zone.color or "none"
            print(f"  {name}: {zone.zone_type.value}, color={color}", file=sys.stderr)
        print(f"completed in {len(turns)} turns", file=sys.stderr)
