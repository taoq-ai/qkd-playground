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
    EntanglementPort,
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


class QiskitEntanglementAdapter(EntanglementPort):
    """Generate entangled Bell pairs |Φ+⟩ = (|00⟩ + |11⟩)/√2.

    When both halves are measured in the same basis, outcomes are
    perfectly correlated. When measured in different bases, outcomes
    are random and uncorrelated.

    Since our Qubit model can't represent true entanglement (each
    qubit is measured independently), we provide measure_bell_pair()
    which does a proper 2-qubit Qiskit simulation at measurement time.
    """

    def __init__(self) -> None:
        self._sampler = StatevectorSampler()

    def generate_bell_pair(self) -> tuple[Qubit, Qubit]:
        """Generate a Bell pair placeholder.

        Returns two qubits with matching random values. For proper
        entanglement correlations, use measure_bell_pair() instead
        of measuring these independently.
        """
        v = random.choice([BitValue.ZERO, BitValue.ONE])  # noqa: S311
        return (
            Qubit(basis=Basis.RECTILINEAR, value=v),
            Qubit(basis=Basis.RECTILINEAR, value=v),
        )

    def measure_bell_pair(
        self,
        alice_basis: Basis,
        bob_basis: Basis,
    ) -> tuple[BitValue, BitValue]:
        """Measure an entangled Bell pair with proper quantum correlations.

        Creates a fresh 2-qubit Bell state |Φ+⟩, applies basis
        transformations for both parties, and measures simultaneously.
        This preserves quantum correlations that would be lost if
        each qubit were measured independently.
        """
        qc = QuantumCircuit(2, 2)
        qc.h(0)
        qc.cx(0, 1)

        # Apply Alice's basis transformation on qubit 0
        if alice_basis == Basis.DIAGONAL:
            qc.h(0)

        # Apply Bob's basis transformation on qubit 1
        if bob_basis == Basis.DIAGONAL:
            qc.h(1)

        qc.measure([0, 1], [0, 1])

        job = self._sampler.run([qc], shots=1)
        result = job.result()
        counts = result[0].data.c.get_counts()
        bitstring = next(iter(counts.keys()))
        # Qiskit bit ordering: rightmost char = qubit 0
        alice_bit = int(bitstring[-1])
        bob_bit = int(bitstring[-2])

        alice_val = BitValue.ONE if alice_bit == 1 else BitValue.ZERO
        bob_val = BitValue.ONE if bob_bit == 1 else BitValue.ZERO
        return alice_val, bob_val


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
