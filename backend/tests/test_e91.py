"""Tests for the E91 QKD protocol implementation."""

from __future__ import annotations

from qkd_playground.adapters.e91 import E91Protocol
from qkd_playground.adapters.qiskit_adapter import (
    DefaultRandomness,
    EavesdroppingChannel,
    IdealQuantumChannel,
    QiskitEntanglementAdapter,
    QiskitMeasurementAdapter,
)
from qkd_playground.domain.models import Basis, ProtocolPhase


def _make_protocol(
    eavesdropper: bool = False,
) -> E91Protocol:
    measurement = QiskitMeasurementAdapter()
    channel: IdealQuantumChannel | EavesdroppingChannel
    if eavesdropper:
        channel = EavesdroppingChannel(measurement)
    else:
        channel = IdealQuantumChannel()
    entanglement = QiskitEntanglementAdapter()
    randomness = DefaultRandomness()
    return E91Protocol(measurement, channel, entanglement, randomness)


def test_e91_run_no_eavesdropper() -> None:
    """E91 produces a shared key with low error rate when no Eve."""
    proto = _make_protocol(eavesdropper=False)
    result = proto.run(num_qubits=100)

    assert result.error_rate < 0.05
    assert not result.eavesdropper_detected
    assert len(result.shared_key) > 0
    assert result.raw_key_length == 100
    assert result.sifted_key_length > 0


def test_e91_run_with_eavesdropper() -> None:
    """E91 detects eavesdropping via elevated error rate or CHSH degradation."""
    proto = _make_protocol(eavesdropper=True)
    result = proto.run(num_qubits=200)

    assert result.eavesdropper_detected
    assert len(result.shared_key) == 0


def test_e91_bell_pair_correlation() -> None:
    """When both measure in same basis, outcomes should be identical."""
    entanglement = QiskitEntanglementAdapter()

    matches = 0
    n = 50
    for _ in range(n):
        # Use measure_bell_pair for proper entanglement simulation
        a_val, b_val = entanglement.measure_bell_pair(
            Basis.RECTILINEAR, Basis.RECTILINEAR
        )
        if a_val == b_val:
            matches += 1

    # Bell pairs should give perfect correlation in matching bases
    assert matches == n


def test_e91_step_by_step() -> None:
    """E91 should go through all 7 phases in order."""
    proto = _make_protocol()
    proto.reset(20)

    expected_phases = [
        ProtocolPhase.TRANSMISSION,
        ProtocolPhase.MEASUREMENT,
        ProtocolPhase.SIFTING,
        ProtocolPhase.ERROR_ESTIMATION,
        ProtocolPhase.RECONCILIATION,
        ProtocolPhase.PRIVACY_AMPLIFICATION,
        ProtocolPhase.COMPLETE,
    ]

    for expected_phase in expected_phases:
        assert not proto.is_complete()
        step = proto.step()
        assert step.phase == expected_phase

    assert proto.is_complete()


def test_e91_chsh_value_no_eavesdropper() -> None:
    """Without Eve, correlation S value should be near 2 (2-basis limit)."""
    proto = _make_protocol(eavesdropper=False)
    result = proto.run(num_qubits=200)

    # Get the last step which has chsh_value
    last_step = result.steps[-1]
    assert last_step.chsh_value is not None
    # With 2 bases, theoretical max is S=2. With finite stats, expect ~1.5-2.2
    assert last_step.chsh_value > 1.2, (
        f"CHSH S = {last_step.chsh_value}, expected > 1.2"
    )
    assert last_step.chsh_value <= 2.5


def test_e91_reset() -> None:
    """Reset clears all protocol state."""
    proto = _make_protocol()
    result = proto.run(num_qubits=20)
    assert len(result.steps) > 0

    proto.reset(10)
    assert not proto.is_complete()
