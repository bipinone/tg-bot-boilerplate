.PHONY: help install run docker-up docker-down test lint clean

help:
	@echo "Available commands:"
	@echo "  make install     - Install dependencies in virtualenv"
	@echo "  make run         - Run the bot in polling mode"
	@echo "  make docker-up   - Build and start containers with docker compose"
	@echo "  make docker-down - Stop running docker containers"
	@echo "  make test        - Run automated test suite"
	@echo "  make lint        - Check code formatting and types"
	@echo "  make clean       - Remove cached pyc and database files"

install:
	pip install -r requirements.txt

run:
	python -m app.main

docker-up:
	docker compose up -d --build

docker-down:
	docker compose down

test:
	python -m unittest discover tests

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
