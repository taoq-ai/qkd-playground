"""Tests for the SARG04 protocol implementation."""

from __future__ import annotations

from qkd_playground.adapters.qiskit_adapter import (
    DefaultRandomness,
    EavesdroppingChannel,
    IdealQuantumChannel,
    QiskitMeasurementAdapter,
)
from qkd_playground.adapters.sarg04 import SARG04Protocol
from qkd_playground.domain.models import (
    ProtocolPhase,
)


class TestSARG04Protocol:
    """Test SARG04 protocol execution."""

    def test_run_ideal_channel_produces_shared_key(self) -> None:
        """With ideal channel (no noise, no Eve), protocol should produce a key."""
        measurement = QiskitMeasurementAdapter()
        channel = IdealQuantumChannel()
        randomness = DefaultRandomness()

        protocol = SARG04Protocol(measurement, channel, randomness)
        result = protocol.run(num_qubits=100)

        assert result.raw_key_length == 100
        assert result.sifted_key_length > 0
        # With ideal channel, error rate should be 0
        assert result.error_rate == 0.0
        assert result.eavesdropper_detected is False
        assert len(result.shared_key) > 0
        assert len(result.steps) == 5  # 5 phases

    def test_run_with_eavesdropper_detects_eve(self) -> None:
        """Eavesdropper should introduce detectable errors."""
        measurement = QiskitMeasurementAdapter()
        channel = EavesdroppingChannel(measurement)
        randomness = DefaultRandomness()

        protocol = SARG04Protocol(measurement, channel, randomness)

        # Run multiple times — detection should happen most of the time
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

        protocol = SARG04Protocol(measurement, channel, randomness)
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
            ProtocolPhase.COMPLETE,
        ]
        assert phases == expected

    def test_sift_rate_approximately_25_percent(self) -> None:
        """SARG04 should have ~25% sift rate (lower than BB84's ~50%)."""
        measurement = QiskitMeasurementAdapter()
        channel = IdealQuantumChannel()
        randomness = DefaultRandomness()

        protocol = SARG04Protocol(measurement, channel, randomness)

        total_sift_rate = 0.0
        runs = 10
        for _ in range(runs):
            result = protocol.run(num_qubits=500)
            sift_rate = result.sifted_key_length / result.raw_key_length
            total_sift_rate += sift_rate

        avg_sift_rate = total_sift_rate / runs
        # SARG04 theoretical sift rate is ~25%
        assert 0.15 < avg_sift_rate < 0.35, (
            f"Average sift rate {avg_sift_rate:.2%} not near expected ~25%"
        )

    def test_step_result_contains_alice_and_bob_data(self) -> None:
        """After each step, StepResult should contain accumulated state."""
        measurement = QiskitMeasurementAdapter()
        channel = IdealQuantumChannel()
        randomness = DefaultRandomness()

        protocol = SARG04Protocol(measurement, channel, randomness)
        protocol.reset(num_qubits=10)

        # Step through preparation
        step1 = protocol.step()
        assert len(step1.alice_bits) == 10
        assert len(step1.alice_bases) == 10

        # Step through transmission
        _step2 = protocol.step()

        # Step through measurement
        step3 = protocol.step()
        assert len(step3.bob_bases) == 10
        assert len(step3.bob_results) == 10

        # Step through sifting
        step4 = protocol.step()
        assert len(step4.matching_bases) == 10
        assert len(step4.sifted_key_alice) <= 10

    def test_ideal_channel_zero_error_rate(self) -> None:
        """Ideal channel should always give 0% error rate."""
        measurement = QiskitMeasurementAdapter()
        channel = IdealQuantumChannel()
        randomness = DefaultRandomness()

        protocol = SARG04Protocol(measurement, channel, randomness)
        # Run 5 times to be sure
        for _ in range(5):
            result = protocol.run(num_qubits=50)
            assert result.error_rate == 0.0
