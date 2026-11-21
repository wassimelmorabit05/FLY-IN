"""Replay the output one turn at a time using basic Pygame drawing."""

import pygame

from graph import Graph, Zone


class Visualizer:
    """Draw zones, connections and current drone positions."""

    def __init__(self, graph: Graph, turns: list[str]) -> None:
        """Prepare screen positions; the GUI never changes the simulation."""
        self.graph = graph
        self.turns = turns
        self.points = self.map_points()
        self.turn_index = 0
        self.positions: dict[str, str] = {}
        self.reset()

    def map_points(self) -> dict[str, tuple[int, int]]:
        """Fit integer map coordinates inside the drawing area."""
        xs = [zone.x for zone in self.graph.zones.values()]
        ys = [zone.y for zone in self.graph.zones.values()]
        width = max(xs) - min(xs)
        height = max(ys) - min(ys)
        # Ratios keep even very large integer coordinates safe to display.
        if not width and not height:
            draw_width, draw_height = 0.0, 0.0
        elif width * 470 >= height * 1000:
            draw_width, draw_height = 1000.0, height / max(width, 1) * 1000
        else:
            draw_width, draw_height = width / height * 470, 470.0
        points: dict[str, tuple[int, int]] = {}
        for name, zone in self.graph.zones.items():
            x = 60 + (1000 - draw_width) / 2
            y = 125 + (470 - draw_height) / 2
            points[name] = (
                int(x + (zone.x - min(xs)) / max(width, 1) * draw_width),
                int(y + (max(ys) - zone.y) / max(height, 1) * draw_height)
            )
        for link in self.graph.connections:
            x1, y1 = points[link.first]
            x2, y2 = points[link.second]
            points[link.name] = ((x1 + x2) // 2, (y1 + y2) // 2)
        return points

    def reset(self) -> None:
        """Return the replay to turn zero."""
        self.turn_index = 0
        self.positions = {
            f"D{i}": self.graph.start
            for i in range(1, self.graph.nb_drones + 1)
        }

    def advance(self) -> None:
        """Apply one complete output line, removing delivered drones."""
        if self.turn_index == len(self.turns):
            return
        for movement in self.turns[self.turn_index].split():
            drone, destination = movement.split("-", 1)
            if destination == self.graph.end:
                del self.positions[drone]
            else:
                self.positions[drone] = destination
        self.turn_index += 1

    @staticmethod
    def color(zone: Zone) -> pygame.Color:
        """Use known colors and a stable fallback for custom color names."""
        if zone.color == "none":
            return pygame.Color(80, 145, 210)
        try:
            return pygame.Color(zone.color)
        except ValueError:
            number = sum(ord(char) for char in zone.color)
            return pygame.Color(80 + number % 150,
                                80 + number * 3 % 150,
                                80 + number * 7 % 150)

    def text(self, message: str, point: tuple[int, int],
             centered: bool = False) -> None:
        """Render text onto a small dark background for readability."""
        surface = self.font.render(message, True, "white", (23, 29, 40))
        rectangle = surface.get_rect()
        if centered:
            rectangle.center = point
        else:
            rectangle.topleft = point
        self.screen.blit(surface, rectangle)

    def draw(self) -> None:
        """Draw one frame from the current replay state."""
        self.screen.fill((23, 29, 40))
        for link in self.graph.connections:
            pygame.draw.line(self.screen, (80, 90, 110),
                             self.points[link.first],
                             self.points[link.second], 2)
        for name, zone in self.graph.zones.items():
            x, y = self.points[name]
            pygame.draw.circle(self.screen, self.color(zone), (x, y), 14)
            pygame.draw.circle(self.screen, "white", (x, y), 14, 1)
            if zone.kind == "restricted":
                pygame.draw.circle(self.screen, "white", (x, y), 18, 1)
            elif zone.kind == "blocked":
                pygame.draw.line(self.screen, "white",
                                 (x - 9, y - 9), (x + 9, y + 9), 3)
                pygame.draw.line(self.screen, "white",
                                 (x - 9, y + 9), (x + 9, y - 9), 3)
            if len(self.graph.zones) <= 20:
                label = name if len(name) <= 12 else name[:9] + "..."
                self.text(label, (x, y - 30), centered=True)

        groups: dict[str, list[str]] = {}
        for drone, location in self.positions.items():
            groups.setdefault(location, []).append(drone)
        for location, drones in groups.items():
            x, y = self.points[location]
            pygame.draw.circle(self.screen, "gold", (x, y), 7)
            label = drones[0] if len(drones) == 1 else f"{len(drones)} drones"
            self.text(label, (x, y + 32), centered=True)

        delivered = self.graph.nb_drones - len(self.positions)
        self.text(f"FLY-IN   |   Turn {self.turn_index}/{len(self.turns)}"
                  f"   |   Delivered {delivered}/{self.graph.nb_drones}",
                  (24, 18))
        self.text("SPACE / RIGHT: next turn     R: restart     ESC: close",
                  (24, 46))
        self.text("Gold dot: drones   Double ring: restricted   X: blocked",
                  (24, 74))
        self.draw_details(groups)

    def draw_details(self, groups: dict[str, list[str]]) -> None:
        """Show full names, capacities and drone IDs near the mouse."""
        mouse = pygame.mouse.get_pos()
        nearest = min(self.points, key=lambda name: (
            (self.points[name][0] - mouse[0]) ** 2
            + (self.points[name][1] - mouse[1]) ** 2
        ))
        x, y = self.points[nearest]
        if (x - mouse[0]) ** 2 + (y - mouse[1]) ** 2 > 35 ** 2:
            self.text("Hover a zone or connection midpoint for details.",
                      (24, 650))
            return
        drones = groups.get(nearest, [])
        if nearest in self.graph.zones:
            zone = self.graph.zones[nearest]
            capacity = str(zone.capacity)
            if nearest in (self.graph.start, self.graph.end):
                capacity = "unlimited"
            detail = (f"{nearest} | {zone.kind} | color={zone.color} | "
                      f"occupancy {len(drones)}/{capacity}")
        else:
            link = next(link for link in self.graph.connections
                        if link.name == nearest)
            detail = (f"{nearest} | in transit "
                      f"{len(drones)}/{link.capacity}")
        self.text(detail[:140], (24, 650))
        ids = ", ".join(drones)
        if len(ids) > 130:
            ids = ids[:127] + "..."
        self.text("Drones: " + (ids or "none"), (24, 680))

    def show(self) -> None:
        """Handle events, draw frames and always release Pygame resources."""
        try:
            pygame.display.init()
            pygame.font.init()
            self.screen = pygame.display.set_mode((1120, 720))
            pygame.display.set_caption("Fly-in")
            self.font = pygame.font.Font(None, 20)
            clock = pygame.time.Clock()
            running = True
            while running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.KEYDOWN:
                        if event.key in (pygame.K_SPACE, pygame.K_RIGHT):
                            self.advance()
                        elif event.key == pygame.K_r:
                            self.reset()
                        elif event.key == pygame.K_ESCAPE:
                            running = False
                self.draw()
                pygame.display.flip()
                clock.tick(30)
        except pygame.error as error:
            raise RuntimeError(
                f"Pygame: {error}. Use --no-gui if no display is available."
            ) from error
        finally:
            pygame.quit()
