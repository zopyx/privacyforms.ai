# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
