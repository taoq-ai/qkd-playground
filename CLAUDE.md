# QKD Playground — Developer Guide

## Project Overview
Interactive web-based Quantum Key Distribution simulator. Python backend (FastAPI + Qiskit) with TypeScript/React frontend.

## Architecture
Hexagonal architecture (ports & adapters) in both backend and frontend:
- `domain/` — Core business logic, models, abstract port interfaces
- `adapters/` — Concrete implementations of ports
- `api/` (backend) / `ui/` (frontend) — Driving adapters

## Commands

### Backend (from `backend/`)
- `uv sync` — Install dependencies
- `uv run pytest` — Run tests
- `uv run pytest tests/test_specific.py` — Run single test file
- `uv run ruff check .` — Lint
- `uv run ruff format .` — Format
- `uv run mypy src/` — Type check

### Frontend (from `frontend/`)
- `yarn install` — Install dependencies
- `yarn test` — Run tests (vitest)
- `yarn build` — Build for production
- `yarn dev` — Dev server
- `yarn lint` — Lint (eslint)
- `yarn format` — Format (prettier)
- `yarn typecheck` — Type check (tsc --noEmit)

### Docs (from root)
- `mkdocs serve` — Local docs server
- `mkdocs build` — Build docs

## Conventions
- Python: ruff for linting + formatting, mypy for types
- TypeScript: eslint + prettier, strict mode
- Tests alongside source in `tests/` directories
- All domain logic must be framework-agnostic (no FastAPI/React imports in domain/)
- Ports are abstract base classes (Python) or interfaces (TypeScript)
- Adapters implement ports and may depend on external libraries
