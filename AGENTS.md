# AGENTS.md - PrivacyForms AI

Project context and conventions for AI coding agents.

## Project Overview

PrivacyForms AI is a Python CLI tool for interacting with LLM models via the `llm` library. It provides commands to list models, send single prompts, and engage in interactive chat sessions.

## Tech Stack

| Component | Tool |
|-----------|------|
| Package Manager | `uv` (modern Python package manager) |
| CLI Framework | `click` |
| LLM Integration | `llm` (Simon Willison's library) |
| Linting/Formatting | `ruff` |
| Type Checking | `ty` (Google's fast type checker) |
| Testing | `pytest` with `pytest-cov` |
| Build | `hatchling` |

## Development Workflow

### Setup

```bash
# Install dependencies
uv sync --all-extras --dev

# Activate virtual environment
source .venv/bin/activate
```

### Common Commands

```bash
# Run tests
uv run pytest tests/ -v

# Run tests with coverage
uv run pytest tests/ -v --cov=privacyforms_ai --cov-report=term

# Format code
uv run ruff format .

# Check formatting (CI)
uv run ruff format --check .

# Lint code
uv run ruff check .

# Auto-fix linting issues
uv run ruff check --fix .

# Type check
uv run ty check --python-version 3.12 src/

# Build package
uv run python -m build

# Run CLI locally
uv run privacyforms-ai --help
uv run python -m privacyforms_ai.cli --help
```

## Code Style

### General

- Python 3.12+ target (minimum version)
- Line length: 100 characters
- Use double quotes for strings
- 4 spaces indentation

### Type Annotations

- Always use type annotations for function parameters and return types
- Use `|` for union types (e.g., `str | None` instead of `Optional[str]`)
- Use built-in generics (e.g., `list[dict[str, str]]` instead of `List[Dict[str, str]]`)

```python
# Good
def get_models() -> list[dict[str, str]]:
    ...

def process(data: str | None) -> None:
    ...
```

### Imports

- Group: stdlib, third-party, first-party
- Sorted alphabetically within groups (enforced by ruff)

```python
"""Module docstring."""

import json
from typing import Any  # If needed, prefer built-in generics

import click
import llm

from .ai import AI
```

### Error Handling

- Use `raise ... from e` when wrapping exceptions
- Use `click.ClickException` for CLI errors

```python
try:
    result = some_operation()
except Exception as e:
    raise click.ClickException(str(e)) from e
```

### CLI Commands

- Add return type annotation `-> None` to all click commands
- Use `click.style()` for colored output
- Use `click.prompt()` for interactive input
- Use `click.echo()` for output (not print)

```python
@cli.command()
@click.argument("name")
def greet(name: str) -> None:
    """Greet someone."""
    click.echo(click.style(f"Hello {name}!", fg="green"))
```

## Project Structure

```
src/privacyforms_ai/
├── __init__.py      # Package exports
├── ai.py            # AI class for LLM interactions
└── cli.py           # Click CLI commands

tests/
├── conftest.py      # Pytest fixtures
├── test_ai.py       # Tests for AI class
└── test_cli.py      # Tests for CLI commands
```

### Adding New Commands

1. Add function to `src/privacyforms_ai/cli.py`:
   - Use `@cli.command()` decorator
   - Add type annotations
   - Use `click.argument()` for required args
   - Use `click.option()` for optional flags

2. Add tests to `tests/test_cli.py`:
   - Use `CliRunner` for testing
   - Mock LLM calls with monkeypatch

## Testing Conventions

### Test Structure

```python
class TestFeatureName:
    """Test cases for a specific feature."""

    def test_specific_behavior(self, runner, monkeypatch):
        """Test description."""
        # Arrange
        # Act
        # Assert
```

### Mocking LLM

Always mock the `llm` library calls in tests:

```python
def test_prompt(self, runner, monkeypatch):
    class MockResponse:
        def text(self):
            return "Hello!"

    class MockModel:
        def prompt(self, prompt, system=None):
            return MockResponse()

    monkeypatch.setattr("llm.get_model", lambda key: MockModel())
    
    result = runner.invoke(cli, ["prompt", "gpt-4o", "Hi"])
    assert result.exit_code == 0
    assert "Hello!" in result.output
```

## CI/CD

GitHub Actions runs on:
- Python: 3.12, 3.13, 3.14, 3.14t (free-threaded)
- OS: Ubuntu, macOS

Jobs:
1. **test** - Run pytest with coverage
2. **lint** - ruff format, ruff check, ty check
3. **build** - Build package artifacts

## Adding Dependencies

Edit `pyproject.toml`:

```toml
[project.dependencies]
new-package = ">=1.0"

[project.optional-dependencies]
dev = [
    "new-dev-package>=1.0",
]
```

Then run:
```bash
uv sync --all-extras --dev
```

## Configuration Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Project metadata, dependencies, tool config |
| `uv.lock` | Locked dependency versions (auto-generated) |
| `.python-version` | Default Python version for uv |
| `.github/workflows/ci.yml` | CI pipeline |
| `.gitignore` | Git ignore patterns |

## Tips

- Use `uv` for all Python operations, not `pip` directly
- Keep `uv.lock` committed for reproducible builds
- Run all checks locally before pushing: format, lint, type-check, test
- The CLI entry point is `privacyforms-ai` (defined in `pyproject.toml`)
