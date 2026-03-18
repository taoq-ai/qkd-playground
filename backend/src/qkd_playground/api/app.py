"""FastAPI application factory."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from qkd_playground.adapters.b92 import B92Protocol
from qkd_playground.adapters.bb84 import BB84Protocol
from qkd_playground.adapters.bell_test import BellTestSimulator
from qkd_playground.adapters.decoy_bb84 import DecoyBB84Protocol
from qkd_playground.adapters.e91 import E91Protocol
from qkd_playground.adapters.key_rate import (
    calculate_key_rate,
    calculate_plob_bound,
)
from qkd_playground.adapters.qiskit_adapter import (
    CompositeChannel,
    DefaultRandomness,
    EavesdroppingChannel,
    IdealQuantumChannel,
    NoisyChannel,
    QiskitEntanglementAdapter,
    QiskitMeasurementAdapter,
)
from qkd_playground.adapters.sarg04 import SARG04Protocol
from qkd_playground.domain.models import (
    ProtocolType,
    StepResult,
)

if TYPE_CHECKING:
    from qkd_playground.domain.ports import ProtocolPort, QuantumChannelPort


class CreateSimulationRequest(BaseModel):
    """Request body for creating a new simulation."""

    protocol: str = Field(default="bb84", description="Protocol type")
    num_qubits: int = Field(default=20, ge=4, le=1000, description="Number of qubits")
    eavesdropper: bool = Field(default=False, description="Enable eavesdropper")
    noise_level: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Depolarizing noise rate"
    )
    loss_rate: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Photon loss rate"
    )


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
    eve_intercepted: bool = False
    eve_bases: list[str] = []
    eve_results: list[int] = []
    reconciled_key_alice: list[int] = []
    reconciled_key_bob: list[int] = []
    reconciliation_corrections: int = 0
    amplified_key: list[int] = []
    privacy_amplification_ratio: float = 0.0
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
            eve_intercepted=step.eve_intercepted,
            eve_bases=[b.value for b in step.eve_bases],
            eve_results=[b.value for b in step.eve_results],
            reconciled_key_alice=[b.value for b in step.reconciled_key_alice],
            reconciled_key_bob=[b.value for b in step.reconciled_key_bob],
            reconciliation_corrections=step.reconciliation_corrections,
            amplified_key=[b.value for b in step.amplified_key],
            privacy_amplification_ratio=step.privacy_amplification_ratio,
            is_complete=complete,
        )


class SimulationState(BaseModel):
    """Full state of a simulation."""

    simulation_id: str
    protocol: str
    num_qubits: int
    eavesdropper: bool
    noise_level: float = 0.0
    loss_rate: float = 0.0
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


class BellTestRequest(BaseModel):
    """Request body for a Bell test experiment."""

    alice_angles: tuple[float, float] = Field(
        default=(0.0, 45.0), description="Alice's angles (a, a') in degrees"
    )
    bob_angles: tuple[float, float] = Field(
        default=(22.5, 67.5), description="Bob's angles (b, b') in degrees"
    )
    num_trials: int = Field(
        default=1000, ge=100, le=10000, description="Shots per angle pair"
    )


class CorrelationResponse(BaseModel):
    """Correlation result for one angle pair."""

    alice_angle: float
    bob_angle: float
    correlation: float
    counts: dict[str, int]


class BellTestResponse(BaseModel):
    """Response for a Bell test experiment."""

    correlations: list[CorrelationResponse]
    s_value: float
    num_trials: int


# In-memory session storage
_sessions: dict[str, dict[str, Any]] = {}


def _create_protocol(
    protocol_type: str,
    eavesdropper: bool,
    noise_level: float = 0.0,
    loss_rate: float = 0.0,
) -> ProtocolPort:
    """Create a protocol instance based on type."""
    measurement = QiskitMeasurementAdapter()

    channels: list[QuantumChannelPort] = []
    if noise_level > 0 or loss_rate > 0:
        channels.append(
            NoisyChannel(depolarizing_rate=noise_level, loss_rate=loss_rate)
        )
    if eavesdropper:
        channels.append(EavesdroppingChannel(measurement))

    channel: QuantumChannelPort
    if not channels:
        channel = IdealQuantumChannel()
    elif len(channels) == 1:
        channel = channels[0]
    else:
        channel = CompositeChannel(channels)

    randomness = DefaultRandomness()
    if protocol_type == "b92":
        return B92Protocol(measurement, channel, randomness)
    if protocol_type == "sarg04":
        return SARG04Protocol(measurement, channel, randomness)
    if protocol_type == "decoy_bb84":
        return DecoyBB84Protocol(measurement, channel, randomness)
    if protocol_type == "e91":
        entanglement = QiskitEntanglementAdapter()
        return E91Protocol(measurement, channel, entanglement, randomness)
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
        protocol = _create_protocol(
            req.protocol, req.eavesdropper, req.noise_level, req.loss_rate
        )
        protocol.reset(req.num_qubits)
        _sessions[sim_id] = {
            "protocol": protocol,
            "protocol_type": req.protocol,
            "num_qubits": req.num_qubits,
            "eavesdropper": req.eavesdropper,
            "noise_level": req.noise_level,
            "loss_rate": req.loss_rate,
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
            noise_level=session.get("noise_level", 0.0),
            loss_rate=session.get("loss_rate", 0.0),
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

    @app.get("/performance")
    async def get_performance(
        protocols: str = "bb84,b92,e91,sarg04",
        max_distance: float = 200.0,
        detector_efficiency: float = 0.1,
        dark_count_rate: float = 1e-6,
        steps: int = 100,
    ) -> dict[str, Any]:
        """Return rate-vs-distance data for requested protocols + PLOB bound."""
        valid_protocols = {"bb84", "b92", "e91", "sarg04"}
        requested = [
            p.strip().lower()
            for p in protocols.split(",")
            if p.strip().lower() in valid_protocols
        ]
        if not requested:
            raise HTTPException(400, "No valid protocols specified")

        num_steps = min(max(steps, 10), 500)

        result: dict[str, list[dict[str, float]]] = {}
        for proto in requested:
            points: list[dict[str, float]] = []
            for i in range(num_steps + 1):
                d = max_distance * i / num_steps
                r = calculate_key_rate(proto, d, detector_efficiency, dark_count_rate)
                points.append({"distance": round(d, 2), "rate": r})
            result[proto] = points

        # PLOB bound
        plob_points: list[dict[str, float]] = []
        for i in range(num_steps + 1):
            d = max_distance * i / num_steps
            r = calculate_plob_bound(d, detector_efficiency)
            plob_points.append({"distance": round(d, 2), "rate": r})
        result["plob_bound"] = plob_points

        return {
            "protocols": result,
            "params": {
                "max_distance": max_distance,
                "detector_efficiency": detector_efficiency,
                "dark_count_rate": dark_count_rate,
            },
        }

    @app.post("/bell-test")
    async def run_bell_test(req: BellTestRequest) -> BellTestResponse:
        """Run a standalone CHSH Bell inequality test."""
        simulator = BellTestSimulator()
        result = simulator.run(
            alice_angles=req.alice_angles,
            bob_angles=req.bob_angles,
            num_trials=req.num_trials,
        )
        return BellTestResponse(
            correlations=[
                CorrelationResponse(
                    alice_angle=c.alice_angle,
                    bob_angle=c.bob_angle,
                    correlation=c.correlation,
                    counts=c.counts,
                )
                for c in result.correlations
            ],
            s_value=result.s_value,
            num_trials=result.num_trials,
        )

    return app
