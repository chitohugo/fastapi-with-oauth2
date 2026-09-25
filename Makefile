COMPOSE=docker compose

.PHONY: up down build logs test migrate mcp mcp-http ngrok shell

up:
	$(COMPOSE) up -d

down:
	$(COMPOSE) down

build:
	$(COMPOSE) build

logs:
	$(COMPOSE) logs -f character

test:
	$(COMPOSE) exec character pytest -vv

migrate:
	$(COMPOSE) exec character alembic upgrade head

mcp:
	./scripts/run_mcp.sh

mcp-http:
	$(COMPOSE) --profile mcp up -d mcp-http

ngrok:
	$(COMPOSE) --profile ngrok up -d ngrok

shell:
	$(COMPOSE) exec character bash
