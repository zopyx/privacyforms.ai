.PHONY: help install sync test test-cov format format-check lint fix type-check check build dist upload clean all

# Default target
.DEFAULT_GOAL := help

# Variables
PACKAGE_NAME := privacyforms_ai
SRC_DIR := src
TEST_DIR := tests
UV_CACHE_DIR := .uv-cache
TWINE_REPOSITORY ?= pypi
TWINE_UPLOAD_ARGS ?=

help: ## Show this help message
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: sync ## Install dependencies (alias for sync)

sync: ## Install dependencies with uv
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv sync --all-extras --dev

test: sync ## Run tests (installs dev dependencies if needed)
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv run --dev pytest $(TEST_DIR)/

test-cov: sync ## Run tests with coverage (installs dev dependencies if needed)
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv run --dev pytest $(TEST_DIR)/ --cov=$(PACKAGE_NAME) --cov-report=term --cov-report=html

format: ## Format code with ruff
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv run ruff format .

format-check: ## Check code formatting
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv run ruff format --check .

lint: format-check ## Run all linting checks (format, ruff, type-check)
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv run ruff check .
	$(MAKE) type-check

fix: ## Auto-fix linting issues
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv run ruff check --fix .
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv run ruff format .

type-check: ## Run type checker
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv run ty check --python-version 3.12 $(SRC_DIR)/

check: format lint test ## Run all checks (format, lint, type-check, test)

build: sync ## Build package
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv run python -m build --no-isolation

dist: clean build ## Build release artifacts into dist/

upload: dist ## Upload release artifacts from dist/ via twine
	UV_CACHE_DIR=$(UV_CACHE_DIR) uvx twine upload --repository $(TWINE_REPOSITORY) $(TWINE_UPLOAD_ARGS) dist/*

clean: ## Clean build artifacts
	rm -rf build/ dist/ *.egg-info .pytest_cache .coverage htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

all: clean sync check build ## Run full pipeline: clean, install, check, build
