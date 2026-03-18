"""Bell test (CHSH inequality) simulator.

Runs a standalone Bell test experiment: creates entangled Bell pairs
|Phi+> = (|00> + |11>)/sqrt(2), measures at arbitrary angles chosen by
Alice and Bob, and computes the CHSH S parameter.

Default CHSH angles (maximally violating):
  a = 0 deg, a' = 45 deg, b = 22.5 deg, b' = 67.5 deg
  -> S = 2*sqrt(2) ~ 2.83
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from qiskit import QuantumCircuit  # type: ignore[import-untyped]
from qiskit.primitives import StatevectorSampler  # type: ignore[import-untyped]


@dataclass(frozen=True)
class AnglePair:
    """A pair of measurement angles (Alice, Bob) in radians."""

    alice: float
    bob: float


@dataclass(frozen=True)
class CorrelationResult:
    """Correlation measurement outcome for one angle pair."""

    alice_angle: float
    bob_angle: float
    correlation: float
    counts: dict[str, int]  # {"++": n, "+-": n, "-+": n, "--": n}


@dataclass(frozen=True)
class BellTestResult:
    """Full Bell test result."""

    correlations: list[CorrelationResult]
    s_value: float
    num_trials: int


# Default CHSH angles (in degrees) that maximally violate the inequality.
DEFAULT_ALICE_ANGLES: tuple[float, float] = (0.0, 45.0)
DEFAULT_BOB_ANGLES: tuple[float, float] = (22.5, 67.5)


class BellTestSimulator:
    """Simulates a CHSH Bell test using Qiskit.

    Creates Bell pairs |Phi+> = (|00> + |11>)/sqrt(2) and measures
    each party's qubit at configurable angles.
    """

    def __init__(self) -> None:
        self._sampler = StatevectorSampler()

    def _measure_at_angles(
        self,
        alice_angle_deg: float,
        bob_angle_deg: float,
        num_trials: int,
    ) -> CorrelationResult:
        """Measure a Bell pair with Alice and Bob at given angles.

        The angle determines a measurement axis in the X-Z plane.
        A rotation Ry(-2*theta) followed by a Z-basis measurement is
        equivalent to measuring along an axis at angle theta from the Z axis.
        """
        alice_rad = math.radians(alice_angle_deg)
        bob_rad = math.radians(bob_angle_deg)

        qc = QuantumCircuit(2, 2)
        # Create Bell state |Phi+>
        qc.h(0)
        qc.cx(0, 1)

        # Rotate to measurement basis
        qc.ry(-2 * alice_rad, 0)
        qc.ry(-2 * bob_rad, 1)

        qc.measure([0, 1], [0, 1])

        job = self._sampler.run([qc], shots=num_trials)
        result = job.result()
        raw_counts = result[0].data.c.get_counts()

        # Parse counts into ++ / +- / -+ / -- categories
        # Convention: 0 -> +1, 1 -> -1
        # Qiskit bit order: rightmost = qubit 0 (Alice)
        outcome_counts = {"++": 0, "+-": 0, "-+": 0, "--": 0}
        for bitstring, count in raw_counts.items():
            alice_bit = int(bitstring[-1])  # qubit 0
            bob_bit = int(bitstring[-2])  # qubit 1
            alice_sign = "+" if alice_bit == 0 else "-"
            bob_sign = "+" if bob_bit == 0 else "-"
            outcome_counts[f"{alice_sign}{bob_sign}"] += count

        n_total = sum(outcome_counts.values())
        correlation = (
            outcome_counts["++"]
            + outcome_counts["--"]
            - outcome_counts["+-"]
            - outcome_counts["-+"]
        ) / n_total

        return CorrelationResult(
            alice_angle=alice_angle_deg,
            bob_angle=bob_angle_deg,
            correlation=correlation,
            counts=outcome_counts,
        )

    def run(
        self,
        alice_angles: tuple[float, float] = DEFAULT_ALICE_ANGLES,
        bob_angles: tuple[float, float] = DEFAULT_BOB_ANGLES,
        num_trials: int = 1000,
    ) -> BellTestResult:
        """Run a full CHSH Bell test.

        Measures four angle-pair combinations and computes:
          S = E(a,b) - E(a,b') + E(a',b) + E(a',b')

        Parameters
        ----------
        alice_angles : tuple of two floats
            Alice's measurement angles a, a' in degrees.
        bob_angles : tuple of two floats
            Bob's measurement angles b, b' in degrees.
        num_trials : int
            Number of measurement shots per angle pair.

        Returns
        -------
        BellTestResult
            Correlations and CHSH S value.
        """
        a, a_prime = alice_angles
        b, b_prime = bob_angles

        e_ab = self._measure_at_angles(a, b, num_trials)
        e_ab_prime = self._measure_at_angles(a, b_prime, num_trials)
        e_a_prime_b = self._measure_at_angles(a_prime, b, num_trials)
        e_a_prime_b_prime = self._measure_at_angles(a_prime, b_prime, num_trials)

        correlations = [e_ab, e_ab_prime, e_a_prime_b, e_a_prime_b_prime]

        s_value = (
            e_ab.correlation
            - e_ab_prime.correlation
            + e_a_prime_b.correlation
            + e_a_prime_b_prime.correlation
        )

        return BellTestResult(
            correlations=correlations,
            s_value=s_value,
            num_trials=num_trials,
        )

    @staticmethod
    def theoretical_correlation(alice_deg: float, bob_deg: float) -> float:
        """Theoretical quantum correlation for |Phi+> state.

        E(a,b) = cos(2*(a - b)) for the Bell state |Phi+> with
        Ry-rotation measurement convention.
        """
        diff_rad = math.radians(alice_deg - bob_deg)
        return float(np.cos(2 * diff_rad))

    @staticmethod
    def theoretical_s(
        alice_angles: tuple[float, float] = DEFAULT_ALICE_ANGLES,
        bob_angles: tuple[float, float] = DEFAULT_BOB_ANGLES,
    ) -> float:
        """Theoretical CHSH S value for given angles."""
        a, a_prime = alice_angles
        b, b_prime = bob_angles
        e_ab = math.cos(2 * math.radians(a - b))
        e_ab_p = math.cos(2 * math.radians(a - b_prime))
        e_ap_b = math.cos(2 * math.radians(a_prime - b))
        e_ap_bp = math.cos(2 * math.radians(a_prime - b_prime))
        return e_ab - e_ab_p + e_ap_b + e_ap_bp
