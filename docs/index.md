# QKD Playground

**Interactive Quantum Key Distribution simulator and learning platform.**

Step through BB84, E91, and B92 protocols, visualize qubit states, and simulate eavesdropping attacks.

## What is QKD?

Quantum Key Distribution (QKD) uses quantum mechanics to establish shared secret keys between two parties. Any eavesdropping attempt disturbs the quantum states and is detectable.

## Supported Protocols

| Protocol | Year | Key Feature |
|----------|------|-------------|
| **BB84** | 1984 | Four-state, two-basis protocol (Bennett & Brassard) |
| **E91**  | 1991 | Entanglement-based with Bell inequality test (Ekert) |
| **B92**  | 1992 | Simplified two-state protocol (Bennett) |

## Quick Start

### Backend

```bash
cd backend
uv sync
uv run pytest
uv run uvicorn qkd_playground.api.app:create_app --factory
```

### Frontend

```bash
cd frontend
yarn install
yarn dev
```

## Tech Stack

- **Backend**: Python 3.11+, FastAPI, Qiskit
- **Frontend**: TypeScript, React 19, Vite
- **Testing**: pytest, vitest
- **Docs**: MkDocs Material
