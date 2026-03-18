# QKD Playground

**Interactive Quantum Key Distribution simulator and learning platform.**

Step through BB84, B92, E91, and SARG04 protocols, visualize qubit states, simulate eavesdropping attacks, and explore real-world channel imperfections — all powered by Qiskit quantum simulation.

## What is QKD?

Quantum Key Distribution (QKD) uses quantum mechanics to establish shared secret keys between two parties. Any eavesdropping attempt disturbs the quantum states and is detectable.

## Supported Protocols

| Protocol | Year | Key Feature |
|----------|------|-------------|
| **BB84** | 1984 | Four-state, two-basis protocol (Bennett & Brassard) |
| **B92**  | 1992 | Simplified two-state protocol (Bennett) |
| **E91**  | 1991 | Entanglement-based with Bell inequality test (Ekert) |
| **SARG04** | 2004 | PNS-attack resistant variant of BB84 (Scarani et al.) |

## Features

- **Step-by-step simulation** — Walk through each phase: preparation, transmission, measurement, sifting, error estimation, reconciliation, and privacy amplification
- **Eavesdropper simulation** — Toggle Eve on/off to see how intercept-resend attacks introduce detectable errors
- **Channel noise models** — Configure depolarizing noise and photon loss to simulate real-world fiber optic channels
- **Post-processing pipeline** — Information reconciliation (Cascade-inspired error correction) and privacy amplification (hash-based key compression)
- **Interactive circuit visualizer** — SVG quantum circuit diagram that updates live with each protocol phase
- **Educational concept panels** — Learn about qubits, superposition, no-cloning, Bell inequalities, PNS attacks, and more
- **Statistics dashboard** — QBER gauge, key efficiency chart, sift rate metrics

## Quick Start

### Install from PyPI

```bash
pip install qkd-playground
qkd-playground              # opens at http://localhost:8000
qkd-playground --port 3000  # custom port
```

The Python package includes the bundled frontend — no Node.js required.

### Docker

```bash
docker-compose up --build
# App available at http://localhost:8000
```

### Deploy to Hugging Face Spaces

1. Create a new Space at [huggingface.co/new-space](https://huggingface.co/new-space)
2. Select **Docker** as the Space SDK
3. Connect your GitHub repository or push directly
4. The Space will build and deploy automatically

The app will be available at `https://huggingface.co/spaces/<your-username>/qkd-playground`

### Development Setup

```bash
# Terminal 1 — Backend
cd backend && uv sync && uv run uvicorn qkd_playground.api.app:create_app --factory --reload

# Terminal 2 — Frontend
cd frontend && yarn install && yarn dev
```

Then open [http://localhost:5173](http://localhost:5173).

## Tech Stack

- **Backend**: Python 3.11+, FastAPI, Qiskit, Pydantic
- **Frontend**: TypeScript, React 19, Vite, Recharts
- **Packaging**: Frontend SPA bundled into the Python wheel via custom hatch build hook
- **Testing**: pytest (80 tests), vitest
- **Docs**: MkDocs Material
- **Deployment**: Docker, Hugging Face Spaces, PyPI, npm
