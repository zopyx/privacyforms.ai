# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- CLI `prompt` command now supports `--attachment` / `-a` (repeatable) for file attachments.
- CLI `chat` command now supports `--attachment` / `-a` (repeatable) for file attachments passed with every turn.
- New `python -m privacyforms_ai` entry point via `__main__.py`.
- `--version` flag on the root CLI.
- GitHub Actions CI badge in README.md.
- Multi-version testing via `tox.ini` for Python 3.12, 3.13, 3.14, 3.14t, 3.15, 3.15t (free-threaded).
- Dependency vulnerability audit via `make audit` (uses `uv-secure`).
- GitHub Actions CI now runs the `tox` matrix across Python 3.12, 3.13, 3.14, and 3.14t.

### Changed
- Prompt logging now emits metadata only (`text_length`, `system_length`) at INFO level (`-v`); full prompt text is logged only at DEBUG level (`-vv`) to avoid leaking sensitive input.
- README updated to describe the new logging levels, attachment options, `python -m` usage, and 100 % coverage target.
- AGENTS.md project structure updated to include `__main__.py`, `tox.ini`, and `test_coverage_100.py`.
- Removed redundant `setup.py`; build configuration now lives entirely in `pyproject.toml`.
- Coverage target raised to 100 %; `make test-cov` now fails below 100 %.

## [0.1.7] - 2026-08-18

### Added
- Comprehensive coverage for `AI` and CLI branches pushing total coverage to 100% (new `tests/test_coverage_98.py`).

### Changed
- Added `# pragma: no cover` to `cli.py` main guard to exclude unreachable entry point from coverage.
- Updated `.gitignore` to exclude `great-docs` build artifacts.

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
