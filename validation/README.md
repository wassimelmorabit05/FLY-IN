# Development checks

This folder is separate from `fly_in`, the project directory. The subject says
test programs are not submitted or graded. Keep this folder locally for checks.

From `fly_in`:

```sh
uv run python ../validation/run_checks.py
```

`verify_output.py` independently reconstructs drone positions from printed turn
lines. It does not read `Simulation.used`, its routes, or its scheduling logic.
It checks movement adjacency, normal/priority costs, two-turn restricted entries,
mandatory next-turn flight arrivals, shared link limits, end-of-turn zone limits,
duplicate movements, stationary output, complete delivery and termination.

The tests include all ten supplied maps, malformed inputs, deterministic random
maps, high capacities, opposite-direction traffic, merging restricted routes,
CLI failures and headless Pygame controls. Deliberately invalid logs also test
that the checker actually detects errors.
