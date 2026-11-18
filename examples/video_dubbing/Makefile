.PHONY: check lint typecheck test install

install:
	python -m pip install -e ".[dev]"

lint:
	ruff check src tests
	ruff format --check src tests

typecheck:
	mypy src/bodhan_dub

test:
	pytest

check: lint typecheck test
