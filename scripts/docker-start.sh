#!/bin/sh
set -e
echo "[docker-start] PORT=${PORT:-8080} DEBUG=${DEBUG:-unset}"
python -c "from app.main import app; print('[docker-start] loaded', app.title)"
exec python -m uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8080}"
