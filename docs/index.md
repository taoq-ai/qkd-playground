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

### Install from PyPI

```bash
pip install qkd-playground
qkd-playground              # opens at http://localhost:8000
qkd-playground --port 3000  # custom port
```

The Python package includes the bundled frontend — no Node.js required.

### Development Setup

```bash
# Terminal 1 — Backend
cd backend && uv sync && uv run uvicorn qkd_playground.api.app:create_app --factory --reload

# Terminal 2 — Frontend
cd frontend && yarn install && yarn dev
```

Then open [http://localhost:5173](http://localhost:5173).

## Tech Stack

- **Backend**: Python 3.11+, FastAPI, Qiskit
- **Frontend**: TypeScript, React 19, Vite
- **Packaging**: Frontend SPA bundled into the Python wheel via custom hatch build hook
- **Testing**: pytest, vitest
- **Docs**: MkDocs Material
