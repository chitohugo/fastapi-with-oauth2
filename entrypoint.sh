#!/bin/sh
set -e

# alembic revision --autogenerate -m "Added tables"
alembic upgrade head
uvicorn main:app --reload --host 0.0.0.0
