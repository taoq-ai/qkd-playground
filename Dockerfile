# ---------- FRONTEND BUILD ----------
FROM node:18 AS frontend-builder

WORKDIR /app/frontend
COPY frontend/ .
RUN corepack enable && corepack prepare yarn@4.6.0 --activate
RUN yarn install && yarn build

# ---------- BACKEND ----------
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Copy backend
COPY backend/ ./backend

# Copy built frontend
COPY --from=frontend-builder /app/frontend/dist ./backend/static

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install dependencies
RUN pip install uv

WORKDIR /app/backend
# Fix setuptools-scm issue
ENV SETUPTOOLS_SCM_PRETEND_VERSION=0.1.0
RUN uv sync

# Environment variables (defaults)
ENV HOST=0.0.0.0
ENV PORT=8000
ENV LOG_LEVEL=info

EXPOSE 8000

CMD ["sh", "-c", "uv run uvicorn qkd_playground.api.app:create_app --factory --host $HOST --port $PORT --log-level $LOG_LEVEL"]