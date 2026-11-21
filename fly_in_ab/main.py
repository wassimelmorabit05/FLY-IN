"""Run Parsing -> Graph -> Dijkstra -> Second Path -> Simulation -> GUI."""

import argparse
import os
import sys

from algorithm import Dijkstra
from graph import Graph
from parser import Parser
from second_path import SecondPath
from simulation import Simulation


class Main:
    """Connect the project stages and handle user-facing errors."""

    @staticmethod
    def arguments() -> argparse.Namespace:
        """Read the map filename and optional display/statistics flags."""
        cli = argparse.ArgumentParser(description="Fly-in drone routing")
        cli.add_argument("map", help="path to a map text file")
        cli.add_argument("--no-gui", action="store_true",
                         help="print movements without opening Pygame")
        cli.add_argument("--stats", action="store_true",
                         help="print the turn count to stderr")
        return cli.parse_args()

    def run(self) -> int:
        """Return zero on success and one on a handled project error."""
        args = self.arguments()
        try:
            data = Parser().parse(args.map)
            graph = Graph(data)
            first = Dijkstra(graph).find_path()
            if not first:
                raise ValueError("no path from start to end (unsolvable map)")
            second = SecondPath(graph).find_path(first)

            turns = Simulation(graph, [first]).run()
            if second:
                combined = Simulation(graph, [first, second]).run()
                if len(combined) < len(turns):
                    turns = combined

            for turn in turns:
                print(turn)
            if args.stats:
                print(f"Delivered {graph.nb_drones} drones in "
                      f"{len(turns)} turns.", file=sys.stderr)
            if not args.no_gui:
                os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
                from visualization import Visualizer
                Visualizer(graph, turns).show()
            return 0
        except (OSError, UnicodeError, ValueError, RuntimeError) as error:
            print(f"Error: {error}", file=sys.stderr)
            return 1
        except ImportError:
            print("Error: install dependencies with 'uv sync', or use "
                  "--no-gui for text output.", file=sys.stderr)
            return 1
        except KeyboardInterrupt:
            print("Stopped.", file=sys.stderr)
            return 130


if __name__ == "__main__":
    sys.exit(Main().run())
