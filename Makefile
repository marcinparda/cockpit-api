DC = docker compose -f docker-compose.dev.yml
API = $(DC) run --rm cockpit_api

# ── App ──────────────────────────────────────────────────────────────────────
up:
	$(DC) up

up-d:
	$(DC) up -d

down:
	$(DC) down

restart:
	$(DC) restart

logs:
	$(DC) logs -f

# ── Dependencies ─────────────────────────────────────────────────────────────
install:
	poetry install

# ── Database ─────────────────────────────────────────────────────────────────
migrate:
	$(API) alembic upgrade head

downgrade:
	$(API) alembic downgrade -1

# Usage: make migration m="add_users_table"
migration:
	$(API) alembic revision --autogenerate -m "$(m)"

# ── Tests ────────────────────────────────────────────────────────────────────
test:
	poetry run pytest

test-cov:
	poetry run pytest --cov=src

test-docker:
	$(API) pytest

# ── Misc ─────────────────────────────────────────────────────────────────────
shell:
	$(API) bash

.PHONY: up up-d down restart logs install migrate downgrade migration test test-cov test-docker shell
