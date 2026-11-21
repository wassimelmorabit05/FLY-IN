# Read the code in execution order

Start with this command and `main.py`. Read only one stage at a time.

```sh
uv run python main.py maps/easy/01_linear_path.txt --no-gui
```

## 1. The actual entry point

At the bottom of `main.py`:

```python
if __name__ == "__main__":
    sys.exit(Main().run())
```

Running the file directly makes `__name__` equal to `"__main__"`. Python creates
a `Main` object and calls its `run()` method. The integer it returns becomes the
process exit status: 0 means success, 1 means a handled project error.
Importing `main` does not run this block.

Inside `run()`, `arguments()` reads the filename and flags. The `try` block runs
the stages below; `except` blocks turn expected failures into readable errors.

**Small exercise:** locate the exact line that stops an unsolvable map before
simulation begins. Explain why an empty path must be checked there.

## 2. Parsing: text becomes objects

Read `Parser.parse()` in `parser.py`, then follow these calls:

1. `parse_line()` chooses the handler using the word before the first colon.
2. `parse_zone()` handles `start_hub`, `end_hub` and `hub`.
3. `parse_connection()` handles connections.
4. `metadata()`, `integer()` and `positive_integer()` validate small pieces.

When you see `Zone(...)`, `Connection(...)` or `MapData()`, briefly open their
classes at the top of `graph.py`. They are containers for named attributes.
Then return to the parser. `Graph` itself is constructed in the next stage.

For `hub: waypoint1 1 0 [color=blue]`, the result includes:

```python
zone.name == "waypoint1"
zone.x == 1
zone.kind == "normal"
zone.color == "blue"
zone.capacity == 1
```

The default values are important: omitted metadata still has a meaning.
The parser does not decide whether a route exists.

## 3. Graph: objects become neighbors

Back in `main.py`, `Graph(data)` builds the adjacency dictionary in `graph.py`.

```python
graph.neighbors["start"]["waypoint1"]
```

This gives the `Connection` object between those zones. The reverse lookup
returns the same object. A bidirectional link has one shared capacity.

## 4. Dijkstra: find the first route

Read `Dijkstra.find_path()` in `algorithm.py`.

| Variable | Meaning |
|---|---|
| `distances` | Best score found so far for each reached zone |
| `pending` | Reached zones still waiting to be processed |
| `visited` | Zones whose best distance has been settled |
| `previous` | Predecessor to follow when rebuilding the route |

For the easy linear map the result is:

```python
["start", "waypoint1", "waypoint2", "goal"]
```

The score is `(turns, -priority_count)`. Python compares tuples from left to
right: travel time first, priority count only on equal times. Every edge still
adds at least one real turn, so this tie-break does not introduce zero-cost
movement. `rebuild_path()` follows predecessors backward, then reverses them.

## 5. Second path: reuse Dijkstra

Read `SecondPath.find_path()` in `second_path.py`.
It excludes each connection of the first route, one at a time, and searches
again. A different route must avoid at least one connection of the first route.
This finds alternatives even if the routes share some zones. An empty list means
there is no alternative; that is normal for a linear map.

## 6. Simulation: reserve, then print

Read `Route.__init__()`, then `Simulation.run()` in `simulation.py`.
Each route becomes the list of places a drone visits after leaving the start.

| Route type | Stages after the start |
|---|---|
| `start -> a -> goal`, with normal `a` | `a`, `goal` |
| `start -> r -> goal`, with restricted `r` | `start-r`, `r`, `goal` |

`resources` adds the capacity checks belonging to each stage. A one-turn move
uses its connection and destination. A two-turn move uses the connection first,
then the destination. The calendar is a dictionary:

```python
self.used[("a", 2)] = 1
```

This means one drone has reserved zone `a` on turn 2.
`can_depart()` checks the entire route against this calendar. `reserve()` writes
the reservations only after the whole journey fits. `Drone` records the chosen
route and departure turn. A later drone can be scheduled to launch earlier than
an earlier ID if another route has room; IDs are identifiers, not departure order.

`next_departure` is only a small optimization: once a departure is impossible,
adding more reservations cannot make it possible again. We need not retry it.

Finally, `output()` places every movement into its absolute turn. Drones waiting
at the start are absent from those lines. The schedule is planned before replay,
so it does not mutate one drone's live position and then decide another's move.

Back in `main.py`, compare the one-path and two-path results. Print the shorter
result, one turn per line. Never add debug labels to stdout during validation;
use `print(..., file=sys.stderr)` for those.

## 7. Visualization: replay an already valid result

Remove `--no-gui` when you are ready to read `visualization.py`.
`Visualizer` receives the same graph and the printed turn lines.
`positions` maps a drone ID to its current zone or connection name.

- `map_points()`: fit the map into screen coordinates; use edge midpoints for flight.
- `advance()`: apply the next output line; delete delivered drones.
- `draw()`: draw connections, zones, drone dots and counters.
- `draw_details()`: show the hovered resource's information.
- `show()`: process events, draw, display the frame, limit frame rate, repeat.

The Pygame calls to learn, in order:

| Call | Purpose |
|---|---|
| `pygame.display.init()` / `pygame.font.init()` | Initialize the used subsystems |
| `pygame.display.set_mode((1120, 720))` | Create the window's drawing surface |
| `pygame.font.Font(None, 20)` | Use Pygame's built-in font |
| `pygame.event.get()` | Read queued key and close-window events |
| `screen.fill(...)` | Clear the previous frame |
| `pygame.draw.line()` / `pygame.draw.circle()` | Draw basic shapes |
| `font.render()` then `screen.blit()` | Create text pixels, then draw them |
| `pygame.display.flip()` | Show the completed frame |
| `clock.tick(30)` | Limit display work to 30 frames per second |
| `pygame.quit()` | Release Pygame resources when leaving |

A display frame is not a simulation turn. The window can redraw 30 times while
the simulation remains on turn 2. Only Space or Right advances it.

## Later: the correction-sheet modification

The live coding task asks for one zone's occupancy and one connection's capacity
use per turn. Start from `Simulation.used`: it already contains the per-turn
counts. Keep a named `Simulation` object in `main.py` for the chosen run so you
can inspect that calendar. The GUI hover reports physical positions; an instant
normal connection traversal is recorded in the calendar but has no end-of-turn
drone sitting on that connection. This distinction matters for that task.
