# Validation report

Verified on 15 November 2026, using Python 3.12.14,
Pygame 2.6.1, flake8 7.5.0 and mypy 2.4.1 on Linux.

## Supplied benchmarks

Each result below was produced by running `main.py MAP --no-gui` as a separate
process. The independent checker replayed the printed output. It checked
adjacency, mandatory flight arrivals, all zone/link capacities and complete
delivery. The process exited successfully, with no diagnostics on stderr.

| Map | Published optimum | Actual turns | Movement rules |
|---|---:|---:|---|
| linear_path | 4 | 4 | Pass |
| simple_fork | 4 | 4 | Pass |
| basic_capacity | 4 | 4 | Pass |
| dead_end_trap | 8 | 8 | Pass |
| circular_loop | 10 | 10 | Pass |
| priority_puzzle | 6 | 6 | Pass |
| maze_nightmare | 13 | 13 | Pass |
| capacity_hell | 16 | 16 | Pass |
| ultimate_challenge | 26 | 26 | Pass |
| the_impossible_dream | 43 | 43 | Pass |

All nine mandatory maps match the published optimum, as does the optional
challenger. These targets come from subject v3.0, not the older maps README.
The correction sheet rounds the 25% margin upward while the subject states a
strict 1.25 multiplier; matching the exact targets satisfies both interpretations.

## Other checks

- `make lint`: passed the exact mandatory flake8/mypy commands.
- `make lint-strict`: passed, with no issues in all seven application files.
- 19 automated test methods passed, including 500 reproducible random graph cases.
  Disconnected or blocked random maps correctly return no route; reachable maps
  have their one-path and two-path outputs independently replayed.
- Parser defaults, metadata ordering, blank lines, comments, custom colors,
  unusual names, duplicate detection, forward references and malformed inputs.
- Single drone, restricted end, consecutive restricted zones, same-turn reuse,
  competing restricted arrivals and opposite-direction use of a shared link.
- 1,000 drones with million-sized capacities: complete in 2 turns.
- 10,000 drones on the linear map: complete in 10,002 turns, with the full output
  independently checked. No fixed drone-count limit is imposed by the code.
- Deliberately corrupted logs are rejected by the checker.
- Actual CLI success/error exit codes, missing arguments/files, invalid maps and
  unsolvable maps. Errors do not produce a traceback.
- `make install`, `make run` and `make debug` were exercised successfully.
- Pygame Space/Right/restart/close handling and full-delivery replay passed using
  SDL's dummy video driver; an unavailable display produces a handled error.
- Medium, hard and challenger frames were rendered and visually inspected.
  Large-map labels use hover details to avoid unreadable overlap.
- Arbitrary color names, repeated coordinates and extremely large integer
  coordinates are accepted without a graphical arithmetic crash.

## Limits of this evidence

These checks cover the supplied requirements and important edge cases; they are
not a proof for every possible input. The two-path scheduler is not guaranteed
to minimize turns on arbitrary graphs. It waits only at the start and considers
only the first and second paths. This keeps the implementation small.

The GUI was tested through SDL's dummy driver, rendered frames and injected
Pygame events. Physical keyboard/window behavior on the user's own computer has
not been tested here. Coincident zone coordinates overlap visually; very long
hover details and large drone lists are shortened to fit the window.

## Reproduce

From `fly_in`:

```sh
make install
make lint-strict
uv run python ../validation/run_checks.py
uv run python main.py maps/challenger/01_the_impossible_dream.txt --no-gui --stats
```

`validation` is a companion development folder, separate from the project
submitted for evaluation.
