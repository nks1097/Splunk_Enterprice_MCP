.PHONY: help install test test-unit test-integration lint format clean docker-build run

help:
	@echo "Splunk Enterprise MCP Server - Automation Targets:"
	@echo "  install          - Install dependencies in editable mode"
	@echo "  test             - Run unit tests"
	@echo "  test-unit        - Run unit test suite only"
	@echo "  test-integration - Run integration tests against live Splunk instance"
	@echo "  lint             - Check formatting and typing"
	@echo "  format           - Auto-format code using ruff"
	@echo "  docker-build     - Build production Docker image"
	@echo "  run              - Start MCP server in STDIO mode"

install:
	pip install -e ".[dev]"

test: test-unit

test-unit:
	pytest tests/unit -v

test-integration:
	pytest tests/integration -v -m integration

lint:
	ruff check src tests

format:
	ruff format src tests

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .ruff_cache dist build *.egg-info

docker-build:
	docker build -t splunk-enterprise-mcp:latest .

run:
	splunk-mcp --transport stdio
