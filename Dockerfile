# ---------- FRONTEND BUILD ----------
FROM node:22-slim AS frontend-builder

WORKDIR /app/frontend
RUN corepack enable && corepack prepare yarn@4.6.0 --activate

# Install dependencies first (layer caching)
COPY frontend/package.json frontend/yarn.lock frontend/.yarnrc.yml ./
RUN yarn install --immutable

# Then copy source and build
COPY frontend/ .
RUN yarn build

# ---------- BACKEND ----------
FROM python:3.11-slim AS runtime

ENV PYTHONUNBUFFERED=1
ENV SETUPTOOLS_SCM_PRETEND_VERSION=0.1.0

WORKDIR /app

# Install curl for healthcheck and uv for dependency management
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Install Python dependencies first (layer caching)
WORKDIR /app/backend
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Copy backend source and install the project
COPY backend/ .
RUN uv sync --frozen --no-dev

# Copy built frontend into the static directory
COPY --from=frontend-builder /app/frontend/dist ./static

RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app

EXPOSE 7860 8000

COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

USER appuser

ENTRYPOINT ["/app/entrypoint.sh"]
