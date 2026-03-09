.PHONY: help install sync test test-cov format format-check lint fix type-check check build clean all

# Default target
.DEFAULT_GOAL := help

# Variables
PACKAGE_NAME := privacyforms_ai
SRC_DIR := src
TEST_DIR := tests

help: ## Show this help message
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: sync ## Install dependencies (alias for sync)

sync: ## Install dependencies with uv
	uv sync --all-extras --dev

test: sync ## Run tests (installs dev dependencies if needed)
	uv run --dev pytest $(TEST_DIR)/

test-cov: sync ## Run tests with coverage (installs dev dependencies if needed)
	uv run --dev pytest $(TEST_DIR)/ --cov=$(PACKAGE_NAME) --cov-report=term --cov-report=html

format: ## Format code with ruff
	uv run ruff format .

format-check: ## Check code formatting
	uv run ruff format --check .

lint: format-check ## Run all linting checks (format, ruff, type-check)
	uv run ruff check .
	$(MAKE) type-check

fix: ## Auto-fix linting issues
	uv run ruff check --fix .
	uv run ruff format .

type-check: ## Run type checker
	uv run ty check --python-version 3.12 $(SRC_DIR)/

check: format lint test ## Run all checks (format, lint, type-check, test)

build: ## Build package
	uv run python -m build

clean: ## Clean build artifacts
	rm -rf build/ dist/ *.egg-info .pytest_cache .coverage htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

all: clean sync check build ## Run full pipeline: clean, install, check, build
