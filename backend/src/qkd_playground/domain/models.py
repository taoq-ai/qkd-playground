"""Domain models for QKD protocols."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Basis(Enum):
    """Measurement basis for qubit operations."""

    RECTILINEAR = "rectilinear"  # Z-basis: |0⟩, |1⟩
    DIAGONAL = "diagonal"  # X-basis: |+⟩, |−⟩


class BitValue(Enum):
    """Classical bit value."""

    ZERO = 0
    ONE = 1


@dataclass(frozen=True)
class Qubit:
    """Represents a qubit prepared in a specific basis with a bit value."""

    basis: Basis
    value: BitValue


@dataclass(frozen=True)
class Measurement:
    """Result of measuring a qubit."""

    basis: Basis
    outcome: BitValue
    qubit: Qubit


@dataclass
class ProtocolResult:
    """Result of running a QKD protocol."""

    shared_key: list[BitValue] = field(default_factory=list)
    error_rate: float = 0.0
    raw_key_length: int = 0
    sifted_key_length: int = 0
    eavesdropper_detected: bool = False


class ProtocolType(Enum):
    """Supported QKD protocols."""

    BB84 = "bb84"
    E91 = "e91"
    B92 = "b92"
