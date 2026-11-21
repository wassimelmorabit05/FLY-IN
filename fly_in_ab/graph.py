"""Store map objects and build a bidirectional adjacency dictionary."""


class Zone:
    """Store one zone's name, coordinates, type, color and capacity."""

    def __init__(self, name: str, x: int, y: int,
                 kind: str = "normal", color: str = "none",
                 capacity: int = 1) -> None:
        """Create a zone from already validated input."""
        self.name = name
        self.x = x
        self.y = y
        self.kind = kind
        self.color = color
        self.capacity = capacity

    def movement_cost(self) -> int:
        """Return the entry duration; pathfinding excludes blocked zones."""
        return 2 if self.kind == "restricted" else 1


class Connection:
    """Store an undirected connection and its shared capacity."""

    def __init__(self, first: str, second: str, capacity: int = 1) -> None:
        """Keep the input order for the connection's output name."""
        self.first = first
        self.second = second
        self.name = f"{first}-{second}"
        self.capacity = capacity


class MapData:
    """Hold the parser's result before adjacency is built."""

    def __init__(self) -> None:
        """Start with an empty map."""
        self.nb_drones = 0
        self.start = ""
        self.end = ""
        self.zones: dict[str, Zone] = {}
        self.connections: list[Connection] = []


class Graph:
    """Provide direct access to each zone's neighboring connections."""

    def __init__(self, data: MapData) -> None:
        """Build both directions without reparsing the input file."""
        self.nb_drones = data.nb_drones
        self.start = data.start
        self.end = data.end
        self.zones = data.zones
        self.connections = data.connections
        self.neighbors: dict[str, dict[str, Connection]] = {
            name: {} for name in self.zones
        }
        for link in self.connections:
            self.neighbors[link.first][link.second] = link
            self.neighbors[link.second][link.first] = link
