"""Qiskit-based implementations of domain ports."""

from __future__ import annotations

import random

from qiskit import QuantumCircuit  # type: ignore[import-untyped]
from qiskit.primitives import StatevectorSampler  # type: ignore[import-untyped]

from qkd_playground.domain.models import (
    Basis,
    BitValue,
    Measurement,
    Qubit,
)
from qkd_playground.domain.ports import (
    MeasurementPort,
    QuantumChannelPort,
    RandomnessPort,
)


class QiskitMeasurementAdapter(MeasurementPort):
    """Qiskit-backed measurement and qubit preparation."""

    def __init__(self) -> None:
        self._sampler = StatevectorSampler()

    def prepare(self, value: BitValue, basis: Basis) -> Qubit:
        """Prepare a qubit with the given value in the given basis."""
        return Qubit(basis=basis, value=value)

    def measure(self, qubit: Qubit, basis: Basis) -> Measurement:
        """Measure a qubit in the given basis using Qiskit simulation.

        If the measurement basis matches the preparation basis, the outcome
        is deterministic. Otherwise, the outcome is random (50/50).
        """
        qc = QuantumCircuit(1, 1)

        # Encode the qubit state
        if qubit.value == BitValue.ONE:
            qc.x(0)
        if qubit.basis == Basis.DIAGONAL:
            qc.h(0)

        # Apply measurement basis transformation
        if basis == Basis.DIAGONAL:
            qc.h(0)

        qc.measure(0, 0)

        job = self._sampler.run([qc], shots=1)
        result = job.result()
        pub_result = result[0]
        counts = pub_result.data.c.get_counts()
        outcome_bit = int(next(iter(counts.keys())))

        outcome = BitValue.ONE if outcome_bit == 1 else BitValue.ZERO
        return Measurement(basis=basis, outcome=outcome, qubit=qubit)


class IdealQuantumChannel(QuantumChannelPort):
    """Perfect quantum channel with no noise or eavesdropping."""

    def transmit(self, qubit: Qubit) -> Qubit:
        """Transmit a qubit perfectly."""
        return qubit


class EavesdroppingChannel(QuantumChannelPort):
    """Quantum channel with an eavesdropper performing intercept-resend."""

    def __init__(self, measurement: MeasurementPort) -> None:
        self._measurement = measurement

    def transmit(self, qubit: Qubit) -> Qubit:
        """Eve intercepts, measures in random basis, resends.

        This introduces ~25% error rate when bases don't match.
        """
        eve_basis = random.choice([Basis.RECTILINEAR, Basis.DIAGONAL])  # noqa: S311
        eve_result = self._measurement.measure(qubit, eve_basis)
        # Eve resends based on her measurement
        return self._measurement.prepare(eve_result.outcome, eve_basis)


class DefaultRandomness(RandomnessPort):
    """Default randomness using Python's random module."""

    def random_basis(self) -> Basis:
        """Generate a random basis choice."""
        return random.choice([Basis.RECTILINEAR, Basis.DIAGONAL])  # noqa: S311

    def random_bit(self) -> BitValue:
        """Generate a random bit value."""
        return random.choice([BitValue.ZERO, BitValue.ONE])  # noqa: S311
