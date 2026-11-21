*This project has been created as part of the 42 curriculum by abguenbo.*

# Fly-in

## Description

Route drones from a start zone to an end zone while respecting zone capacity,
shared connection capacity and movement costs. The code follows this order:
Parsing -> Graph -> Dijkstra -> Second Path -> Simulation -> Visualization.

Seven Python files contain the application. Graph logic uses only the standard
library. Pygame is used only for the display. Python 3.10+ is supported by the
source; `.python-version` selects the tested Python 3.12 environment for uv.

## Instructions

From this `fly_in` directory:

```sh
make install
make run
make run MAP=maps/medium/03_priority_puzzle.txt
```

The equivalent direct command is:

```sh
uv run python main.py maps/medium/03_priority_puzzle.txt
```

For tests or a machine without a display:

```sh
uv run python main.py maps/medium/03_priority_puzzle.txt --no-gui --stats
```

Only movement lines go to stdout. Errors and optional statistics go to stderr.
The GUI opens after the complete movement log has been printed. Closing it exits
the program. Text-only execution also works with `python3 main.py MAP --no-gui`
without installing Pygame.

```sh
make lint
make lint-strict
make debug MAP=maps/easy/01_linear_path.txt ARGS=--no-gui
make clean
```

At the debugger prompt, enter `n` to step, `s` to enter a function, `c` to continue,
or `q` to quit. `clean` removes caches, not the environment or source files.

## Algorithm explanation

1. **Parsing:** `Parser.parse()` reads the file once. It creates `Zone`,
   `Connection` and `MapData` objects. It checks syntax, defaults, duplicates,
   metadata, capacities and previously defined connection endpoints. Bad input
   reports its line and cause. Missing required records report end-of-file.
2. **Graph:** `Graph(data)` builds `neighbors[source][destination] = connection`.
   Both directions refer to the same connection object and share its capacity.
3. **Dijkstra:** select the pending zone with the smallest known score, update
   neighbors and record predecessors. Normal/priority entry costs one turn;
   restricted entry costs two. Blocked zones are skipped. Among equal travel
   times, prefer more priority zones. Priority never means zero movement time.
   Alphabetical names break remaining ties for repeatable output.
4. **Second path:** temporarily exclude each first-path connection, one at a
   time, and rerun Dijkstra. Keep the cheapest different path. Blocking an edge
   allows alternatives with shared junctions and works when the first path is
   a direct start-to-end edge. No graph objects are changed.
5. **Simulation:** expand each restricted entry into two stages: connection,
   then destination zone. For each drone, find the earliest departure with space
   for its *whole* journey. Compare the arrival times on the available routes,
   select the earlier arrival, then reserve its resources. An equal arrival
   prefers the first path. Group the reserved movements into turn lines.
6. **Selection:** `main.py` compares first-path-only scheduling with two-path
   scheduling and keeps the result using fewer turns. A tie keeps the first run.
7. **Visualization:** replay the chosen output; drawing cannot change its rules.

### Why reservations satisfy simultaneous movement

`used[(resource_name, turn)]` counts reservations, not a mutable live position.
A normal move reserves its connection and destination on that turn. A restricted
move reserves the connection on turn `t` and the destination on turn `t + 1`.
The connection is free again on `t + 1`; the drone must arrive then. Each drone
leaves an intermediate zone on the following turn, making its space available
to another drone in that turn. All reservations are checked before committing.

For `start -> restricted -> goal`, three drones can finish in five turns:

```text
D1-start-restricted
D1-restricted D2-start-restricted
D1-goal D2-restricted D3-start-restricted
D2-goal D3-restricted
D3-goal
```

The end zone has unlimited capacity and delivered drones disappear from active
tracking. The start also has unlimited capacity. Subject v3 explicitly ignores
`max_drones` metadata on these endpoints, including an otherwise invalid value;
the bracket/tag syntax must still be valid. Their zone types remain meaningful:
a restricted end still needs two turns. A blocked endpoint is unsolvable.
Unreachable maps are valid input, reported separately from parsing failures.
Repeated coordinates and self-links are accepted because the subject does not
forbid them; self-links are never useful to these positive-cost shortest paths.

### Trade-offs and complexity

This is a small routing heuristic, not a general optimal-flow solver. It uses
at most two fixed paths; drones wait at the start rather than at intermediate
zones. Full journey reservations prevent deadlocks and guarantee timely flight
arrivals. They can sacrifice throughput on other maps. The supplied benchmarks
reach their published optima; this does not prove optimality on arbitrary maps.

Let `V` be zones, `E` connections, `L` the first path's edge count, `S` the longest
expanded route, `N` drones, `K <= 2` routes and `T` the result's turn count:

- Graph construction: `O(V + E)` time and space.
- Dijkstra: `O(V² + E)` time and `O(V)` extra space. Scanning for the minimum
  keeps it easier to read than a heap implementation.
- Second path: at most `L` Dijkstra runs; `O(L(V² + E))` time. Candidate storage
  is at most `O(LV)`. Paths are found before scheduling, never once per drone.
- Scheduling: `O(K(N + T)S)` time, because failed departure times are never
  retried. Reservations and movement output take `O(NS + T)` space.
- Drawing: `O(V + E + N)` work per frame, at most 30 frames per second.

## Visualization

- **Space / Right:** advance one complete turn. **R:** restart. **Esc:** close.
- Zone colors come from the map. Unknown single-word colors such as `rainbow`
  are accepted and assigned a deterministic fallback color; `none` uses blue.
- A gold dot marks drones; the label shows a drone ID or the group size.
- Drones halfway along a connection are travelling toward a restricted zone.
- A double ring marks restricted zones; an X marks blocked zones.
- Hover a zone or a connection midpoint for its name, type/capacity and drone IDs.
  Large maps show names on hover to avoid covering the graph with labels.
- The counter shows turns and deliveries. Playback stops advancing at the final
  turn, leaving the final result visible until the window is closed.

This deliberately uses basic drawing and discrete steps: no sprites, images,
animation framework, camera or external assets. Coordinates are fitted to the
window. Zones with identical coordinates overlap in the display.

## Example input and output

Input: `maps/easy/01_linear_path.txt`:

```text
nb_drones: 2
start_hub: start 0 0 [color=green]
hub: waypoint1 1 0 [color=blue]
hub: waypoint2 2 0 [color=blue]
end_hub: goal 3 0 [color=red]
connection: start-waypoint1
connection: waypoint1-waypoint2
connection: waypoint2-goal
```

Expected stdout:

```text
D1-waypoint1
D1-waypoint2 D2-waypoint1
D1-goal D2-waypoint2
D2-goal
```

## Resources

- The supplied Fly-in subject v3.0, correction sheet and official maps define
  the requirements. The old `maps/README.md` quotes a 45-turn challenger record;
  the subject's newer 43-turn optimum is the target used here.
- [Python classes](https://docs.python.org/3/tutorial/classes.html).
- [Python argparse](https://docs.python.org/3/library/argparse.html).
- [Pygame tutorial and examples](https://www.pygame.org/docs/).
- [pygame.draw](https://www.pygame.org/docs/ref/draw.html),
  [pygame.font.Font.render](https://www.pygame.org/docs/ref/font.html),
  [pygame.event.get](https://www.pygame.org/docs/ref/event.html),
  [pygame.time.Clock.tick](https://www.pygame.org/docs/ref/time.html).
- [uv project commands](https://docs.astral.sh/uv/guides/projects/).

AI was used to review the supplied requirements and peer reference, write this
implementation, create the independent tests, and prepare the documentation.
The peer project informed the module order and two-path approach. This version
uses a different reservation-based scheduler, typed objects, one parsing pass
and a smaller step-based display. The developer should understand and verify
these choices before the review; see `WALKTHROUGH.md` for the reading order.
