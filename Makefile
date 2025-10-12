# Vega Framework - Test Makefile

.PHONY: help test test-unit test-functional test-integration test-all test-cov test-watch clean

help:
	@echo "Vega Framework - Test Commands"
	@echo "=============================="
	@echo ""
	@echo "Available commands:"
	@echo "  make test              - Run all tests"
	@echo "  make test-unit         - Run unit tests only"
	@echo "  make test-functional   - Run functional tests only"
	@echo "  make test-integration  - Run integration tests only"
	@echo "  make test-cov          - Run tests with coverage report"
	@echo "  make test-watch        - Run tests in watch mode"
	@echo "  make test-web          - Run web-related tests only"
	@echo "  make test-di           - Run DI-related tests only"
	@echo "  make test-events       - Run event system tests only"
	@echo "  make clean             - Clean test artifacts and cache"
	@echo ""

# Run all tests
test:
	poetry run pytest

# Run unit tests only
test-unit:
	poetry run pytest tests/unit -m unit -v

# Run functional tests only
test-functional:
	poetry run pytest tests/functional -m functional -v

# Run integration tests only
test-integration:
	poetry run pytest tests/integration -m integration -v

# Run all test categories
test-all:
	@echo "Running unit tests..."
	@poetry run pytest tests/unit -m unit -v
	@echo ""
	@echo "Running functional tests..."
	@poetry run pytest tests/functional -m functional -v
	@echo ""
	@echo "Running integration tests..."
	@poetry run pytest tests/integration -m integration -v

# Run tests with coverage
test-cov:
	poetry run pytest --cov=vega --cov-report=term-missing --cov-report=html

# Run tests in watch mode (requires pytest-watch)
test-watch:
	poetry run ptw

# Run web-related tests
test-web:
	poetry run pytest -m web -v

# Run DI-related tests
test-di:
	poetry run pytest -m di -v

# Run event system tests
test-events:
	poetry run pytest -m events -v

# Run tests excluding slow ones
test-fast:
	poetry run pytest -m "not slow" -v

# Run only failed tests
test-failed:
	poetry run pytest --lf -v

# Clean test artifacts
clean:
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf coverage.xml
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Install test dependencies
install-test:
	poetry install --with dev

# Run linting before tests
lint:
	poetry run black --check .
	poetry run isort --check-only .
	poetry run ruff check .

# Format code
format:
	poetry run black .
	poetry run isort .

# Run all checks (lint + test)
check: lint test

# Open coverage report in browser
show-cov:
	@if [ -d "htmlcov" ]; then \
		echo "Opening coverage report..."; \
		xdg-open htmlcov/index.html 2>/dev/null || open htmlcov/index.html 2>/dev/null || start htmlcov/index.html; \
	else \
		echo "No coverage report found. Run 'make test-cov' first."; \
	fi
