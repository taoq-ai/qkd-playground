"""Tests for the BB84 protocol implementation."""

from __future__ import annotations

from qkd_playground.adapters.bb84 import BB84Protocol
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
from qkd_playground.domain.ports import RandomnessPort


class DeterministicRandomness(RandomnessPort):
    """Predictable randomness for testing."""

    def __init__(self, bases: list[Basis], bits: list[BitValue]) -> None:
        self._bases = list(bases)
        self._bits = list(bits)
        self._basis_idx = 0
        self._bit_idx = 0

    def random_basis(self) -> Basis:
        basis = self._bases[self._basis_idx % len(self._bases)]
        self._basis_idx += 1
        return basis

    def random_bit(self) -> BitValue:
        bit = self._bits[self._bit_idx % len(self._bits)]
        self._bit_idx += 1
        return bit


class TestBB84Protocol:
    """Test BB84 protocol execution."""

    def test_run_ideal_channel_produces_shared_key(self) -> None:
        """With ideal channel (no noise, no Eve), protocol should produce a key."""
        measurement = QiskitMeasurementAdapter()
        channel = IdealQuantumChannel()
        randomness = DefaultRandomness()

        protocol = BB84Protocol(measurement, channel, randomness)
        result = protocol.run(num_qubits=100)

        assert result.raw_key_length == 100
        assert result.sifted_key_length > 0
        # With ideal channel, error rate should be 0
        assert result.error_rate == 0.0
        assert result.eavesdropper_detected is False
        assert len(result.shared_key) > 0
        assert len(result.steps) == 5  # 5 phases

    def test_run_with_eavesdropper_detects_eve(self) -> None:
        """Eavesdropper should introduce detectable errors (~25%)."""
        measurement = QiskitMeasurementAdapter()
        channel = EavesdroppingChannel(measurement)
        randomness = DefaultRandomness()

        protocol = BB84Protocol(measurement, channel, randomness)

        # Run multiple times — detection should happen most of the time
        detections = 0
        runs = 20
        for _ in range(runs):
            result = protocol.run(num_qubits=200)
            if result.eavesdropper_detected:
                detections += 1

        # With 200 qubits, Eve should be detected reliably
        assert detections > runs * 0.7, f"Eve detected only {detections}/{runs} times"

    def test_deterministic_matching_bases_gives_full_key(self) -> None:
        """When Alice and Bob always use the same basis, sift rate = 100%."""
        all_rect = [Basis.RECTILINEAR] * 20
        bits = [BitValue.ZERO, BitValue.ONE] * 10

        randomness = DeterministicRandomness(bases=all_rect, bits=bits)
        measurement = QiskitMeasurementAdapter()
        channel = IdealQuantumChannel()

        protocol = BB84Protocol(measurement, channel, randomness)
        result = protocol.run(num_qubits=10)

        # All bases match, so sifted key = raw key
        assert result.sifted_key_length == 10
        assert result.error_rate == 0.0
        assert len(result.shared_key) == 10

    def test_step_through_phases(self) -> None:
        """Stepping through should visit all phases in order."""
        measurement = QiskitMeasurementAdapter()
        channel = IdealQuantumChannel()
        randomness = DefaultRandomness()

        protocol = BB84Protocol(measurement, channel, randomness)
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

    def test_step_result_contains_alice_and_bob_data(self) -> None:
        """After each step, StepResult should contain accumulated state."""
        measurement = QiskitMeasurementAdapter()
        channel = IdealQuantumChannel()
        randomness = DefaultRandomness()

        protocol = BB84Protocol(measurement, channel, randomness)
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

        protocol = BB84Protocol(measurement, channel, randomness)
        # Run 5 times to be sure
        for _ in range(5):
            result = protocol.run(num_qubits=50)
            assert result.error_rate == 0.0

    def test_eavesdropper_error_rate_around_25_percent(self) -> None:
        """Intercept-resend attack should introduce ~25% errors."""
        measurement = QiskitMeasurementAdapter()
        channel = EavesdroppingChannel(measurement)
        randomness = DefaultRandomness()

        protocol = BB84Protocol(measurement, channel, randomness)

        total_error = 0.0
        runs = 10
        for _ in range(runs):
            result = protocol.run(num_qubits=500)
            total_error += result.error_rate

        avg_error = total_error / runs
        # Theoretical: 25% error rate from intercept-resend
        assert 0.15 < avg_error < 0.35, f"Average error rate {avg_error:.2%}"


class TestQiskitMeasurement:
    """Test Qiskit measurement adapter."""

    def test_matching_basis_deterministic(self) -> None:
        """Measuring in the same basis should always give the prepared value."""
        m = QiskitMeasurementAdapter()
        for basis in [Basis.RECTILINEAR, Basis.DIAGONAL]:
            for value in [BitValue.ZERO, BitValue.ONE]:
                qubit = m.prepare(value, basis)
                result = m.measure(qubit, basis)
                assert result.outcome == value

    def test_mismatched_basis_random(self) -> None:
        """Measuring in wrong basis should give roughly 50/50 outcomes."""
        m = QiskitMeasurementAdapter()
        qubit = m.prepare(BitValue.ZERO, Basis.RECTILINEAR)

        zeros = 0
        trials = 200
        for _ in range(trials):
            result = m.measure(qubit, Basis.DIAGONAL)
            if result.outcome == BitValue.ZERO:
                zeros += 1

        # Should be roughly 50/50
        assert 0.3 < zeros / trials < 0.7


class TestQuantumChannels:
    """Test quantum channel implementations."""

    def test_ideal_channel_preserves_qubit(self) -> None:
        """Ideal channel should return the same qubit."""
        channel = IdealQuantumChannel()
        m = QiskitMeasurementAdapter()
        qubit = m.prepare(BitValue.ONE, Basis.DIAGONAL)
        result = channel.transmit(qubit)
        assert result == qubit

    def test_eavesdropping_channel_sometimes_flips(self) -> None:
        """Eavesdropping channel should sometimes change the qubit."""
        m = QiskitMeasurementAdapter()
        channel = EavesdroppingChannel(m)

        changes = 0
        trials = 100
        for _ in range(trials):
            qubit = m.prepare(BitValue.ZERO, Basis.RECTILINEAR)
            transmitted = channel.transmit(qubit)
            # Measure in original basis
            result = m.measure(transmitted, Basis.RECTILINEAR)
            if result.outcome != BitValue.ZERO:
                changes += 1

        # Eve should cause some changes (not all, not none)
        assert changes > 0, "Eve should disturb some qubits"
