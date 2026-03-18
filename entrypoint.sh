#!/bin/sh
exec uv run --no-sync uvicorn qkd_playground.api.app:create_app \
  --factory \
  --host 0.0.0.0 \
  --port "${PORT:-7860}" \
  --log-level info
