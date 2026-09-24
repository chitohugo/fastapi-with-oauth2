#!/bin/sh
set -e

host="${POSTGRES_HOST:-db}"
port="${POSTGRES_PORT:-5432}"

if [ "${WAIT_FOR_DB:-true}" = "true" ]; then
  echo "Waiting for PostgreSQL at ${host}:${port}..."
  until python - <<'PY'
import os
import socket
import sys

host = os.environ.get("POSTGRES_HOST", "db")
port = int(os.environ.get("POSTGRES_PORT", "5432"))
sock = socket.socket()
try:
    sock.settimeout(2)
    sock.connect((host, port))
except OSError:
    sys.exit(1)
finally:
    sock.close()
PY
  do
    sleep 1
  done
  echo "PostgreSQL is up."
fi

if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
  alembic upgrade head
fi

reload_flag=""
if [ "${UVICORN_RELOAD:-true}" = "true" ]; then
  reload_flag="--reload"
fi

workers="${UVICORN_WORKERS:-1}"
if [ "$workers" -gt 1 ] 2>/dev/null; then
  exec uvicorn main:app --host 0.0.0.0 --port 8000 --workers "$workers"
fi

exec uvicorn main:app --host 0.0.0.0 --port 8000 $reload_flag
