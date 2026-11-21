"""Find an alternative even when it shares zones with the first path."""

from algorithm import Dijkstra
from graph import Graph


class SecondPath:
    """Temporarily block each first-path edge and rerun Dijkstra."""

    def __init__(self, graph: Graph) -> None:
        """Keep the same graph; blocking never modifies it."""
        self.graph = graph

    def find_path(self, first: list[str]) -> list[str]:
        """Return the cheapest different path, or [] if none exists."""
        dijkstra = Dijkstra(self.graph)
        candidates: list[list[str]] = []
        for source, target in zip(first, first[1:]):
            link = self.graph.neighbors[source][target]
            path = dijkstra.find_path(blocked_link=link.name)
            if path and path not in candidates:
                candidates.append(path)
        if not candidates:
            return []
        return min(candidates, key=lambda p: (dijkstra.path_score(p), p))
