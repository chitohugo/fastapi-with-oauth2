#!/bin/sh
# Run MCP stdio inside the API container (same DB/env as the REST API).
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
exec docker compose -f "$ROOT/docker-compose.yml" exec -i character python /app/mcp_server.py
