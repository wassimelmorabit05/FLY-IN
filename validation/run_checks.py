"""Run standalone development checks from the companion validation folder."""

import os
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

PROJECT = Path(__file__).resolve().parents[1] / "fly_in"
sys.path.insert(0, str(PROJECT))

from algorithm import Dijkstra  # noqa: E402
from graph import Graph  # noqa: E402
from parser import Parser  # noqa: E402
from second_path import SecondPath  # noqa: E402
from simulation import Simulation  # noqa: E402
from verify_output import OutputVerifier  # noqa: E402


BASE = """nb_drones: 3
start_hub: s 0 0
hub: a 1 0
end_hub: g 2 0
connection: s-a
connection: a-g
"""

BENCHMARKS = {
    "easy/01_linear_path.txt": 4,
    "easy/02_simple_fork.txt": 4,
    "easy/03_basic_capacity.txt": 4,
    "medium/01_dead_end_trap.txt": 8,
    "medium/02_circular_loop.txt": 10,
    "medium/03_priority_puzzle.txt": 6,
    "hard/01_maze_nightmare.txt": 13,
    "hard/02_capacity_hell.txt": 16,
    "hard/03_ultimate_challenge.txt": 26,
    "challenger/01_the_impossible_dream.txt": 43,
}


class ProjectTests(unittest.TestCase):
    """Test observable behavior and check generated outputs independently."""

    def setUp(self) -> None:
        """Give every test an isolated temporary input file."""
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.filename = Path(self.temp.name) / "map.txt"

    def graph(self, text: str) -> Graph:
        """Parse test text through the real file parser."""
        self.filename.write_text(text, encoding="utf-8")
        return Graph(Parser().parse(str(self.filename)))

    @staticmethod
    def solve(graph: Graph) -> list[str]:
        """Run both strategies and replay every candidate for legality."""
        first = Dijkstra(graph).find_path()
        if not first:
            return []
        second = SecondPath(graph).find_path(first)
        runs = [Simulation(graph, [first]).run()]
        if second:
            runs.append(Simulation(graph, [first, second]).run())
        for turns in runs:
            OutputVerifier().verify(graph, turns)
        return min(runs, key=len)

    def test_benchmarks(self) -> None:
        """All nine maps and the challenger must be legal and optimal."""
        for name, expected in BENCHMARKS.items():
            with self.subTest(map=name):
                graph = Graph(Parser().parse(str(PROJECT / "maps" / name)))
                self.assertEqual(len(self.solve(graph)), expected)

    def test_defaults(self) -> None:
        """Keep types, colors and default capacities exactly as specified."""
        graph = self.graph(BASE)
        zone = graph.zones["a"]
        self.assertEqual((zone.kind, zone.color, zone.capacity),
                         ("normal", "none", 1))
        self.assertEqual(graph.connections[0].capacity, 1)
        self.assertIs(graph.neighbors["s"]["a"], graph.neighbors["a"]["s"])
        self.assertEqual(len(self.solve(graph)), 4)

    def test_valid_parser_variants(self) -> None:
        """Allow comments, signed coordinates, custom colors and odd names."""
        variants = [
            "\ufeff\n# header\n" + BASE.replace("\n", "\r\n"),
            BASE.replace("hub: a 1 0", "hub: a -10 +2 [] # comment"),
            BASE.replace("hub: a 1 0", "hub: a 1 0 [color=rainbow "
                         "max_drones=50 zone=priority]"),
            BASE.replace("hub: a 1 0", "hub: a 0 0"),
            BASE.replace("hub: a 1 0", "hub: a 1 0 [ max_drones=5 ]"),
            BASE.replace("hub: a ", "hub: @a_:é[ok] ")
                .replace("s-a", "s-@a_:é[ok]")
                .replace("a-g", "@a_:é[ok]-g"),
            BASE + "connection: a-a\n",
        ]
        for text in variants:
            with self.subTest(text=text):
                self.assertTrue(self.solve(self.graph(text)))

    def test_endpoint_capacity_is_ignored(self) -> None:
        """Subject v3 overrides generic capacity validation on endpoints."""
        for value in ("1", "0", "-2", "nonsense"):
            text = BASE.replace("s 0 0", f"s 0 0 [max_drones={value}]")
            text = text.replace("g 2 0", f"g 2 0 [max_drones={value}]")
            graph = self.graph(text)
            self.assertEqual(graph.zones["s"].capacity, 3)
            self.assertTrue(self.solve(graph))

    def test_parser_errors(self) -> None:
        """Reject malformed records with useful line-aware errors."""
        bad = [
            "", "# empty\n", BASE.replace("nb_drones: 3\n", ""),
            "hub: first 0 0\n" + BASE,
            BASE + "nb_drones: 2\n",
            BASE.replace("nb_drones: 3", "nb_drones 3"),
            BASE.replace("hub: a 1 0", "hub: a 1"),
            BASE.replace("hub: a 1 0", "hub: a x 0"),
            BASE.replace("hub: a 1 0", "hub: bad-name 1 0"),
            BASE + "hub: a 4 0\n",
            BASE + "start_hub: another 4 0\n",
            BASE + "end_hub: another 4 0\n",
            BASE.replace("start_hub: s 0 0\n", ""),
            BASE.replace("end_hub: g 2 0\n", ""),
            BASE + "connection: a-s\n",
            BASE + "connection: s-missing\n",
            BASE.replace("hub: a 1 0\n", "") + "hub: a 1 0\n",
            BASE + "nonsense: value\n",
            BASE + "connection: s a\n",
            BASE + "connection: s-a-g\n",
        ]
        for value in ("0", "-1", "abc", "1.5", "1_0", "++1", "1e3"):
            bad.append(BASE.replace("nb_drones: 3", f"nb_drones: {value}"))
            bad.append(BASE.replace("hub: a 1 0",
                                    f"hub: a 1 0 [max_drones={value}]"))
            bad.append(BASE.replace("connection: s-a",
                                    "connection: s-a "
                                    f"[max_link_capacity={value}]"))
        for suffix in ("[zone=unknown]", "[zone=]", "[zone=normal",
                       "zone=normal", "[zone=normal] junk", "[[color=red]]",
                       "[color=red][zone=normal]", "[color=red color=blue]",
                       "[max_drones=1=2]", "[unknown=3]", "[color=light blue]"):
            bad.append(BASE.replace("hub: a 1 0", f"hub: a 1 0 {suffix}"))
        bad.append(BASE.replace("connection: s-a", "connection: s-a "
                                "[max_link_capacity=1 max_link_capacity=2]"))
        for text in bad:
            with self.subTest(text=text):
                with self.assertRaisesRegex(ValueError, "line"):
                    self.graph(text)

    def test_single_drone(self) -> None:
        """Use the expected two moves for a single normal-route drone."""
        graph = self.graph(BASE.replace("nb_drones: 3", "nb_drones: 1"))
        self.assertEqual(self.solve(graph), ["D1-a", "D1-g"])

    def test_disconnected_and_blocked(self) -> None:
        """Unreachable graphs terminate without starting the simulation."""
        for text in (BASE.replace("connection: a-g\n", ""),
                     BASE.replace("hub: a 1 0", "hub: a 1 0 [zone=blocked]"),
                     BASE.replace("g 2 0", "g 2 0 [zone=blocked]"),
                     BASE.replace("s 0 0", "s 0 0 [zone=blocked]")):
            self.assertEqual(Dijkstra(self.graph(text)).find_path(), [])

    def test_restricted_pipeline(self) -> None:
        """Arriving frees a link and departing frees a zone that same turn."""
        graph = self.graph(BASE.replace("hub: a 1 0",
                                       "hub: a 1 0 [zone=restricted]"))
        self.assertEqual(self.solve(graph), [
            "D1-s-a",
            "D1-a D2-s-a",
            "D1-g D2-a D3-s-a",
            "D2-g D3-a",
            "D3-g",
        ])

    def test_restricted_end_and_consecutive_zones(self) -> None:
        """Apply the entry cost to the end too, with consecutive flights."""
        text = BASE.replace("hub: a 1 0", "hub: a 1 0 [zone=restricted]")
        text = text.replace("end_hub: g 2 0", "end_hub: g 2 0 [zone=restricted]")
        self.assertEqual(len(self.solve(self.graph(text))), 6)

    def test_high_capacity(self) -> None:
        """Use huge capacities without expanding storage by their value."""
        text = BASE.replace("nb_drones: 3", "nb_drones: 1000")
        text = text.replace("hub: a 1 0", "hub: a 1 0 [max_drones=1000000]")
        text = text.replace("connection: s-a", "connection: s-a [max_link_capacity=1000000]")
        text = text.replace("connection: a-g", "connection: a-g [max_link_capacity=1000000]")
        self.assertEqual(len(self.solve(self.graph(text))), 2)

    def test_priority_tie_and_actual_cost(self) -> None:
        """Priority is a tie-breaker, never a zero-turn movement."""
        text = """nb_drones: 1
start_hub: s 0 0
hub: a 1 0
hub: z 1 1 [zone=priority]
end_hub: g 2 0
connection: s-a
connection: a-g
connection: s-z
connection: z-g
"""
        graph = self.graph(text)
        self.assertEqual(Dijkstra(graph).find_path(), ["s", "z", "g"])
        self.assertEqual(len(self.solve(graph)), 2)
        graph = self.graph(text + "connection: s-g\n")
        first = Dijkstra(graph).find_path()
        self.assertEqual(first, ["s", "g"])
        self.assertEqual(SecondPath(graph).find_path(first), ["s", "z", "g"])

    def test_merging_restricted_routes(self) -> None:
        """Two incoming links cannot overbook the same restricted zone."""
        graph = self.graph("""nb_drones: 12
start_hub: s 0 0
hub: a 1 0 [max_drones=4]
hub: b 1 1 [max_drones=4]
hub: r 2 0 [zone=restricted]
end_hub: g 3 0
connection: s-a [max_link_capacity=4]
connection: s-b [max_link_capacity=4]
connection: a-r [max_link_capacity=4]
connection: b-r [max_link_capacity=4]
connection: r-g
""")
        self.assertTrue(self.solve(graph))

    def test_opposing_routes_share_link_capacity(self) -> None:
        """A bidirectional edge has one capacity shared by both directions."""
        for kind in ("normal", "restricted"):
            graph = self.graph(f"""nb_drones: 10
start_hub: s 0 0
hub: a 1 0 [zone={kind} max_drones=2]
hub: b 1 1 [max_drones=2]
end_hub: g 2 0
connection: s-a
connection: s-b
connection: a-b
connection: a-g
connection: b-g
""")
            turns = Simulation(graph, [["s", "a", "b", "g"],
                                       ["s", "b", "a", "g"]]).run()
            OutputVerifier().verify(graph, turns)

    def test_random_graphs(self) -> None:
        """Replay 500 seeded graphs with cycles, bottlenecks and blocks."""
        for seed in range(500):
            rng = random.Random(seed)
            count = rng.randint(3, 14)
            lines = [f"nb_drones: {rng.randint(1, 35)}"]
            for i in range(count):
                role = "start_hub" if i == 0 else "hub"
                role = "end_hub" if i == count - 1 else role
                kind = rng.choice(["normal", "normal", "priority",
                                   "restricted", "blocked"])
                if i == 0:
                    kind = "normal"
                lines.append(f"{role}: z{i} {i} {i % 3} "
                             f"[zone={kind} max_drones={rng.randint(1, 4)}]")
            for a in range(count):
                for b in range(a + 1, count):
                    if b == a + 1 or rng.random() < 0.25:
                        lines.append(f"connection: z{a}-z{b} "
                                     f"[max_link_capacity={rng.randint(1, 4)}]")
            with self.subTest(seed=seed):
                self.solve(self.graph("\n".join(lines)))

    def test_checker_rejects_invalid_outputs(self) -> None:
        """Show that the independent checker catches deliberate corruption."""
        graph = self.graph(BASE)
        for turns in (["D1-a D2-a D3-a", "D1-g D2-g D3-g"],
                      ["D1-g D2-g D3-g"], ["D1-a D1-g"],
                      ["D1-s"], ["D4-a"], ["D1-a"]):
            with self.assertRaises(AssertionError):
                OutputVerifier().verify(graph, turns)
        restricted = self.graph(BASE.replace("hub: a 1 0",
                                            "hub: a 1 0 [zone=restricted]"))
        for turns in (["D1-a"], ["D1-s-a", "", "D1-a"],
                      ["D1-s-a", "D1-g"]):
            with self.assertRaises(AssertionError):
                OutputVerifier().verify(restricted, turns)

    def test_cli_output_and_failures(self) -> None:
        """Check real process output, failures, and Pygame import isolation."""
        self.graph(BASE)
        command = [sys.executable, str(PROJECT / "main.py"),
                   str(self.filename), "--no-gui"]
        result = subprocess.run(command, text=True, capture_output=True,
                                timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        OutputVerifier().verify(self.graph(BASE), result.stdout.splitlines())
        for text in ("nb_drones: wrong\n", BASE.replace("connection: a-g", "#")):
            self.filename.write_text(text)
            result = subprocess.run(command, text=True, capture_output=True,
                                    timeout=10)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(result.stdout, "")
            self.assertIn("Error:", result.stderr)
            self.assertNotIn("Traceback", result.stderr)
        self.filename.unlink()
        result = subprocess.run(command, text=True, capture_output=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn("Error:", result.stderr)
        result = subprocess.run(command[:2], text=True, capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("usage:", result.stderr)

    def test_gui_failure_is_handled(self) -> None:
        """An unavailable display must produce a helpful error, not a crash."""
        self.graph(BASE)
        env = dict(os.environ, SDL_VIDEODRIVER="nonexistent-driver")
        result = subprocess.run(
            [sys.executable, str(PROJECT / "main.py"), str(self.filename)],
            text=True, capture_output=True, env=env, timeout=10
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("--no-gui", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_visualizer_replay_and_events(self) -> None:
        """Replay all deliveries and exercise real Pygame event handling."""
        os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        import pygame
        from visualization import Visualizer
        graph = self.graph(BASE)
        turns = self.solve(graph)
        view = Visualizer(graph, turns)
        for _ in turns:
            view.advance()
        self.assertEqual(view.positions, {})
        view.advance()
        self.assertEqual(view.turn_index, len(turns))
        view.reset()
        self.assertEqual(len(view.positions), 3)
        events = [
            [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE)],
            [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT)],
            [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_r)],
            [pygame.event.Event(pygame.QUIT)],
        ]
        with patch("pygame.event.get", side_effect=events):
            view.show()
        self.assertEqual(view.turn_index, 0)
        self.assertEqual(len(view.positions), 3)
        self.assertFalse(pygame.display.get_init())

    def test_visualizer_extreme_coordinates_and_custom_color(self) -> None:
        """Avoid display arithmetic failures on valid unusual map data."""
        os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
        from visualization import Visualizer
        text = BASE.replace("hub: a 1 0",
                            f"hub: a {10 ** 400} 0 [color=rainbow]")
        graph = self.graph(text)
        view = Visualizer(graph, self.solve(graph))
        for x, y in view.points.values():
            self.assertTrue(60 <= x <= 1060 and 125 <= y <= 595)
        self.assertEqual(view.color(graph.zones["a"]),
                         view.color(graph.zones["a"]))
        graph = self.graph(BASE.replace("a 1 0", "a 0 0")
                          .replace("g 2 0", "g 0 0"))
        self.assertEqual(Visualizer(graph, []).points["a"], (560, 360))


if __name__ == "__main__":
    unittest.main(verbosity=2)
