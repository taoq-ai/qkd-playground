# Architecture

QKD Playground uses **hexagonal architecture** (ports & adapters) to keep core quantum simulation logic independent of frameworks and infrastructure.

## Overview

```mermaid
graph TD
    subgraph "Driving Adapters"
        API[FastAPI REST API]
        UI[React UI]
        Tests[Test Suites]
    end

    subgraph "Domain"
        Models[Models<br/>Qubit, Basis, Key]
        Ports[Port Interfaces<br/>ChannelPort, MeasurementPort, ProtocolPort]
    end

    subgraph "Driven Adapters"
        Qiskit[Qiskit Adapter<br/>Quantum simulation]
        Noise[Noise Adapter<br/>Channel noise models]
    end

    API --> Ports
    UI --> API
    Tests --> Ports
    Ports --> Models
    Qiskit --> Ports
    Noise --> Ports
```

## Key Principles

1. **Domain is framework-agnostic** — No FastAPI or React imports in `domain/`
2. **Ports define contracts** — Abstract base classes (Python) or interfaces (TypeScript)
3. **Adapters are swappable** — Qiskit today, different simulator tomorrow
4. **Dependencies point inward** — Adapters depend on domain, never the reverse

## Deployment Model

The frontend SPA is bundled into the Python wheel at build time via a custom hatch build hook (`hatch_build.py`). FastAPI serves the static assets alongside the API, so users get a single-command install:

```bash
pip install qkd-playground
qkd-playground
```

The npm package (`@taoq-ai/qkd-playground`) remains available for consumers who want to embed the React components in their own applications.

## Backend Structure

```
backend/src/qkd_playground/
├── domain/
│   ├── models.py      # Qubit, Basis, BitValue, ProtocolResult
│   └── ports.py       # QuantumChannelPort, MeasurementPort, ProtocolPort
├── adapters/
│   ├── bb84.py        # BB84 protocol implementation
│   └── qiskit_adapter.py  # Qiskit-based implementations
├── api/
│   └── app.py         # FastAPI application factory (serves API + bundled frontend)
├── cli.py             # CLI entry point (qkd-playground command)
└── static/            # Bundled frontend SPA (auto-generated at build time)
```

### Domain Models

- **`Qubit`** — A qubit prepared in a specific basis with a bit value
- **`Basis`** — Rectilinear (Z) or Diagonal (X) measurement basis
- **`BitValue`** — Classical bit: 0 or 1
- **`ProtocolResult`** — Shared key, error rate, detection flags

### Port Interfaces

- **`QuantumChannelPort`** — Transmit qubits (may add noise/eavesdropping)
- **`MeasurementPort`** — Prepare and measure qubits
- **`ProtocolPort`** — Run full QKD protocol end-to-end or step-by-step
- **`RandomnessPort`** — Generate random basis and bit choices

## Frontend Structure

```
frontend/src/
├── domain/       # TypeScript interfaces mirroring backend types
├── adapters/     # API client implementing SimulationPort
└── ui/           # React components (presentation layer)
```

The frontend follows the same hexagonal pattern: UI components depend only on domain types, and adapters handle API communication.
