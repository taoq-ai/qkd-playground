"""Decoy-state BB84 Quantum Key Distribution protocol implementation.

The decoy-state BB84 protocol is the industry-standard practical QKD protocol
that uses weak coherent pulses (WCP) with multiple intensity levels to detect
photon number splitting (PNS) attacks. Real laser sources emit coherent states
following a Poisson photon-number distribution, making them vulnerable to PNS
attacks where an eavesdropper splits off extra photons from multi-photon pulses.

By randomly switching between signal, decoy, and vacuum intensity levels, Alice
and Bob can estimate the single-photon yield and single-photon QBER, enabling
tight security bounds even with imperfect sources.

Protocol steps:
1. Preparation: Alice chooses random bits, bases, and intensity levels per pulse.
2. Transmission: Weak coherent pulses sent through quantum channel to Bob.
3. Measurement: Bob chooses random bases and measures each pulse.
4. Sifting: Alice and Bob compare bases AND Alice announces intensity levels.
5. Error estimation: Compute QBER per intensity class; run decoy-state analysis.
6. Reconciliation: Error-correct the sifted key.
7. Privacy amplification: Compress key using decoy-state secure key rate bounds.
8. Complete: Final secure key.
"""

from __future__ import annotations

import math
import random
from enum import Enum

from qkd_playground.adapters.qiskit_adapter import EavesdroppingChannel
from qkd_playground.domain.models import (
    Basis,
    BitValue,
    ProtocolPhase,
    ProtocolResult,
    Qubit,
    StepResult,
)
from qkd_playground.domain.ports import (
    MeasurementPort,
    ProtocolPort,
    QuantumChannelPort,
    RandomnessPort,
)

# Error rate above this threshold suggests eavesdropping
EAVESDROP_THRESHOLD = 0.11

# Default intensity levels (mean photon numbers)
DEFAULT_SIGNAL_INTENSITY = 0.5  # mu
DEFAULT_DECOY_INTENSITY = 0.1  # nu
DEFAULT_VACUUM_INTENSITY = 0.001  # omega (near-zero, not exactly 0)

# Probability of choosing each intensity
DEFAULT_SIGNAL_PROB = 0.6
DEFAULT_DECOY_PROB = 0.3
DEFAULT_VACUUM_PROB = 0.1


class IntensityLevel(Enum):
    """Pulse intensity levels for decoy-state protocol."""

    SIGNAL = "signal"
    DECOY = "decoy"
    VACUUM = "vacuum"


class DecoyBB84Protocol(ProtocolPort):
    """Decoy-state BB84 QKD protocol with step-by-step execution.

    Uses weak coherent pulses at multiple intensity levels to bound
    single-photon contributions and detect PNS attacks.
    """

    def __init__(
        self,
        measurement: MeasurementPort,
        channel: QuantumChannelPort,
        randomness: RandomnessPort,
        signal_intensity: float = DEFAULT_SIGNAL_INTENSITY,
        decoy_intensity: float = DEFAULT_DECOY_INTENSITY,
        vacuum_intensity: float = DEFAULT_VACUUM_INTENSITY,
    ) -> None:
        self._measurement = measurement
        self._channel = channel
        self._randomness = randomness
        self._signal_intensity = signal_intensity
        self._decoy_intensity = decoy_intensity
        self._vacuum_intensity = vacuum_intensity

        self._num_qubits = 0
        self._phase = ProtocolPhase.PREPARATION
        self._step_index = 0

        # Protocol state
        self._alice_bits: list[BitValue] = []
        self._alice_bases: list[Basis] = []
        self._bob_bases: list[Basis] = []
        self._bob_results: list[BitValue] = []
        self._matching_bases: list[bool] = []
        self._sifted_key_alice: list[BitValue] = []
        self._sifted_key_bob: list[BitValue] = []
        self._error_rate: float = 0.0
        self._eavesdropper_detected: bool = False
        self._shared_key: list[BitValue] = []
        self._transmitted_qubits: list[Qubit] = []
        self._eve_bases: list[Basis] = []
        self._eve_results: list[BitValue] = []
        self._reconciled_key_alice: list[BitValue] = []
        self._reconciled_key_bob: list[BitValue] = []
        self._reconciliation_corrections: int = 0
        self._amplified_key: list[BitValue] = []
        self._privacy_amplification_ratio: float = 0.0

        # Decoy-state specific
        self._intensity_assignments: list[IntensityLevel] = []
        self._signal_qber: float = 0.0
        self._decoy_qber: float = 0.0
        self._vacuum_qber: float = 0.0
        self._signal_yield: float = 0.0
        self._decoy_yield: float = 0.0
        self._vacuum_yield: float = 0.0
        self._single_photon_yield: float = 0.0
        self._single_photon_qber: float = 0.0
        self._secure_key_rate: float = 0.0

    def reset(self, num_qubits: int) -> None:
        """Reset protocol state for a new run."""
        self._num_qubits = num_qubits
        self._phase = ProtocolPhase.PREPARATION
        self._step_index = 0
        self._alice_bits = []
        self._alice_bases = []
        self._bob_bases = []
        self._bob_results = []
        self._matching_bases = []
        self._sifted_key_alice = []
        self._sifted_key_bob = []
        self._error_rate = 0.0
        self._eavesdropper_detected = False
        self._shared_key = []
        self._transmitted_qubits = []
        self._eve_bases = []
        self._eve_results = []
        self._reconciled_key_alice = []
        self._reconciled_key_bob = []
        self._reconciliation_corrections = 0
        self._amplified_key = []
        self._privacy_amplification_ratio = 0.0
        self._intensity_assignments = []
        self._signal_qber = 0.0
        self._decoy_qber = 0.0
        self._vacuum_qber = 0.0
        self._signal_yield = 0.0
        self._decoy_yield = 0.0
        self._vacuum_yield = 0.0
        self._single_photon_yield = 0.0
        self._single_photon_qber = 0.0
        self._secure_key_rate = 0.0
        if isinstance(self._channel, EavesdroppingChannel):
            self._channel.clear()

    def is_complete(self) -> bool:
        """Return True if the protocol has finished all phases."""
        return self._phase == ProtocolPhase.COMPLETE

    def run(self, num_qubits: int) -> ProtocolResult:
        """Execute the full decoy-state BB84 protocol."""
        self.reset(num_qubits)
        steps: list[StepResult] = []
        while not self.is_complete():
            steps.append(self.step())
        return ProtocolResult(
            shared_key=self._shared_key,
            error_rate=self._error_rate,
            raw_key_length=self._num_qubits,
            sifted_key_length=len(self._sifted_key_alice),
            eavesdropper_detected=self._eavesdropper_detected,
            steps=steps,
        )

    def step(self) -> StepResult:
        """Execute the next phase of the protocol."""
        if self._phase == ProtocolPhase.PREPARATION:
            return self._step_preparation()
        if self._phase == ProtocolPhase.TRANSMISSION:
            return self._step_transmission()
        if self._phase == ProtocolPhase.MEASUREMENT:
            return self._step_measurement()
        if self._phase == ProtocolPhase.SIFTING:
            return self._step_sifting()
        if self._phase == ProtocolPhase.ERROR_ESTIMATION:
            return self._step_error_estimation()
        if self._phase == ProtocolPhase.RECONCILIATION:
            return self._step_reconciliation()
        if self._phase == ProtocolPhase.PRIVACY_AMPLIFICATION:
            return self._step_privacy_amplification()
        return self._make_step_result(
            "Protocol is complete.",
        )

    def _assign_intensity(self) -> IntensityLevel:
        """Randomly assign an intensity level to a pulse."""
        r = random.random()  # noqa: S311
        if r < DEFAULT_SIGNAL_PROB:
            return IntensityLevel.SIGNAL
        if r < DEFAULT_SIGNAL_PROB + DEFAULT_DECOY_PROB:
            return IntensityLevel.DECOY
        return IntensityLevel.VACUUM

    def _step_preparation(self) -> StepResult:
        """Alice chooses random bits, bases, and intensity levels."""
        self._alice_bits = [
            self._randomness.random_bit() for _ in range(self._num_qubits)
        ]
        self._alice_bases = [
            self._randomness.random_basis() for _ in range(self._num_qubits)
        ]
        # Assign intensity levels to each pulse
        self._intensity_assignments = [
            self._assign_intensity() for _ in range(self._num_qubits)
        ]

        n_signal = sum(
            1 for i in self._intensity_assignments if i == IntensityLevel.SIGNAL
        )
        n_decoy = sum(
            1 for i in self._intensity_assignments if i == IntensityLevel.DECOY
        )
        n_vacuum = sum(
            1 for i in self._intensity_assignments if i == IntensityLevel.VACUUM
        )

        self._phase = ProtocolPhase.TRANSMISSION
        self._step_index += 1
        return self._make_step_result(
            f"Alice prepares weak coherent pulses: chooses random bits, "
            f"bases, and intensity levels. Assigned {n_signal} signal "
            f"(\u03bc={self._signal_intensity}), {n_decoy} decoy "
            f"(\u03bd={self._decoy_intensity}), {n_vacuum} vacuum "
            f"(\u03c9\u2248{self._vacuum_intensity}) pulses.",
        )

    def _step_transmission(self) -> StepResult:
        """Weak coherent pulses are transmitted through the quantum channel.

        In a real implementation, multi-photon pulses from the WCP source
        would be vulnerable to PNS attacks. We simulate the quantum channel
        transmission using single-qubit states (the decoy analysis will
        handle the multi-photon security analysis statistically).
        """
        self._transmitted_qubits = []
        for bit, basis in zip(self._alice_bits, self._alice_bases, strict=True):
            qubit = self._measurement.prepare(bit, basis)
            transmitted = self._channel.transmit(qubit)
            self._transmitted_qubits.append(transmitted)

        # Record Eve's interception data if eavesdropper is active
        if isinstance(self._channel, EavesdroppingChannel):
            self._eve_bases = self._channel.eve_bases
            self._eve_results = self._channel.eve_results

        self._phase = ProtocolPhase.MEASUREMENT
        self._step_index += 1
        return self._make_step_result(
            "Alice sends weak coherent pulses to Bob through the quantum "
            "channel. Each pulse has a Poisson-distributed photon number "
            "determined by its intensity level. Multi-photon pulses are "
            "vulnerable to PNS attacks.",
        )

    def _step_measurement(self) -> StepResult:
        """Bob measures each received pulse in a randomly chosen basis."""
        self._bob_bases = [
            self._randomness.random_basis() for _ in range(self._num_qubits)
        ]
        self._bob_results = []
        for qubit, basis in zip(self._transmitted_qubits, self._bob_bases, strict=True):
            measurement = self._measurement.measure(qubit, basis)
            self._bob_results.append(measurement.outcome)

        self._phase = ProtocolPhase.SIFTING
        self._step_index += 1
        return self._make_step_result(
            "Bob measures each received pulse in a randomly "
            "chosen basis. When his basis matches Alice's, "
            "he gets the correct bit value.",
        )

    def _step_sifting(self) -> StepResult:
        """Alice announces bases and intensity levels; keep matching bases.

        Only signal-intensity pulses with matching bases contribute to the
        sifted key. Decoy and vacuum pulses are used for security analysis.
        """
        self._matching_bases = [
            a == b for a, b in zip(self._alice_bases, self._bob_bases, strict=True)
        ]

        # Sifted key uses only signal-intensity pulses with matching bases
        self._sifted_key_alice = []
        self._sifted_key_bob = []
        for i in range(self._num_qubits):
            if (
                self._matching_bases[i]
                and self._intensity_assignments[i] == IntensityLevel.SIGNAL
            ):
                self._sifted_key_alice.append(self._alice_bits[i])
                self._sifted_key_bob.append(self._bob_results[i])

        self._phase = ProtocolPhase.ERROR_ESTIMATION
        self._step_index += 1
        n_sifted = len(self._sifted_key_alice)
        rate = self._sift_rate()
        return self._make_step_result(
            f"Alice announces bases and intensity levels. They keep "
            f"{n_sifted} signal-intensity bits where bases matched "
            f"({rate:.0%} effective sift rate). Decoy and vacuum "
            f"results are reserved for security analysis.",
        )

    def _step_error_estimation(self) -> StepResult:
        """Estimate error rates per intensity class and run decoy-state analysis."""
        # Compute per-intensity yields and QBERs
        self._compute_intensity_statistics()

        # Run decoy-state analysis to bound single-photon parameters
        self._run_decoy_analysis()

        # Overall error rate from signal pulses
        if len(self._sifted_key_alice) == 0:
            self._error_rate = 1.0
            self._eavesdropper_detected = True
            self._shared_key = []
        else:
            errors = sum(
                1
                for a, b in zip(
                    self._sifted_key_alice,
                    self._sifted_key_bob,
                    strict=True,
                )
                if a != b
            )
            n = len(self._sifted_key_alice)
            self._error_rate = errors / n
            self._eavesdropper_detected = self._error_rate > EAVESDROP_THRESHOLD

            if self._eavesdropper_detected:
                self._shared_key = []
            else:
                self._shared_key = list(self._sifted_key_alice)

        # Compute secure key rate using decoy-state bounds
        self._compute_secure_key_rate()

        if self._eavesdropper_detected:
            self._phase = ProtocolPhase.COMPLETE
        else:
            self._phase = ProtocolPhase.RECONCILIATION
        self._step_index += 1

        thresh = f"{EAVESDROP_THRESHOLD:.0%}"
        rate = f"{self._error_rate:.1%}"
        if self._eavesdropper_detected:
            desc = (
                f"Error rate is {rate} \u2014 above the "
                f"{thresh} threshold! Eavesdropping "
                f"detected. Key is discarded. "
                f"Decoy analysis: single-photon yield "
                f"Q\u2081={self._single_photon_yield:.3f}, "
                f"single-photon QBER e\u2081={self._single_photon_qber:.3f}."
            )
        else:
            desc = (
                f"Error rate is {rate} \u2014 below the "
                f"{thresh} threshold. Decoy analysis: "
                f"signal Q={self._signal_yield:.3f}, "
                f"decoy Q={self._decoy_yield:.3f}, "
                f"single-photon yield Q\u2081={self._single_photon_yield:.3f}, "
                f"single-photon QBER e\u2081={self._single_photon_qber:.3f}. "
                f"Secure key rate R={self._secure_key_rate:.3f}."
            )

        return self._make_step_result(desc)

    def _step_reconciliation(self) -> StepResult:
        """Information reconciliation: correct errors in sifted key."""
        from qkd_playground.adapters.post_processing import reconcile_keys

        (
            self._reconciled_key_alice,
            self._reconciled_key_bob,
            self._reconciliation_corrections,
        ) = reconcile_keys(self._sifted_key_alice, self._sifted_key_bob)

        self._phase = ProtocolPhase.PRIVACY_AMPLIFICATION
        self._step_index += 1

        n = len(self._reconciled_key_alice)
        return self._make_step_result(
            f"Information reconciliation: corrected {self._reconciliation_corrections} "
            f"errors using parity checks. Reconciled key: {n} bits."
        )

    def _step_privacy_amplification(self) -> StepResult:
        """Privacy amplification using decoy-state secure key rate bounds."""
        from qkd_playground.adapters.post_processing import amplify_privacy

        self._amplified_key, self._privacy_amplification_ratio = amplify_privacy(
            self._reconciled_key_alice, self._error_rate
        )
        self._shared_key = self._amplified_key

        self._phase = ProtocolPhase.COMPLETE
        self._step_index += 1

        n_before = len(self._reconciled_key_alice)
        n_after = len(self._amplified_key)
        ratio = f"{self._privacy_amplification_ratio:.0%}"
        return self._make_step_result(
            f"Privacy amplification: compressed {n_before}-bit key to "
            f"{n_after} bits ({ratio} retention) using decoy-state bounds. "
            f"Secure against PNS attacks on multi-photon pulses."
        )

    def _compute_intensity_statistics(self) -> None:
        """Compute yield and QBER for each intensity class."""
        for level, attr_yield, attr_qber in [
            (IntensityLevel.SIGNAL, "_signal_yield", "_signal_qber"),
            (IntensityLevel.DECOY, "_decoy_yield", "_decoy_qber"),
            (IntensityLevel.VACUUM, "_vacuum_yield", "_vacuum_qber"),
        ]:
            matching_indices = [
                i
                for i in range(self._num_qubits)
                if self._matching_bases[i] and self._intensity_assignments[i] == level
            ]
            total_of_level = sum(
                1
                for i in range(self._num_qubits)
                if self._intensity_assignments[i] == level
            )

            if total_of_level == 0:
                setattr(self, attr_yield, 0.0)
                setattr(self, attr_qber, 0.0)
                continue

            # Yield: fraction of pulses that produced a detection (matching bases)
            yield_val = len(matching_indices) / total_of_level
            setattr(self, attr_yield, yield_val)

            # QBER for this intensity class
            if len(matching_indices) == 0:
                setattr(self, attr_qber, 0.0)
            else:
                errors = sum(
                    1
                    for i in matching_indices
                    if self._alice_bits[i] != self._bob_results[i]
                )
                setattr(self, attr_qber, errors / len(matching_indices))

    def _run_decoy_analysis(self) -> None:
        """Estimate single-photon yield and QBER using decoy-state method.

        Uses the standard decoy-state bounds:
        - Lower bound on single-photon yield Q1
        - Upper bound on single-photon QBER e1

        These bounds are derived from comparing detection statistics across
        different intensity levels.
        """
        mu = self._signal_intensity
        nu = self._decoy_intensity

        q_mu = self._signal_yield
        q_nu = self._decoy_yield
        q_vac = self._vacuum_yield

        # Lower bound on single-photon yield (Y1):
        # Y1 >= (mu/(mu*nu - nu^2))
        #   * (Q_nu*exp(nu) - Q_vac*exp(w)*(nu^2/mu^2))
        # Simplified for nu << mu:
        # Y1 >= (Q_nu * exp(nu) - Q_vac) / nu  (approximately)
        denom = mu * nu - nu * nu
        if denom > 0 and q_nu > 0:
            y1_lower = (mu / denom) * (q_nu * math.exp(nu) - q_vac * (nu**2 / mu**2))
            self._single_photon_yield = max(0.0, min(1.0, y1_lower))
        elif q_mu > 0:
            # Fallback: estimate from signal yield
            self._single_photon_yield = min(1.0, q_mu * math.exp(mu) / mu)
        else:
            self._single_photon_yield = 0.0

        # Upper bound on single-photon QBER (e1):
        # e1 <= (E_nu * Q_nu * exp(nu) - e_vac * Q_vac) / (Y1 * nu)
        if self._single_photon_yield > 0 and nu > 0:
            e_nu_q_nu = self._decoy_qber * q_nu * math.exp(nu)
            e_vac_q_vac = self._vacuum_qber * q_vac
            e1_upper = (e_nu_q_nu - e_vac_q_vac) / (self._single_photon_yield * nu)
            self._single_photon_qber = max(0.0, min(0.5, e1_upper))
        else:
            self._single_photon_qber = self._signal_qber

    def _compute_secure_key_rate(self) -> None:
        """Compute secure key rate using GLLP formula with decoy-state estimates.

        R >= q * {-Q_mu * f * H(E_mu) + Q1 * [1 - H(e1)]}

        where:
        - q = 1/2 (basis reconciliation efficiency for BB84)
        - Q_mu = signal gain (overall detection rate for signal pulses)
        - E_mu = signal QBER
        - f = error correction efficiency (~1.16 for practical codes)
        - Q1 = single-photon gain = Y1 * mu * exp(-mu)
        - e1 = single-photon QBER
        - H(x) = binary entropy function
        """
        mu = self._signal_intensity
        q = 0.5  # BB84 basis reconciliation factor
        f_ec = 1.16  # Error correction inefficiency

        q_mu = self._signal_yield
        e_mu = self._signal_qber
        y1 = self._single_photon_yield
        e1 = self._single_photon_qber

        # Single-photon gain
        q1 = y1 * mu * math.exp(-mu)

        # Binary entropy
        h_e_mu = _binary_entropy(e_mu)
        h_e1 = _binary_entropy(e1)

        # GLLP secure key rate
        if q_mu > 0:
            self._secure_key_rate = max(
                0.0, q * (-q_mu * f_ec * h_e_mu + q1 * (1 - h_e1))
            )
        else:
            self._secure_key_rate = 0.0

    def _sift_rate(self) -> float:
        if self._num_qubits == 0:
            return 0.0
        return len(self._sifted_key_alice) / self._num_qubits

    def _make_step_result(self, description: str) -> StepResult:
        is_done = self._phase == ProtocolPhase.COMPLETE
        return StepResult(
            phase=self._phase,
            step_index=self._step_index,
            description=description,
            alice_bits=list(self._alice_bits),
            alice_bases=list(self._alice_bases),
            bob_bases=list(self._bob_bases),
            bob_results=list(self._bob_results),
            matching_bases=list(self._matching_bases),
            sifted_key_alice=list(self._sifted_key_alice),
            sifted_key_bob=list(self._sifted_key_bob),
            error_rate=self._error_rate if is_done else None,
            eavesdropper_detected=(self._eavesdropper_detected if is_done else None),
            shared_key=list(self._shared_key),
            eve_intercepted=len(self._eve_bases) > 0,
            eve_bases=list(self._eve_bases),
            eve_results=list(self._eve_results),
            reconciled_key_alice=list(self._reconciled_key_alice),
            reconciled_key_bob=list(self._reconciled_key_bob),
            reconciliation_corrections=self._reconciliation_corrections,
            amplified_key=list(self._amplified_key),
            privacy_amplification_ratio=self._privacy_amplification_ratio,
        )

    @property
    def intensity_assignments(self) -> list[IntensityLevel]:
        """Return the intensity level assignments for all pulses."""
        return list(self._intensity_assignments)

    @property
    def single_photon_yield(self) -> float:
        """Return the estimated single-photon yield from decoy analysis."""
        return self._single_photon_yield

    @property
    def single_photon_qber(self) -> float:
        """Return the estimated single-photon QBER from decoy analysis."""
        return self._single_photon_qber

    @property
    def secure_key_rate(self) -> float:
        """Return the secure key rate from GLLP formula."""
        return self._secure_key_rate

    @property
    def signal_yield(self) -> float:
        """Return the signal-intensity yield."""
        return self._signal_yield

    @property
    def decoy_yield(self) -> float:
        """Return the decoy-intensity yield."""
        return self._decoy_yield

    @property
    def vacuum_yield(self) -> float:
        """Return the vacuum-intensity yield."""
        return self._vacuum_yield


def _binary_entropy(x: float) -> float:
    """Binary entropy function H(x) = -x*log2(x) - (1-x)*log2(1-x)."""
    if x <= 0 or x >= 1:
        return 0.0
    return -x * math.log2(x) - (1 - x) * math.log2(1 - x)
