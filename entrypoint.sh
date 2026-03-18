#!/bin/sh
exec uv run uvicorn qkd_playground.api.app:create_app \
  --factory \
  --host 0.0.0.0 \
  --port "${PORT:-8000}" \
  --log-level info
