#!/bin/sh
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
exec docker compose -f "$ROOT/docker-compose.yml" exec -i character python /app/mcp_server.py
