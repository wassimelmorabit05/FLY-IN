"""Independently replay output: never inspect the scheduler's reservations."""

from collections import Counter

from graph import Graph


class OutputVerifier:
    """Check the movement rules using only a graph and printed turn lines."""

    def verify(self, graph: Graph, turns: list[str]) -> None:
        """Raise AssertionError for any invalid movement or incomplete run."""
        links = {link.name: link for link in graph.connections}
        positions = {
            f"D{i}": graph.start for i in range(1, graph.nb_drones + 1)
        }
        in_flight: dict[str, str] = {}
        for number, line in enumerate(turns, 1):
            assert positions, f"turn {number}: output after all deliveries"
            moves: dict[str, str] = {}
            for token in line.split():
                drone, separator, target = token.partition("-")
                assert separator and drone in positions, token
                assert drone not in moves, f"drone moved twice: {token}"
                moves[drone] = target
            for drone, destination in in_flight.items():
                assert moves.get(drone) == destination, (
                    f"turn {number}: {drone} must arrive at {destination}"
                )
            next_positions = positions.copy()
            next_flight: dict[str, str] = {}
            used_links: Counter[str] = Counter()
            for drone, target in moves.items():
                origin = positions[drone]
                if drone in in_flight:
                    # Arriving releases the connection for this same turn.
                    assert target == in_flight[drone]
                elif target in graph.zones:
                    assert target != origin, "stationary drone was printed"
                    assert target in graph.neighbors[origin], token
                    assert graph.zones[target].kind in ("normal", "priority")
                    used_links[graph.neighbors[origin][target].name] += 1
                else:
                    assert target in links, f"unknown destination {target}"
                    link = links[target]
                    assert origin in (link.first, link.second)
                    destination = (link.second if origin == link.first
                                   else link.first)
                    assert graph.zones[destination].kind == "restricted"
                    next_flight[drone] = destination
                    used_links[target] += 1
                if target == graph.end:
                    del next_positions[drone]
                else:
                    next_positions[drone] = target
            for name, count in used_links.items():
                assert count <= links[name].capacity, (
                    f"turn {number}: connection {name} capacity exceeded"
                )
            for name, count in Counter(next_positions.values()).items():
                if name in graph.zones:
                    assert graph.zones[name].kind != "blocked"
                    if name not in (graph.start, graph.end):
                        assert count <= graph.zones[name].capacity, (
                            f"turn {number}: zone {name} capacity exceeded"
                        )
            positions, in_flight = next_positions, next_flight
        assert not positions, f"undelivered drones: {positions}"
