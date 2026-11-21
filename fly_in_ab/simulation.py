"""Reserve complete journeys, then emit their simultaneous movements."""

from graph import Connection, Graph, Zone


class Route:
    """Expand restricted entries into a connection turn and a zone turn."""

    def __init__(self, graph: Graph, path: list[str]) -> None:
        """Build stages and the capacity resources needed at each stage."""
        self.stages: list[Zone | Connection] = []
        self.resources: list[list[Zone | Connection]] = []
        for source, target in zip(path, path[1:]):
            zone = graph.zones[target]
            link = graph.neighbors[source][target]
            if zone.kind == "restricted":
                self.stages.append(link)
                self.resources.append([link])
                self.stages.append(zone)
                self.resources.append([zone])
            else:
                self.stages.append(zone)
                self.resources.append([link, zone])


class Drone:
    """Store one drone's chosen route and first movement turn."""

    def __init__(self, drone_id: int, route: Route, departure: int) -> None:
        """Record a complete, conflict-free journey."""
        self.id = drone_id
        self.route = route
        self.departure = departure


class Simulation:
    """Choose earliest arrival times using a (resource, turn) calendar."""

    def __init__(self, graph: Graph, paths: list[list[str]]) -> None:
        """Prepare candidate routes and an initially empty calendar."""
        self.graph = graph
        self.routes = [Route(graph, path) for path in paths]
        self.used: dict[tuple[str, int], int] = {}
        self.drones: list[Drone] = []

    def can_depart(self, route: Route, departure: int) -> bool:
        """Check every future resource before committing any movement."""
        for offset, resources in enumerate(route.resources):
            turn = departure + offset
            for resource in resources:
                if resource.name in (self.graph.start, self.graph.end):
                    continue
                count = self.used.get((resource.name, turn), 0)
                if count >= resource.capacity:
                    return False
        return True

    def reserve(self, route: Route, departure: int) -> None:
        """Reserve every occupied zone and used connection on the route."""
        for offset, resources in enumerate(route.resources):
            for resource in resources:
                key = (resource.name, departure + offset)
                self.used[key] = self.used.get(key, 0) + 1

    def run(self) -> list[str]:
        """Plan drones in ID order, then output one line per turn."""
        self.used.clear()
        self.drones.clear()
        # Reservations only increase: earlier failed departures stay invalid.
        next_departure = [1] * len(self.routes)
        for drone_id in range(1, self.graph.nb_drones + 1):
            choices: list[tuple[int, int, int]] = []
            for index, route in enumerate(self.routes):
                departure = next_departure[index]
                while not self.can_depart(route, departure):
                    departure += 1
                next_departure[index] = departure
                arrival = departure + len(route.stages) - 1
                choices.append((arrival, index, departure))
            _, index, departure = min(choices)
            route = self.routes[index]
            self.reserve(route, departure)
            self.drones.append(Drone(drone_id, route, departure))
        return self.output()

    def output(self) -> list[str]:
        """Group movements by absolute turn; omit drones that are waiting."""
        turns: list[list[str]] = []
        for drone in self.drones:
            for offset, stage in enumerate(drone.route.stages):
                turn_index = drone.departure + offset - 1
                while len(turns) <= turn_index:
                    turns.append([])
                turns[turn_index].append(f"D{drone.id}-{stage.name}")
        return [" ".join(moves) for moves in turns]
