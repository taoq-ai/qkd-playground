"""FastAPI application factory."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from qkd_playground.adapters.b92 import B92Protocol
from qkd_playground.adapters.bb84 import BB84Protocol
from qkd_playground.adapters.qiskit_adapter import (
    DefaultRandomness,
    EavesdroppingChannel,
    IdealQuantumChannel,
    QiskitMeasurementAdapter,
)
from qkd_playground.domain.models import (
    ProtocolType,
    StepResult,
)

if TYPE_CHECKING:
    from qkd_playground.domain.ports import ProtocolPort


class CreateSimulationRequest(BaseModel):
    """Request body for creating a new simulation."""

    protocol: str = Field(default="bb84", description="Protocol type")
    num_qubits: int = Field(default=20, ge=4, le=1000, description="Number of qubits")
    eavesdropper: bool = Field(default=False, description="Enable eavesdropper")


class StepResponse(BaseModel):
    """API response for a protocol step."""

    phase: str
    step_index: int
    description: str
    alice_bits: list[int]
    alice_bases: list[str]
    bob_bases: list[str]
    bob_results: list[int]
    matching_bases: list[bool]
    sifted_key_alice: list[int]
    sifted_key_bob: list[int]
    error_rate: float | None
    eavesdropper_detected: bool | None
    shared_key: list[int]
    conclusive_mask: list[bool] = []
    chsh_value: float | None = None
    is_complete: bool

    @classmethod
    def from_step_result(cls, step: StepResult, complete: bool) -> StepResponse:
        """Convert domain StepResult to API response."""
        return cls(
            phase=step.phase.value,
            step_index=step.step_index,
            description=step.description,
            alice_bits=[b.value for b in step.alice_bits],
            alice_bases=[b.value for b in step.alice_bases],
            bob_bases=[b.value for b in step.bob_bases],
            bob_results=[b.value for b in step.bob_results],
            matching_bases=step.matching_bases,
            sifted_key_alice=[b.value for b in step.sifted_key_alice],
            sifted_key_bob=[b.value for b in step.sifted_key_bob],
            error_rate=step.error_rate,
            eavesdropper_detected=step.eavesdropper_detected,
            shared_key=[b.value for b in step.shared_key],
            conclusive_mask=step.conclusive_mask,
            chsh_value=step.chsh_value,
            is_complete=complete,
        )


class SimulationState(BaseModel):
    """Full state of a simulation."""

    simulation_id: str
    protocol: str
    num_qubits: int
    eavesdropper: bool
    current_step: StepResponse | None
    steps: list[StepResponse]
    is_complete: bool


class RunResponse(BaseModel):
    """Response for running the full protocol."""

    simulation_id: str
    steps: list[StepResponse]
    shared_key: list[int]
    error_rate: float
    sifted_key_length: int
    raw_key_length: int
    eavesdropper_detected: bool


# In-memory session storage
_sessions: dict[str, dict[str, Any]] = {}


def _create_protocol(
    protocol_type: str,
    eavesdropper: bool,
) -> ProtocolPort:
    """Create a protocol instance based on type."""
    measurement = QiskitMeasurementAdapter()
    channel: IdealQuantumChannel | EavesdroppingChannel
    if eavesdropper:
        channel = EavesdroppingChannel(measurement)
    else:
        channel = IdealQuantumChannel()
    randomness = DefaultRandomness()
    if protocol_type == "b92":
        return B92Protocol(measurement, channel, randomness)
    return BB84Protocol(measurement, channel, randomness)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="QKD Playground",
        description="Quantum Key Distribution simulator API",
        version="0.2.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/protocols")
    async def list_protocols() -> list[dict[str, str]]:
        return [{"name": p.value, "label": p.name} for p in ProtocolType]

    @app.post("/simulation/create")
    async def create_simulation(
        req: CreateSimulationRequest,
    ) -> dict[str, str]:
        sim_id = str(uuid.uuid4())
        protocol = _create_protocol(req.protocol, req.eavesdropper)
        protocol.reset(req.num_qubits)
        _sessions[sim_id] = {
            "protocol": protocol,
            "protocol_type": req.protocol,
            "num_qubits": req.num_qubits,
            "eavesdropper": req.eavesdropper,
            "steps": [],
        }
        return {"simulation_id": sim_id}

    @app.post("/simulation/{sim_id}/step")
    async def step_simulation(sim_id: str) -> StepResponse:
        if sim_id not in _sessions:
            raise HTTPException(404, "Simulation not found")
        session = _sessions[sim_id]
        protocol: ProtocolPort = session["protocol"]
        if protocol.is_complete():
            raise HTTPException(400, "Simulation already complete")
        step = protocol.step()
        resp = StepResponse.from_step_result(step, protocol.is_complete())
        session["steps"].append(resp)
        return resp

    @app.get("/simulation/{sim_id}/state")
    async def get_state(sim_id: str) -> SimulationState:
        if sim_id not in _sessions:
            raise HTTPException(404, "Simulation not found")
        session = _sessions[sim_id]
        protocol: ProtocolPort = session["protocol"]
        steps: list[StepResponse] = session["steps"]
        return SimulationState(
            simulation_id=sim_id,
            protocol=session["protocol_type"],
            num_qubits=session["num_qubits"],
            eavesdropper=session["eavesdropper"],
            current_step=steps[-1] if steps else None,
            steps=steps,
            is_complete=protocol.is_complete(),
        )

    @app.post("/simulation/{sim_id}/run")
    async def run_simulation(sim_id: str) -> RunResponse:
        """Run remaining steps of simulation to completion."""
        if sim_id not in _sessions:
            raise HTTPException(404, "Simulation not found")
        session = _sessions[sim_id]
        protocol: ProtocolPort = session["protocol"]

        while not protocol.is_complete():
            step = protocol.step()
            resp = StepResponse.from_step_result(step, protocol.is_complete())
            session["steps"].append(resp)

        steps: list[StepResponse] = session["steps"]
        last = steps[-1]
        return RunResponse(
            simulation_id=sim_id,
            steps=steps,
            shared_key=last.shared_key,
            error_rate=last.error_rate or 0.0,
            sifted_key_length=len(last.sifted_key_alice),
            raw_key_length=session["num_qubits"],
            eavesdropper_detected=last.eavesdropper_detected or False,
        )

    @app.post("/simulation/{sim_id}/reset")
    async def reset_simulation(sim_id: str) -> dict[str, str]:
        if sim_id not in _sessions:
            raise HTTPException(404, "Simulation not found")
        session = _sessions[sim_id]
        protocol: ProtocolPort = session["protocol"]
        protocol.reset(session["num_qubits"])
        session["steps"] = []
        return {"status": "reset"}

    return app
