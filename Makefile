# Makefile for active-finance-agent

.PHONY: install install-browser test run-once schedule docker-build docker-up docker-down clean help

help:
	@echo "active-finance-agent - 主动式个人财务资产监控 Multi-Agent"
	@echo ""
	@echo "Available commands:"
	@echo "  install         - Install dependencies with uv"
	@echo "  install-browser  - Install playwright chromium browser"
	@echo "  test            - Run basic tests"
	@echo "  run-once category=tech  - Run once"
	@echo "  schedule        - Start scheduled monitoring"
	@echo "  docker-build  - Build docker image"
	@echo "  docker-up    - Start with docker-compose"
	@echo "  docker-down  - Stop docker-compose"
	@echo "  clean        - Clean cache"

install:
	uv sync

install-browser:
	uv run playwright install chromium

test:
	uv run python tests/test_basic.py

run-once:
	uv run python main.py --run-once

schedule:
	uv run python main.py --schedule

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
