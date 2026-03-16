"""Cross-protocol eavesdropping test suite.

Verifies that intercept-resend attacks are detected across all
QKD protocols, and that ideal channels produce no disturbance.
"""

from __future__ import annotations

from qkd_playground.adapters.b92 import B92Protocol
from qkd_playground.adapters.bb84 import BB84Protocol
from qkd_playground.adapters.e91 import E91Protocol
from qkd_playground.adapters.qiskit_adapter import (
    DefaultRandomness,
    EavesdroppingChannel,
    IdealQuantumChannel,
    QiskitEntanglementAdapter,
    QiskitMeasurementAdapter,
)
from qkd_playground.domain.models import Basis, BitValue, Qubit


def _make_bb84(eavesdropper: bool = False) -> BB84Protocol:
    measurement = QiskitMeasurementAdapter()
    channel: IdealQuantumChannel | EavesdroppingChannel
    if eavesdropper:
        channel = EavesdroppingChannel(measurement)
    else:
        channel = IdealQuantumChannel()
    return BB84Protocol(measurement, channel, DefaultRandomness())


def _make_b92(eavesdropper: bool = False) -> B92Protocol:
    measurement = QiskitMeasurementAdapter()
    channel: IdealQuantumChannel | EavesdroppingChannel
    if eavesdropper:
        channel = EavesdroppingChannel(measurement)
    else:
        channel = IdealQuantumChannel()
    return B92Protocol(measurement, channel, DefaultRandomness())


def _make_e91(eavesdropper: bool = False) -> E91Protocol:
    measurement = QiskitMeasurementAdapter()
    channel: IdealQuantumChannel | EavesdroppingChannel
    if eavesdropper:
        channel = EavesdroppingChannel(measurement)
    else:
        channel = IdealQuantumChannel()
    entanglement = QiskitEntanglementAdapter()
    return E91Protocol(measurement, channel, entanglement, DefaultRandomness())


# --- Eavesdropper detection across protocols ---


def test_bb84_eavesdrop_detection() -> None:
    """BB84 detects intercept-resend eavesdropping."""
    result = _make_bb84(eavesdropper=True).run(200)
    assert result.eavesdropper_detected
    assert result.error_rate > 0.15
    assert len(result.shared_key) == 0


def test_b92_eavesdrop_detection() -> None:
    """B92 detects intercept-resend eavesdropping."""
    result = _make_b92(eavesdropper=True).run(200)
    assert result.eavesdropper_detected
    assert result.error_rate > 0.15
    assert len(result.shared_key) == 0


def test_e91_eavesdrop_detection() -> None:
    """E91 detects eavesdropping via elevated error rate."""
    result = _make_e91(eavesdropper=True).run(200)
    assert result.eavesdropper_detected
    assert len(result.shared_key) == 0


# --- Ideal channel produces no disturbance ---


def test_ideal_channel_no_disturbance() -> None:
    """IdealQuantumChannel passes qubits through unchanged."""
    channel = IdealQuantumChannel()
    qubit = Qubit(basis=Basis.RECTILINEAR, value=BitValue.ZERO)
    assert channel.transmit(qubit) is qubit

    qubit2 = Qubit(basis=Basis.DIAGONAL, value=BitValue.ONE)
    assert channel.transmit(qubit2) is qubit2


# --- All protocols produce keys without Eve ---


def test_bb84_no_eavesdropper_produces_key() -> None:
    """BB84 produces a shared key when no eavesdropper is present."""
    result = _make_bb84(eavesdropper=False).run(100)
    assert not result.eavesdropper_detected
    assert result.error_rate < 0.05
    assert len(result.shared_key) > 0


def test_b92_no_eavesdropper_produces_key() -> None:
    """B92 produces a shared key when no eavesdropper is present."""
    result = _make_b92(eavesdropper=False).run(100)
    assert not result.eavesdropper_detected
    assert result.error_rate < 0.05
    assert len(result.shared_key) > 0


def test_e91_no_eavesdropper_produces_key() -> None:
    """E91 produces a shared key when no eavesdropper is present."""
    result = _make_e91(eavesdropper=False).run(100)
    assert not result.eavesdropper_detected
    assert result.error_rate < 0.05
    assert len(result.shared_key) > 0


# --- Error rates with eavesdropper ---


def test_error_rates_elevated_with_eavesdropper() -> None:
    """All protocols show elevated error rates under eavesdropping."""
    bb84 = _make_bb84(eavesdropper=True).run(200)
    b92 = _make_b92(eavesdropper=True).run(200)
    e91 = _make_e91(eavesdropper=True).run(200)

    # All should have significantly elevated error rates
    assert bb84.error_rate > 0.15, f"BB84 error rate too low: {bb84.error_rate}"
    assert b92.error_rate > 0.15, f"B92 error rate too low: {b92.error_rate}"
    assert e91.error_rate > 0.10, f"E91 error rate too low: {e91.error_rate}"


def test_e91_chsh_degraded_with_eavesdropper() -> None:
    """E91 CHSH correlation is degraded when Eve is present."""
    result_clean = _make_e91(eavesdropper=False).run(200)
    result_eve = _make_e91(eavesdropper=True).run(200)

    clean_chsh = result_clean.steps[-1].chsh_value
    eve_chsh = result_eve.steps[-1].chsh_value

    assert clean_chsh is not None
    assert eve_chsh is not None
    # Eve should degrade the correlation
    assert eve_chsh < clean_chsh, (
        f"Eve CHSH ({eve_chsh}) should be less than clean ({clean_chsh})"
    )
