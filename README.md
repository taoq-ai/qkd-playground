# QKD Playground

[![CI](https://github.com/taoq-ai/qkd-playground/actions/workflows/ci.yml/badge.svg)](https://github.com/taoq-ai/qkd-playground/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/qkd-playground)](https://pypi.org/project/qkd-playground/)
[![npm](https://img.shields.io/npm/v/@qkd-playground/frontend)](https://www.npmjs.com/package/@qkd-playground/frontend)
[![Docs](https://img.shields.io/badge/docs-mkdocs-blue)](https://taoq-ai.github.io/qkd-playground)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue)](LICENSE)

Interactive web-based Quantum Key Distribution simulator and learning platform.
Step through BB84, E91, and B92 protocols, visualize qubit states, and simulate eavesdropping attacks.

## Quick Start

### Backend

```bash
cd backend
uv sync
uv run pytest          # run tests
uv run uvicorn qkd_playground.api.app:create_app --factory  # start API
```

### Frontend

```bash
cd frontend
yarn install
yarn dev               # dev server
yarn test              # run tests
```

### Documentation

```bash
pip install mkdocs-material
mkdocs serve           # local docs at http://127.0.0.1:8000
```

## Architecture

This project uses **hexagonal architecture** (ports & adapters):

- **Domain** — Core business logic, models, and abstract port interfaces (no framework dependencies)
- **Adapters** — Concrete implementations (Qiskit for quantum sim, API clients)
- **Driving adapters** — FastAPI (backend) and React UI (frontend)

## Tech Stack

| Layer    | Technology                     |
|----------|--------------------------------|
| Backend  | Python 3.11+, FastAPI, Qiskit  |
| Frontend | TypeScript, React 19, Vite     |
| Testing  | pytest, vitest                 |
| Docs     | MkDocs Material                |
| CI/CD    | GitHub Actions                 |

## License

[Apache License 2.0](LICENSE)
