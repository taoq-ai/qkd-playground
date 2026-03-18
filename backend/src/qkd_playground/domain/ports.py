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
        StepResult,
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
    def step(self) -> StepResult:
        """Execute one step of the protocol and return the current state."""

    @abstractmethod
    def reset(self, num_qubits: int) -> None:
        """Reset the protocol to its initial state."""

    @abstractmethod
    def is_complete(self) -> bool:
        """Return True if the protocol has finished all phases."""


class EntanglementPort(ABC):
    """Port for generating entangled qubit pairs."""

    @abstractmethod
    def generate_bell_pair(self) -> tuple[Qubit, Qubit]:
        """Generate a Bell pair |Phi+> = (|00> + |11>)/sqrt(2)."""


class RandomnessPort(ABC):
    """Port for generating random values (basis choices, bit values)."""

    @abstractmethod
    def random_basis(self) -> Basis:
        """Generate a random basis choice."""

    @abstractmethod
    def random_bit(self) -> BitValue:
        """Generate a random bit value."""


class AttackPort(QuantumChannelPort):
    """Port for eavesdropping attack models.

    Each attack implementation intercepts qubits during transmission
    and returns modified qubits along with information about what
    Eve learned. Extends QuantumChannelPort so attacks can be used
    as drop-in channel replacements.
    """

    @abstractmethod
    def clear(self) -> None:
        """Reset recorded Eve data for a new run."""

    @property
    @abstractmethod
    def eve_bases(self) -> list[Basis]:
        """Return the bases Eve chose for interception."""

    @property
    @abstractmethod
    def eve_results(self) -> list[BitValue]:
        """Return Eve's measurement results."""

    @property
    @abstractmethod
    def eve_information_gain(self) -> float:
        """Return Eve's estimated information gain (0.0 to 1.0)."""

    @property
    @abstractmethod
    def intercepted_count(self) -> int:
        """Return the number of qubits Eve intercepted."""

    @property
    @abstractmethod
    def multi_photon_count(self) -> int:
        """Return the number of multi-photon pulses (for PNS attacks)."""

    @property
    @abstractmethod
    def total_count(self) -> int:
        """Return the total number of qubits transmitted."""
