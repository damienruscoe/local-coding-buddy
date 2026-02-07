.PHONY: help setup build up down logs shell test clean

# Default target
help:
	@echo "Local AI Coding Buddy - Makefile Commands"
	@echo ""
	@echo "Setup & Build:"
	@echo "  make setup    - Run initial setup"
	@echo "  make build    - Build Docker images"
	@echo ""
	@echo "Run:"
	@echo "  make up       - Start containers"
	@echo "  make down     - Stop containers"
	@echo "  make restart  - Restart containers"
	@echo ""
	@echo "Development:"
	@echo "  make logs     - View logs"
	@echo "  make shell    - Open orchestrator shell"
	@echo "  make test     - Run tests"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean    - Remove containers and volumes"
	@echo "  make rebuild  - Clean rebuild"

setup:
	@./scripts/setup.sh

build:
	@echo "Building containers..."
	@docker-compose build

up:
	@echo "Starting containers..."
	@docker-compose up -d
	@echo "Waiting for services to be ready..."
	@sleep 5
	@docker-compose ps

down:
	@echo "Stopping containers..."
	@docker-compose down

restart: down up

logs:
	@docker-compose logs -f

logs-orchestrator:
	@docker-compose logs -f orchestrator

logs-agent:
	@docker-compose logs -f agent-runtime

shell:
	@docker-compose exec orchestrator /bin/bash

shell-agent:
	@docker-compose exec agent-runtime /bin/bash

test:
	#@echo "Running orchestrator tests..."
	#@docker-compose exec orchestrator pytest /app/orchestrator/tests/ -v || true
	@echo "Running agent tests..."
	@docker-compose exec agent-runtime pytest /app/agents/tests/ -v || true
	@echo "Running agent tests v2..."
	docker-compose exec agent-runtime pytest agents/tests || true
	@echo "Running agent tests v1..."
	@docker-compose run --rm orchestrator pytest || true
	@echo "Running agent tests v2..."
	@docker-compose run --rm orchestrator pytest /app/agents/tests/ -v || true
	@echo "Running orchestrator tests v3..."
	docker-compose run --rm orchestrator pytest orchestrator/tests || true

status:
	@docker-compose exec orchestrator python -m orchestrator.main status

clean:
	@echo "Cleaning up..."
	@docker-compose down -v
	@docker system prune -f

rebuild: clean build up

# Project-specific commands (requires PROJECT_PATH in .env)
run:
	@docker-compose exec orchestrator python -m orchestrator.main run \
		--project /workspace \
		--request "$(REQUEST)"

scan:
	@docker-compose exec orchestrator python -m orchestrator.main scan \
		--project /workspace
