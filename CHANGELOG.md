# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.6] - 2026-08-10

### Fixed
- `setup.py` reported a stale hardcoded version (`0.1.2`); it now reads `__version__` from `src/privacyforms_ai/_version.py` via AST parsing, keeping `_version.py` the single source of truth and working inside isolated build environments.

## [0.1.5] - 2026-08-10

### Added
- Added GitHub Actions publish workflows for PyPI and TestPyPI using trusted publishing (OIDC), plus weekly Dependabot updates for GitHub Actions and pip.
- Re-added `setup.py` for compatibility with legacy tooling.

### Fixed
- Added `# type: ignore` for `unresolved-attribute` on `conversation.system`.
- Switched CI lint to `uvx ruff` (always-latest ruff) and reformatted for ruff 0.16.1.

### Changed
- Refreshed `uv.lock`.

## [0.1.4] - 2026-04-15

### Added
- Added `LICENSE` file (MIT).
- Added `CHANGELOG.md`.
- Added `.gitattributes` for consistent LF line endings.
- Added `src/privacyforms_ai/_version.py` as the single source of truth for package versioning.
- Added `-v/--verbose` global CLI flag to control log verbosity (`-v` for INFO, `-vv` for DEBUG).
- Added CI `build` job to verify package artifacts with `twine check`.
- Added MIME type detection tests for known and unknown file extensions.
- Added shared test fixtures (`mock_response`, `mock_model`, `mock_conversation`) in `tests/conftest.py`.
- Enriched `pyproject.toml` with `authors`, `keywords`, `classifiers`, and `project.urls`.

### Changed
- **Packaging**: Removed redundant `setup.py`; build is now fully driven by `pyproject.toml`.
- **Versioning**: Centralized version management in `src/privacyforms_ai/_version.py` read dynamically by `pyproject.toml`.
- **Logging**: Replaced direct `stderr` prints with Python standard `logging` in `ai.py`.
- **Linting**: Expanded `ruff` rules to include security (`S`), pathlib (`PTH`), return checks (`RET`), and ruff-specific rules (`RUF`).
- **CLI UX**: Hardened `/clear` so model errors are echoed to stderr instead of terminating the chat session.
- **CLI UX**: Improved EOF (Ctrl+D) handling to print a friendly "Goodbye!" message.
- **CLI Style**: Replaced verbose `click.echo(click.style(...))` calls with `click.secho(...)`.
- **Exception handling**: Catches `llm.errors.ModelError` specifically in CLI commands instead of broad `Exception`.
- **Tests**: Refactored CLI tests to use shared fixtures; migrated prompt-log assertions to `caplog` for reliability.
- **Makefile**: Fixed `check` target to use `format-check` instead of `format` (prevents CI mutation). Removed redundant `format-check` duplication inside `check`. Aligned `build` target with CI by removing `--no-isolation`.
- **README & AGENTS.md**: Updated project structure diagrams, release instructions, and CLI examples to reflect all changes.

### Fixed
- Fixed setuptools deprecation warning by using `license = "MIT"` instead of a TOML table.
- Fixed broken README CLI example (`--json` → `--json-output`).
- Fixed `Makefile` vs CI build divergence.
- Aligned README with actual CI matrix (Ubuntu only).
- Scoped `S101` (assert) ignore to `tests/**` only instead of globally.

## [0.1.3] - 2026-04-15

Release 0.1.3 (uploaded to PyPI).
