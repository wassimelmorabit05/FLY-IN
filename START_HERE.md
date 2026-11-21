# Fly-in for Abdo

The application is in `fly_in`. Open that folder in your editor.
It contains seven Python files, the maps, a Makefile and the dependency files.

From this extracted folder:

```sh
cd fly_in
uv sync
uv run python main.py maps/easy/01_linear_path.txt
```

Press Space to advance a turn, R to restart, or Esc to close the window.
For terminal-only output, append `--no-gui` to the command.

Read `fly_in/WALKTHROUGH.md` starting at `main.py`. It follows the actual call
order: Parsing -> Graph -> Dijkstra -> Second Path -> Simulation -> Visualization.
`fly_in/README.md` explains installation and algorithm choices.
`fly_in/TEST_REPORT.md` records the checks and their limits.

The `validation` folder contains development tests and an independent movement
checker. Run it from `fly_in` with:

```sh
uv run python ../validation/run_checks.py
```

Use the contents of `fly_in` as the project repository root. Keep `validation`
as a separate local test folder, as the subject requests. The README uses the
login `abguenbo`; change the author list there if your submission has teammates
or uses a different login. The README explicitly describes the AI assistance.
