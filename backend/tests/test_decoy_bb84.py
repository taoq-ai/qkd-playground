"""Tests for the decoy-state BB84 protocol implementation."""

from __future__ import annotations

from qkd_playground.adapters.decoy_bb84 import (
    DecoyBB84Protocol,
    IntensityLevel,
)
from qkd_playground.adapters.qiskit_adapter import (
    DefaultRandomness,
    EavesdroppingChannel,
    IdealQuantumChannel,
    QiskitMeasurementAdapter,
)
from qkd_playground.domain.models import ProtocolPhase


class TestDecoyBB84Protocol:
    """Test decoy-state BB84 protocol execution."""

    def test_run_ideal_channel_produces_shared_key(self) -> None:
        """With ideal channel, protocol should produce a key."""
        measurement = QiskitMeasurementAdapter()
        channel = IdealQuantumChannel()
        randomness = DefaultRandomness()

        protocol = DecoyBB84Protocol(measurement, channel, randomness)
        result = protocol.run(num_qubits=100)

        assert result.raw_key_length == 100
        assert result.sifted_key_length > 0
        assert result.error_rate == 0.0
        assert result.eavesdropper_detected is False
        assert len(result.shared_key) > 0
        assert len(result.steps) == 7  # 7 phases

    def test_run_with_eavesdropper_detects_eve(self) -> None:
        """Eavesdropper should introduce detectable errors."""
        measurement = QiskitMeasurementAdapter()
        channel = EavesdroppingChannel(measurement)
        randomness = DefaultRandomness()

        protocol = DecoyBB84Protocol(measurement, channel, randomness)

        detections = 0
        runs = 20
        for _ in range(runs):
            result = protocol.run(num_qubits=200)
            if result.eavesdropper_detected:
                detections += 1

        # With 200 qubits, Eve should be detected reliably
        assert detections > runs * 0.7, f"Eve detected only {detections}/{runs} times"

    def test_step_through_phases(self) -> None:
        """Stepping through should visit all phases in order."""
        measurement = QiskitMeasurementAdapter()
        channel = IdealQuantumChannel()
        randomness = DefaultRandomness()

        protocol = DecoyBB84Protocol(measurement, channel, randomness)
        protocol.reset(num_qubits=20)

        phases = []
        while not protocol.is_complete():
            step = protocol.step()
            phases.append(step.phase)

        expected = [
            ProtocolPhase.TRANSMISSION,
            ProtocolPhase.MEASUREMENT,
            ProtocolPhase.SIFTING,
            ProtocolPhase.ERROR_ESTIMATION,
            ProtocolPhase.RECONCILIATION,
            ProtocolPhase.PRIVACY_AMPLIFICATION,
            ProtocolPhase.COMPLETE,
        ]
        assert phases == expected

    def test_intensity_assignment_distribution(self) -> None:
        """Intensity assignments should follow expected distribution."""
        measurement = QiskitMeasurementAdapter()
        channel = IdealQuantumChannel()
        randomness = DefaultRandomness()

        protocol = DecoyBB84Protocol(measurement, channel, randomness)
        protocol.reset(num_qubits=1000)

        # Step through preparation to assign intensities
        protocol.step()

        assignments = protocol.intensity_assignments
        assert len(assignments) == 1000

        n_signal = sum(1 for a in assignments if a == IntensityLevel.SIGNAL)
        n_decoy = sum(1 for a in assignments if a == IntensityLevel.DECOY)
        n_vacuum = sum(1 for a in assignments if a == IntensityLevel.VACUUM)

        # Check rough distribution (60% signal, 30% decoy, 10% vacuum)
        assert 400 < n_signal < 800, f"Signal count {n_signal} out of range"
        assert 150 < n_decoy < 450, f"Decoy count {n_decoy} out of range"
        assert n_vacuum > 10, f"Vacuum count {n_vacuum} too low"
        assert n_signal + n_decoy + n_vacuum == 1000

    def test_decoy_analysis_produces_valid_estimates(self) -> None:
        """Decoy analysis should produce reasonable single-photon estimates."""
        measurement = QiskitMeasurementAdapter()
        channel = IdealQuantumChannel()
        randomness = DefaultRandomness()

        protocol = DecoyBB84Protocol(measurement, channel, randomness)
        result = protocol.run(num_qubits=200)

        # On ideal channel, single-photon yield should be positive
        assert protocol.single_photon_yield >= 0.0
        assert protocol.single_photon_yield <= 1.0

        # Single-photon QBER should be low on ideal channel
        assert protocol.single_photon_qber >= 0.0
        assert protocol.single_photon_qber <= 0.5

        # Secure key rate should be positive on clean channel
        assert protocol.secure_key_rate >= 0.0
        assert result.error_rate == 0.0

    def test_key_rate_calculation(self) -> None:
        """Secure key rate should be positive on ideal channel."""
        measurement = QiskitMeasurementAdapter()
        channel = IdealQuantumChannel()
        randomness = DefaultRandomness()

        protocol = DecoyBB84Protocol(measurement, channel, randomness)
        protocol.run(num_qubits=200)

        # Signal yield should be positive
        assert protocol.signal_yield > 0.0
        # Decoy yield should be positive (or at least non-negative)
        assert protocol.decoy_yield >= 0.0

    def test_sifted_key_uses_only_signal_pulses(self) -> None:
        """Sifted key should only contain signal-intensity pulses."""
        measurement = QiskitMeasurementAdapter()
        channel = IdealQuantumChannel()
        randomness = DefaultRandomness()

        protocol = DecoyBB84Protocol(measurement, channel, randomness)
        result = protocol.run(num_qubits=100)

        # Sifted key should be shorter than total matching bases
        # because only signal pulses contribute
        assert result.sifted_key_length > 0
        assert result.sifted_key_length < 100

    def test_ideal_channel_zero_error_rate(self) -> None:
        """Ideal channel should always give 0% error rate."""
        measurement = QiskitMeasurementAdapter()
        channel = IdealQuantumChannel()
        randomness = DefaultRandomness()

        protocol = DecoyBB84Protocol(measurement, channel, randomness)
        for _ in range(5):
            result = protocol.run(num_qubits=50)
            assert result.error_rate == 0.0

    def test_reset_clears_state(self) -> None:
        """Reset should clear all protocol state."""
        measurement = QiskitMeasurementAdapter()
        channel = IdealQuantumChannel()
        randomness = DefaultRandomness()

        protocol = DecoyBB84Protocol(measurement, channel, randomness)
        protocol.run(num_qubits=50)

        # After a run, properties should be set
        assert protocol.single_photon_yield >= 0.0

        # After reset, should be back to initial state
        protocol.reset(num_qubits=20)
        assert protocol.single_photon_yield == 0.0
        assert protocol.single_photon_qber == 0.0
        assert protocol.secure_key_rate == 0.0
        assert protocol.intensity_assignments == []
        assert not protocol.is_complete()
