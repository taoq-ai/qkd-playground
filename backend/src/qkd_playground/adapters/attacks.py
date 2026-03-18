"""Attack model implementations for advanced eavesdropping simulations.

Provides PNS (Photon Number Splitting) and Partial Intercept attacks
beyond the basic intercept-resend attack in qiskit_adapter.py.
"""

from __future__ import annotations

import math
import random

from qkd_playground.domain.models import Basis, BitValue, Qubit
from qkd_playground.domain.ports import AttackPort, MeasurementPort


class PNSAttackChannel(AttackPort):
    """Photon Number Splitting (PNS) attack on weak coherent pulse sources.

    Eve splits multi-photon pulses from weak coherent sources, stores the
    extra photons, and measures them after basis announcement. Only
    multi-photon pulses are intercepted; single-photon pulses pass through
    undisturbed.

    The probability of n photons per pulse follows a Poisson distribution
    with mean photon number mu. Eve intercepts all pulses with n >= 2.
    """

    def __init__(
        self,
        measurement: MeasurementPort,
        mu: float = 0.5,
    ) -> None:
        if not 0.0 < mu <= 2.0:
            msg = "Mean photon number mu must be between 0.0 (exclusive) and 2.0"
            raise ValueError(msg)
        self._measurement = measurement
        self._mu = mu
        self._eve_bases: list[Basis] = []
        self._eve_results: list[BitValue] = []
        self._total_count: int = 0
        self._intercepted_count: int = 0
        self._multi_photon_count: int = 0

    @property
    def eve_bases(self) -> list[Basis]:
        """Return the bases Eve chose for interception."""
        return list(self._eve_bases)

    @property
    def eve_results(self) -> list[BitValue]:
        """Return Eve's measurement results."""
        return list(self._eve_results)

    @property
    def eve_information_gain(self) -> float:
        """Return Eve's estimated information gain.

        Eve gains full information on multi-photon pulses she intercepts.
        Her information gain is the fraction of intercepted pulses.
        """
        if self._total_count == 0:
            return 0.0
        return self._intercepted_count / self._total_count

    @property
    def intercepted_count(self) -> int:
        """Return the number of qubits Eve intercepted."""
        return self._intercepted_count

    @property
    def multi_photon_count(self) -> int:
        """Return the number of multi-photon pulses."""
        return self._multi_photon_count

    @property
    def total_count(self) -> int:
        """Return the total number of qubits transmitted."""
        return self._total_count

    def clear(self) -> None:
        """Reset recorded Eve data for a new run."""
        self._eve_bases = []
        self._eve_results = []
        self._total_count = 0
        self._intercepted_count = 0
        self._multi_photon_count = 0

    def _is_multi_photon(self) -> bool:
        """Determine if this pulse contains multiple photons.

        Probability of multi-photon pulse: P(n>=2) = 1 - P(0) - P(1)
        P(0) = e^(-mu), P(1) = mu * e^(-mu)
        """
        p_zero = math.exp(-self._mu)
        p_one = self._mu * math.exp(-self._mu)
        p_multi = 1.0 - p_zero - p_one
        return random.random() < p_multi  # noqa: S311

    def transmit(self, qubit: Qubit) -> Qubit:
        """Transmit a qubit, intercepting only multi-photon pulses.

        Single-photon pulses pass through undisturbed (no error introduced).
        Multi-photon pulses: Eve splits off a photon and measures it in a
        random basis. The original qubit passes through to Bob undisturbed
        since Eve has extra photons to work with.
        """
        self._total_count += 1

        if self._is_multi_photon():
            self._multi_photon_count += 1
            self._intercepted_count += 1

            # Eve measures her split-off photon in a random basis
            eve_basis = random.choice(  # noqa: S311
                [Basis.RECTILINEAR, Basis.DIAGONAL]
            )
            eve_result = self._measurement.measure(qubit, eve_basis)
            self._eve_bases.append(eve_basis)
            self._eve_results.append(eve_result.outcome)

            # The original qubit passes through undisturbed to Bob
            # (Eve has extra photons, doesn't need to resend)
            return qubit

        # Single-photon or vacuum pulse: passes through undisturbed
        # Eve records nothing for this pulse
        self._eve_bases.append(Basis.RECTILINEAR)  # placeholder
        self._eve_results.append(BitValue.ZERO)  # placeholder
        return qubit


class PartialInterceptChannel(AttackPort):
    """Partial intercept-resend attack.

    Eve intercepts only a configurable fraction of qubits, performing
    a full intercept-resend attack on those she intercepts. The remaining
    qubits pass through undisturbed.

    This trades information gained for lower detection probability.
    """

    def __init__(
        self,
        measurement: MeasurementPort,
        intercept_fraction: float = 0.5,
    ) -> None:
        if not 0.0 <= intercept_fraction <= 1.0:
            msg = "intercept_fraction must be between 0.0 and 1.0"
            raise ValueError(msg)
        self._measurement = measurement
        self._intercept_fraction = intercept_fraction
        self._eve_bases: list[Basis] = []
        self._eve_results: list[BitValue] = []
        self._total_count: int = 0
        self._intercepted_count: int = 0

    @property
    def eve_bases(self) -> list[Basis]:
        """Return the bases Eve chose for interception."""
        return list(self._eve_bases)

    @property
    def eve_results(self) -> list[BitValue]:
        """Return Eve's measurement results."""
        return list(self._eve_results)

    @property
    def eve_information_gain(self) -> float:
        """Return Eve's estimated information gain.

        Eve gains ~50% of intercepted bits' information on average
        (correct when her basis matches Alice's, which is 50% of the time).
        Overall: intercept_fraction * 0.5
        """
        return self._intercept_fraction * 0.5

    @property
    def intercepted_count(self) -> int:
        """Return the number of qubits Eve intercepted."""
        return self._intercepted_count

    @property
    def multi_photon_count(self) -> int:
        """Return the number of multi-photon pulses (always 0 for this attack)."""
        return 0

    @property
    def total_count(self) -> int:
        """Return the total number of qubits transmitted."""
        return self._total_count

    def clear(self) -> None:
        """Reset recorded Eve data for a new run."""
        self._eve_bases = []
        self._eve_results = []
        self._total_count = 0
        self._intercepted_count = 0

    def transmit(self, qubit: Qubit) -> Qubit:
        """Transmit a qubit, intercepting only a fraction.

        With probability intercept_fraction, Eve performs a full
        intercept-resend attack (measure in random basis, resend).
        Otherwise, the qubit passes through undisturbed.
        """
        self._total_count += 1

        if random.random() < self._intercept_fraction:  # noqa: S311
            self._intercepted_count += 1

            # Full intercept-resend on this qubit
            eve_basis = random.choice(  # noqa: S311
                [Basis.RECTILINEAR, Basis.DIAGONAL]
            )
            eve_result = self._measurement.measure(qubit, eve_basis)
            self._eve_bases.append(eve_basis)
            self._eve_results.append(eve_result.outcome)

            # Eve resends based on her measurement
            return self._measurement.prepare(eve_result.outcome, eve_basis)

        # Not intercepted -- pass through undisturbed
        self._eve_bases.append(Basis.RECTILINEAR)  # placeholder
        self._eve_results.append(BitValue.ZERO)  # placeholder
        return qubit
