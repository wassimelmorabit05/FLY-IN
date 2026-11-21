"""Find a shortest path with a simple, heap-free Dijkstra algorithm."""

from graph import Graph


class Dijkstra:
    """Minimize real turns, then prefer more priority zones on ties."""

    def __init__(self, graph: Graph) -> None:
        """Reuse the graph already constructed by main."""
        self.graph = graph

    def path_score(self, path: list[str]) -> tuple[int, int]:
        """Return (travel turns, negative number of priority entries)."""
        turns = 0
        priority = 0
        for name in path[1:]:
            zone = self.graph.zones[name]
            turns += zone.movement_cost()
            priority += int(zone.kind == "priority")
        return turns, -priority

    def find_path(self, blocked_link: str = "") -> list[str]:
        """Return the best path, or [] if the destination is unreachable."""
        start, end = self.graph.start, self.graph.end
        if (self.graph.zones[start].kind == "blocked"
                or self.graph.zones[end].kind == "blocked"):
            return []
        distances: dict[str, tuple[int, int]] = {start: (0, 0)}
        previous: dict[str, str] = {}
        pending = {start}
        visited: set[str] = set()
        while pending:
            current = min(pending, key=lambda n: (distances[n], n))
            pending.remove(current)
            if current == end:
                return self.rebuild_path(previous, end)
            visited.add(current)
            for name, link in self.graph.neighbors[current].items():
                zone = self.graph.zones[name]
                if (name in visited or zone.kind == "blocked"
                        or link.name == blocked_link):
                    continue
                turns, priority = distances[current]
                score = (turns + zone.movement_cost(),
                         priority - int(zone.kind == "priority"))
                if name not in distances or score < distances[name]:
                    distances[name] = score
                    previous[name] = current
                    pending.add(name)
        return []

    @staticmethod
    def rebuild_path(previous: dict[str, str], end: str) -> list[str]:
        """Follow predecessor names backward, then reverse the result."""
        path = [end]
        while path[-1] in previous:
            path.append(previous[path[-1]])
        path.reverse()
        return path
