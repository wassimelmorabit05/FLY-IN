MAP ?= maps/easy/01_linear_path.txt
ARGS ?=

.PHONY: install run debug clean lint lint-strict

install:
	uv sync

run:
	@uv run python main.py "$(MAP)" $(ARGS)

debug:
	@uv run python -m pdb main.py "$(MAP)" $(ARGS)

clean:
	find . -type d \( -name __pycache__ -o -name .mypy_cache \) -prune -exec rm -rf {} +
	find . -type f -name '*.py[co]' -delete

lint:
	uv run flake8 .
	uv run mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	uv run flake8 .
	uv run mypy . --strict
