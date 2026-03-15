"""Port interfaces (abstract base classes) for the hexagonal architecture."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from qkd_playground.domain.models import (
        Basis,
        BitValue,
        Measurement,
        ProtocolResult,
        Qubit,
    )


class QuantumChannelPort(ABC):
    """Port for transmitting qubits through a quantum channel."""

    @abstractmethod
    def transmit(self, qubit: Qubit) -> Qubit:
        """Transmit a qubit through the channel.

        May introduce noise or eavesdropping effects.
        """


class MeasurementPort(ABC):
    """Port for performing quantum measurements."""

    @abstractmethod
    def measure(self, qubit: Qubit, basis: Basis) -> Measurement:
        """Measure a qubit in the given basis."""

    @abstractmethod
    def prepare(self, value: BitValue, basis: Basis) -> Qubit:
        """Prepare a qubit with the given value in the given basis."""


class ProtocolPort(ABC):
    """Port for running a QKD protocol end-to-end."""

    @abstractmethod
    def run(self, num_qubits: int) -> ProtocolResult:
        """Execute the protocol with the given number of qubits."""

    @abstractmethod
    def step(self) -> dict[str, object]:
        """Execute one step of the protocol and return the current state."""

    @abstractmethod
    def reset(self) -> None:
        """Reset the protocol to its initial state."""


class RandomnessPort(ABC):
    """Port for generating random values (basis choices, bit values)."""

    @abstractmethod
    def random_basis(self) -> Basis:
        """Generate a random basis choice."""

    @abstractmethod
    def random_bit(self) -> BitValue:
        """Generate a random bit value."""
