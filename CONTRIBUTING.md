# Contributing

## Setup

```bash
uv sync --all-extras --dev
uv run pre-commit install
```

## Development

```bash
# Run tests
uv run pytest

# Lint
uv run ruff check .

# Format
uv run ruff format .

# Type check
uv run ty check .
```

## Pre-commit Hooks

Pre-commit hooks run Ruff lint + format automatically on each commit.
Install them once with `uv run pre-commit install`.
