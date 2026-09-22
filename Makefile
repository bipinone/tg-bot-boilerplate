.PHONY: help install dev run docker-up docker-down test lint format migrate seed clean module

help:
	@echo "TeleCore - Developer Workflow Commands:"
	@echo "  make install     - Install all Python dependencies"
	@echo "  make dev         - Launch the bot in development mode"
	@echo "  make test        - Execute test suite"
	@echo "  make seed        - Seed demo data and superadmin accounts"
	@echo "  make module name=<n> - Scaffold a new feature module"
	@echo "  make docker-up   - Build and start Docker stack in background"
	@echo "  make docker-down - Stop Docker containers"
	@echo "  make clean       - Remove cached bytecode and temp artifacts"

install:
	pip install -r requirements.txt

dev:
	python -m app.main

run: dev

test:
	python -m unittest discover tests

seed:
	python -m app.cli db:seed

module:
	@if [ -z "$(name)" ]; then echo "❌ Usage: make module name=<module_name>"; exit 1; fi
	python -m app.cli make:module $(name)

docker-up:
	docker compose up -d --build

docker-down:
	docker compose down

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
