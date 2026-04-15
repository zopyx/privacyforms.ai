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
| Build | `setuptools` + `build` |

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
# Install dependencies
make sync

# Run tests
make test

# Run tests with coverage
make test-cov

# Format code
make format

# Check formatting (CI)
make format-check

# Lint code
make lint

# Auto-fix linting issues
make fix

# Type check
make type-check

# Run the full local quality gate
make check

# Build release artifacts into dist/
make dist

# Upload release artifacts via twine
make upload

# Upload to another configured repository
make upload TWINE_REPOSITORY=testpypi

# Run CLI locally
uv run privacyforms-ai --help
uv run python -m privacyforms_ai.cli --help
```

`make` targets use a project-local `.uv-cache/` so they remain usable in sandboxed environments where the default uv cache directory is not writable.

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
├── _version.py      # Package version
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
- OS: Ubuntu

Jobs:
1. **test** - Run pytest with coverage
2. **lint** - ruff format, ruff check, ty check
3. **build** - Build package artifacts

## Release Workflow

### Make Targets

- `make dist` builds source and wheel artifacts into `dist/`
- `make upload` rebuilds artifacts and uploads `dist/*` with `twine`
- `TWINE_REPOSITORY` defaults to `pypi` and can be overridden, for example `testpypi`
- `TWINE_UPLOAD_ARGS` passes additional flags through to `twine upload`, for example `--skip-existing`

### Twine Credentials

`make upload` uses `uvx twine upload`. Credentials should come from one of:

- `~/.pypirc`
- `TWINE_USERNAME` and `TWINE_PASSWORD`
- `TWINE_USERNAME=__token__` and `TWINE_PASSWORD=<pypi-token>`

### Creating a New Release

1. Update the version consistently in:
   - `pyproject.toml`
   - `src/privacyforms_ai/_version.py`
   - `README.md` and `AGENTS.md` examples
   - any version assertions in tests
2. Refresh the lockfile if the project version changed:
   - `uv sync --all-extras --dev`
3. Verify the release candidate:
   - `make check`
4. Build release artifacts:
   - `make dist`
5. Upload artifacts:
   - `make upload`
   - For TestPyPI: `make upload TWINE_REPOSITORY=testpypi`
6. Finalize the git release:
   - `git add pyproject.toml src/privacyforms_ai/_version.py src/privacyforms_ai/__init__.py tests/ uv.lock CHANGELOG.md .gitattributes LICENSE`
   - `git commit -m "Release X.Y.Z"`
   - `git tag vX.Y.Z`
   - `git push origin HEAD`
   - `git push origin vX.Y.Z`

Agents should prefer these `make` targets over ad hoc `uv`, `build`, or `twine` commands so the release flow stays consistent.

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
- Use `make dist` to build release artifacts and `make upload` to publish them via twine
- The CLI entry point is `privacyforms-ai` (defined in `pyproject.toml`)
