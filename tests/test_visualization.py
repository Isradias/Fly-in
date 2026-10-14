"""Tests for the optional ANSI terminal visualization."""

from contextlib import redirect_stderr
from io import StringIO
import unittest

from flyin.parser import MapParser
from flyin.simulation import Simulator
from flyin.visualization import TerminalVisualizer


class TerminalVisualizationTests(unittest.TestCase):
    """Verify that visual mode exposes colored movements and zone states."""

    def test_visualization_colors_movements_and_reports_zone_states(self) -> None:
        """Configured zone colors and post-turn occupancy are rendered to stderr."""
        definition = MapParser().parse_lines(
            [
                "nb_drones: 1\n",
                "start_hub: start 0 0 [color=green]\n",
                "end_hub: end 1 0 [color=red]\n",
                "connection: start-end\n",
            ]
        )
        turns = Simulator(definition.graph, definition.drone_count).run()
        output = StringIO()
        with redirect_stderr(output):
            TerminalVisualizer().render(
                definition.graph,
                definition.drone_count,
                turns,
            )
        rendered = output.getvalue()
        self.assertIn("\033[31mD1-end\033[0m", rendered)
        self.assertIn("turn 1:", rendered)
        self.assertIn("start", rendered)
        self.assertIn("end", rendered)
