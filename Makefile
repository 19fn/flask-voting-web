# Entry point for common local development tasks. Run `make` to list them.
# Works with GNU Make and the Make shipped with macOS (3.81).

# Python used to create the virtual environment (needs 3.14+). Override with
# e.g. `make install PYTHON=python3.14`.
PYTHON ?= $(shell command -v python3.14 2>/dev/null || command -v python3)
VENV   ?= venv
VPY    := $(VENV)/bin/python
COMPOSE := docker compose

# Port and host for `make run`.
HOST ?= 127.0.0.1
PORT ?= 5000

.DEFAULT_GOAL := help
.PHONY: help install run up down logs reset lint test test-integration check

help: ## List the available targets
	@echo "Usage: make <target>"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*## "} {printf "  %-18s %s\n", $$1, $$2}'

# Stamp file: dependencies are (re)installed when the requirements change, so
# `make test` and `make run` also work right after a fresh clone.
STAMP := $(VENV)/.deps-installed

$(STAMP): requirements.txt requirements-dev.txt
	$(PYTHON) -m venv $(VENV)
	$(VPY) -m pip install --upgrade pip
	$(VPY) -m pip install -r requirements-dev.txt
	touch $(STAMP)

install: ## Create the virtual environment and install runtime and dev dependencies
	$(MAKE) -B $(STAMP)

run: $(STAMP) ## Run the app locally with Flask (DATABASE_URL or DB_*; defaults to SQLite db.sqlite3)
	@if [ -z "$$DATABASE_URL" ] && [ -z "$$DB_HOST" ]; then \
		echo "No DATABASE_URL or DB_HOST set: using SQLite file db.sqlite3"; \
		export DATABASE_URL="sqlite:///$(CURDIR)/db.sqlite3"; \
	fi; \
	export FLASK_SECRET_KEY="$${FLASK_SECRET_KEY:-dev-only-secret-key}"; \
	exec $(VPY) -m flask --app app run --host $(HOST) --port $(PORT)

.env:
	cp .env.example .env
	@echo "Created .env from .env.example; adjust the placeholder values if you like."

up: .env ## Build and start the Compose stack in the background (http://localhost:8080)
	$(COMPOSE) up --build -d

down: ## Stop the Compose stack (votes are kept in the db-data volume)
	$(COMPOSE) down

logs: ## Follow the Compose stack logs
	$(COMPOSE) logs -f

reset: ## Stop the Compose stack and delete its volumes (all votes are lost)
	$(COMPOSE) down -v

lint: $(STAMP) ## Lint and check formatting with Ruff
	$(VPY) -m ruff check .
	$(VPY) -m ruff format --check .

test: $(STAMP) ## Run the unit tests (SQLite, no Docker needed)
	$(VPY) -m pytest tests/unit

test-integration: ## Run the integration tests against a throwaway MySQL (needs Docker)
	tests/integration/run.sh

check: lint test ## Run every local quality gate (lint and unit tests)
