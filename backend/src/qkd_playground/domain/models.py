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


class ProtocolPhase(Enum):
    """Phases of a QKD protocol execution."""

    PREPARATION = "preparation"
    TRANSMISSION = "transmission"
    MEASUREMENT = "measurement"
    SIFTING = "sifting"
    ERROR_ESTIMATION = "error_estimation"
    RECONCILIATION = "reconciliation"
    PRIVACY_AMPLIFICATION = "privacy_amplification"
    COMPLETE = "complete"


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
class StepResult:
    """Result of a single protocol step, suitable for UI consumption."""

    phase: ProtocolPhase
    step_index: int
    description: str
    alice_bits: list[BitValue] = field(default_factory=list)
    alice_bases: list[Basis] = field(default_factory=list)
    bob_bases: list[Basis] = field(default_factory=list)
    bob_results: list[BitValue] = field(default_factory=list)
    matching_bases: list[bool] = field(default_factory=list)
    sifted_key_alice: list[BitValue] = field(default_factory=list)
    sifted_key_bob: list[BitValue] = field(default_factory=list)
    error_rate: float | None = None
    eavesdropper_detected: bool | None = None
    shared_key: list[BitValue] = field(default_factory=list)
    conclusive_mask: list[bool] = field(default_factory=list)
    chsh_value: float | None = None
    eve_intercepted: bool = False
    eve_bases: list[Basis] = field(default_factory=list)
    eve_results: list[BitValue] = field(default_factory=list)
    reconciled_key_alice: list[BitValue] = field(default_factory=list)
    reconciled_key_bob: list[BitValue] = field(default_factory=list)
    reconciliation_corrections: int = 0
    amplified_key: list[BitValue] = field(default_factory=list)
    privacy_amplification_ratio: float = 0.0
    eve_information_gain: float = 0.0
    intercepted_fraction: float = 0.0
    multi_photon_fraction: float = 0.0


@dataclass
class ProtocolResult:
    """Result of running a QKD protocol."""

    shared_key: list[BitValue] = field(default_factory=list)
    error_rate: float = 0.0
    raw_key_length: int = 0
    sifted_key_length: int = 0
    eavesdropper_detected: bool = False
    steps: list[StepResult] = field(default_factory=list)


class ProtocolType(Enum):
    """Supported QKD protocols."""

    BB84 = "bb84"
    E91 = "e91"
    B92 = "b92"
    SARG04 = "sarg04"
    DECOY_BB84 = "decoy_bb84"
    MDI_QKD = "mdi_qkd"


class AttackType(Enum):
    """Types of eavesdropping attacks."""

    NONE = "none"
    INTERCEPT_RESEND = "intercept_resend"
    PNS = "pns"
    PARTIAL_INTERCEPT = "partial_intercept"
