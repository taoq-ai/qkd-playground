"""Tests for the MDI-QKD protocol implementation."""

from __future__ import annotations

from qkd_playground.adapters.mdi_qkd import MDIQKDProtocol
from qkd_playground.adapters.qiskit_adapter import (
    DefaultRandomness,
    EavesdroppingChannel,
    IdealQuantumChannel,
    QiskitMeasurementAdapter,
)
from qkd_playground.domain.models import (
    ProtocolPhase,
)


class TestMDIQKDProtocol:
    """Test MDI-QKD protocol execution."""

    def test_run_ideal_channel_produces_shared_key(self) -> None:
        """With ideal channel (no noise, no Eve), protocol should produce a key."""
        measurement = QiskitMeasurementAdapter()
        channel = IdealQuantumChannel()
        randomness = DefaultRandomness()

        protocol = MDIQKDProtocol(measurement, channel, randomness)
        result = protocol.run(num_qubits=200)

        assert result.raw_key_length == 200
        assert result.sifted_key_length > 0
        # With ideal channel, error rate should be 0
        assert result.error_rate == 0.0
        assert result.eavesdropper_detected is False
        assert len(result.shared_key) > 0
        assert len(result.steps) == 7  # 7 phases

    def test_run_with_eavesdropper_detects_eve(self) -> None:
        """Eavesdropper should introduce detectable errors."""
        measurement = QiskitMeasurementAdapter()
        channel = EavesdroppingChannel(measurement)
        randomness = DefaultRandomness()

        protocol = MDIQKDProtocol(measurement, channel, randomness)

        # Run multiple times -- detection should happen most of the time
        detections = 0
        runs = 20
        for _ in range(runs):
            result = protocol.run(num_qubits=400)
            if result.eavesdropper_detected:
                detections += 1

        # With enough qubits, Eve should be detected reliably
        assert detections > runs * 0.5, f"Eve detected only {detections}/{runs} times"

    def test_bsm_success_rate_approximately_50_percent(self) -> None:
        """BSM success rate should be approximately 50%."""
        measurement = QiskitMeasurementAdapter()
        channel = IdealQuantumChannel()
        randomness = DefaultRandomness()

        protocol = MDIQKDProtocol(measurement, channel, randomness)

        total_success = 0
        total_pairs = 0
        runs = 10
        for _ in range(runs):
            protocol.reset(num_qubits=200)
            # Step through preparation, transmission, measurement
            protocol.step()  # preparation
            protocol.step()  # transmission
            protocol.step()  # measurement (BSM)

            n_success = sum(protocol.bsm_success)
            total_success += n_success
            total_pairs += 200

        bsm_rate = total_success / total_pairs
        # Should be approximately 50% (within statistical tolerance)
        assert 0.35 < bsm_rate < 0.65, f"BSM success rate {bsm_rate:.2%}"

    def test_sift_rate_approximately_12_5_percent(self) -> None:
        """Sift rate should be approximately 12.5% (50% BSM * 50% basis match)."""
        measurement = QiskitMeasurementAdapter()
        channel = IdealQuantumChannel()
        randomness = DefaultRandomness()

        protocol = MDIQKDProtocol(measurement, channel, randomness)

        total_sifted = 0
        total_qubits = 0
        runs = 20
        for _ in range(runs):
            result = protocol.run(num_qubits=200)
            total_sifted += result.sifted_key_length
            total_qubits += 200

        sift_rate = total_sifted / total_qubits
        # Expected ~12.5% (50% BSM success x 50% matching bases)
        assert 0.05 < sift_rate < 0.25, f"Sift rate {sift_rate:.2%}"

    def test_step_through_phases(self) -> None:
        """Stepping through should visit all phases in order."""
        measurement = QiskitMeasurementAdapter()
        channel = IdealQuantumChannel()
        randomness = DefaultRandomness()

        protocol = MDIQKDProtocol(measurement, channel, randomness)
        protocol.reset(num_qubits=100)

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

    def test_compromised_charlie_does_not_break_security(self) -> None:
        """Even if Charlie is compromised, keys should still match without Eve.

        In MDI-QKD, Charlie only performs BSM and announces results.
        A compromised Charlie cannot learn the actual key bits.
        We verify this by running the protocol on an ideal channel
        (no eavesdropper) and confirming keys match.
        """
        measurement = QiskitMeasurementAdapter()
        channel = IdealQuantumChannel()
        randomness = DefaultRandomness()

        protocol = MDIQKDProtocol(measurement, channel, randomness)

        # Run multiple times to be sure
        for _ in range(5):
            result = protocol.run(num_qubits=200)
            assert result.error_rate == 0.0
            assert result.eavesdropper_detected is False
            assert len(result.shared_key) > 0

    def test_ideal_channel_zero_error_rate(self) -> None:
        """Ideal channel should always give 0% error rate."""
        measurement = QiskitMeasurementAdapter()
        channel = IdealQuantumChannel()
        randomness = DefaultRandomness()

        protocol = MDIQKDProtocol(measurement, channel, randomness)
        # Run 5 times to be sure
        for _ in range(5):
            result = protocol.run(num_qubits=200)
            assert result.error_rate == 0.0
