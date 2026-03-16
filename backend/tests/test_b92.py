"""Tests for the B92 QKD protocol implementation."""

from __future__ import annotations

from qkd_playground.adapters.b92 import B92Protocol
from qkd_playground.adapters.qiskit_adapter import (
    DefaultRandomness,
    EavesdroppingChannel,
    IdealQuantumChannel,
    QiskitMeasurementAdapter,
)
from qkd_playground.domain.models import (
    Basis,
    BitValue,
    ProtocolPhase,
)


def _make_protocol(
    eavesdropper: bool = False,
) -> B92Protocol:
    measurement = QiskitMeasurementAdapter()
    channel: IdealQuantumChannel | EavesdroppingChannel
    if eavesdropper:
        channel = EavesdroppingChannel(measurement)
    else:
        channel = IdealQuantumChannel()
    randomness = DefaultRandomness()
    return B92Protocol(measurement, channel, randomness)


def test_b92_run_no_eavesdropper() -> None:
    """B92 produces a shared key with ~0% error rate when no Eve."""
    proto = _make_protocol(eavesdropper=False)
    result = proto.run(num_qubits=100)

    assert result.error_rate < 0.05
    assert not result.eavesdropper_detected
    assert len(result.shared_key) > 0
    assert result.raw_key_length == 100
    assert result.sifted_key_length > 0


def test_b92_run_with_eavesdropper() -> None:
    """B92 detects eavesdropping (elevated error rate)."""
    proto = _make_protocol(eavesdropper=True)
    result = proto.run(num_qubits=200)

    # With 200 qubits, Eve should be reliably detected
    assert result.eavesdropper_detected
    assert result.error_rate > 0.15
    assert len(result.shared_key) == 0


def test_b92_sift_rate() -> None:
    """B92 sift rate should be ~25% (conclusive measurements)."""
    proto = _make_protocol(eavesdropper=False)
    result = proto.run(num_qubits=200)

    sift_rate = result.sifted_key_length / result.raw_key_length
    # Expect ~25% with reasonable tolerance
    assert 0.10 < sift_rate < 0.45


def test_b92_step_by_step() -> None:
    """B92 should go through all 5 phases in order."""
    proto = _make_protocol()
    proto.reset(20)

    expected_phases = [
        ProtocolPhase.TRANSMISSION,
        ProtocolPhase.MEASUREMENT,
        ProtocolPhase.SIFTING,
        ProtocolPhase.ERROR_ESTIMATION,
        ProtocolPhase.COMPLETE,
    ]

    for expected_phase in expected_phases:
        assert not proto.is_complete()
        step = proto.step()
        assert step.phase == expected_phase

    assert proto.is_complete()


def test_b92_preparation_states() -> None:
    """B92 uses only 2 non-orthogonal states: |0⟩ and |+⟩."""
    proto = _make_protocol()
    proto.reset(50)

    # Run preparation step
    step = proto.step()
    assert step.phase == ProtocolPhase.TRANSMISSION  # moved to next phase

    # Check that Alice's bases are determined by her bits
    for bit, basis in zip(step.alice_bits, step.alice_bases, strict=True):
        if bit == BitValue.ZERO:
            assert basis == Basis.RECTILINEAR
        else:
            assert basis == Basis.DIAGONAL


def test_b92_conclusive_mask_populated() -> None:
    """B92 step results include conclusive_mask after measurement."""
    proto = _make_protocol()
    proto.reset(30)

    # Run through preparation, transmission, measurement
    proto.step()  # preparation → transmission
    proto.step()  # transmission → measurement
    step = proto.step()  # measurement → sifting

    assert len(step.conclusive_mask) == 30
    # Some should be True, some False
    assert any(step.conclusive_mask)
    assert not all(step.conclusive_mask)


def test_b92_reset() -> None:
    """Reset clears all protocol state."""
    proto = _make_protocol()
    result = proto.run(num_qubits=20)
    assert len(result.steps) > 0

    proto.reset(10)
    assert not proto.is_complete()
