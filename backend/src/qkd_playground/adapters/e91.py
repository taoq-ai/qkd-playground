"""E91 Quantum Key Distribution protocol implementation.

The E91 protocol was proposed by Ekert in 1991. It is based on quantum
entanglement and uses Bell's inequality (CHSH variant) to detect
eavesdropping.

Protocol steps:
1. Preparation: Generate entangled Bell pairs |Φ+⟩ = (|00⟩ + |11⟩)/√2.
2. Transmission: Bob's halves sent through quantum channel.
3. Measurement: Alice and Bob each choose a random basis and measure.
4. Sifting: Matching bases → key bits; non-matching → correlation data.
5. Error estimation: Compute error rate + correlation for security.

Note: This simplified implementation uses 2 bases (rectilinear, diagonal).
The full E91 uses 3 bases per party at optimal angles for CHSH > 2.
With only 2 bases, the correlation coefficient serves as an indicator
of entanglement quality, while the error rate provides the primary
security check.
"""

from __future__ import annotations

from qkd_playground.adapters.qiskit_adapter import (
    EavesdroppingChannel,  # noqa: TCH001
    QiskitEntanglementAdapter,  # noqa: TCH001
)
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

EAVESDROP_THRESHOLD = 0.11


class E91Protocol(ProtocolPort):
    """E91 QKD protocol with step-by-step execution."""

    def __init__(
        self,
        measurement: MeasurementPort,
        channel: QuantumChannelPort,
        entanglement: QiskitEntanglementAdapter,
        randomness: RandomnessPort,
    ) -> None:
        self._measurement = measurement
        self._channel = channel
        self._entanglement = entanglement
        self._randomness = randomness

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
        self._chsh_value: float | None = None

        # Entanglement state
        self._alice_qubits: list[Qubit] = []
        self._bob_qubits: list[Qubit] = []
        self._disturbed: list[bool] = []
        self._eve_bases: list[Basis] = []
        self._eve_results: list[BitValue] = []

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
        self._chsh_value = None
        self._alice_qubits = []
        self._bob_qubits = []
        self._disturbed = []
        self._eve_bases = []
        self._eve_results = []
        if isinstance(self._channel, EavesdroppingChannel):
            self._channel.clear()

    def is_complete(self) -> bool:
        return self._phase == ProtocolPhase.COMPLETE

    def run(self, num_qubits: int) -> ProtocolResult:
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
        return self._make_step_result("Protocol is complete.")

    def _step_preparation(self) -> StepResult:
        """Generate entangled Bell pairs for Alice and Bob."""
        self._alice_qubits = []
        self._bob_qubits = []

        for _ in range(self._num_qubits):
            alice_qubit, bob_qubit = self._entanglement.generate_bell_pair()
            self._alice_qubits.append(alice_qubit)
            self._bob_qubits.append(bob_qubit)

        self._phase = ProtocolPhase.TRANSMISSION
        self._step_index += 1
        return self._make_step_result(
            f"Generate {self._num_qubits} entangled Bell pairs "
            f"|Φ+⟩ = (|00⟩ + |11⟩)/√2. Alice keeps one half, "
            f"Bob's halves are sent through the channel.",
        )

    def _step_transmission(self) -> StepResult:
        """Transmit Bob's halves through the quantum channel.

        Track which qubits were disturbed by the channel (eavesdropper).
        """
        original_bob = list(self._bob_qubits)
        self._bob_qubits = [self._channel.transmit(q) for q in self._bob_qubits]
        # Track which pairs had their entanglement broken
        self._disturbed = [
            transmitted is not original
            for transmitted, original in zip(
                self._bob_qubits, original_bob, strict=True
            )
        ]

        # Record Eve's interception data if eavesdropper is active
        if isinstance(self._channel, EavesdroppingChannel):
            self._eve_bases = self._channel.eve_bases
            self._eve_results = self._channel.eve_results

        self._phase = ProtocolPhase.MEASUREMENT
        self._step_index += 1
        return self._make_step_result(
            "Bob's halves of the Bell pairs are transmitted "
            "through the quantum channel. An eavesdropper "
            "would disturb the entanglement correlations.",
        )

    def _step_measurement(self) -> StepResult:
        """Alice and Bob each measure in random bases.

        For undisturbed pairs, use the entanglement adapter's
        measure_bell_pair() to get proper quantum correlations.
        For disturbed pairs (Eve intercepted), measure independently.
        """
        self._alice_bases = [
            self._randomness.random_basis() for _ in range(self._num_qubits)
        ]
        self._bob_bases = [
            self._randomness.random_basis() for _ in range(self._num_qubits)
        ]

        self._alice_bits = []
        self._bob_results = []

        for i in range(self._num_qubits):
            if self._disturbed[i]:
                # Eve broke entanglement — measure independently
                a = self._measurement.measure(
                    self._alice_qubits[i], self._alice_bases[i]
                )
                b = self._measurement.measure(self._bob_qubits[i], self._bob_bases[i])
                self._alice_bits.append(a.outcome)
                self._bob_results.append(b.outcome)
            else:
                # Proper entangled measurement
                a_val, b_val = self._entanglement.measure_bell_pair(
                    self._alice_bases[i], self._bob_bases[i]
                )
                self._alice_bits.append(a_val)
                self._bob_results.append(b_val)

        self._phase = ProtocolPhase.SIFTING
        self._step_index += 1
        return self._make_step_result(
            "Alice and Bob each measure their qubits in "
            "randomly chosen bases (rectilinear or diagonal).",
        )

    def _step_sifting(self) -> StepResult:
        """Matching bases → key; non-matching → CHSH test."""
        self._matching_bases = [
            a == b for a, b in zip(self._alice_bases, self._bob_bases, strict=True)
        ]

        self._sifted_key_alice = [
            bit
            for bit, match in zip(self._alice_bits, self._matching_bases, strict=True)
            if match
        ]
        self._sifted_key_bob = [
            bit
            for bit, match in zip(self._bob_results, self._matching_bases, strict=True)
            if match
        ]

        self._phase = ProtocolPhase.ERROR_ESTIMATION
        self._step_index += 1
        n_matching = sum(self._matching_bases)
        n_chsh = self._num_qubits - n_matching
        return self._make_step_result(
            f"Alice and Bob compare bases publicly. "
            f"{n_matching} matching bases → key bits; "
            f"{n_chsh} non-matching → CHSH test data.",
        )

    def _compute_chsh(self) -> float:
        """Compute the CHSH S value from non-matching basis pairs.

        S = |E(R,R) - E(R,D)| + |E(D,R) + E(D,D)|

        where E(a,b) is the correlation coefficient for basis pair (a,b).
        For entangled pairs, S ≈ 2√2 ≈ 2.83.
        For non-matching bases, we compute correlations.
        """
        # Collect outcomes for each basis combination
        correlations: dict[tuple[Basis, Basis], list[float]] = {
            (Basis.RECTILINEAR, Basis.RECTILINEAR): [],
            (Basis.RECTILINEAR, Basis.DIAGONAL): [],
            (Basis.DIAGONAL, Basis.RECTILINEAR): [],
            (Basis.DIAGONAL, Basis.DIAGONAL): [],
        }

        for i in range(self._num_qubits):
            ab = self._alice_bases[i]
            bb = self._bob_bases[i]
            # Convert to ±1 values: 0 → +1, 1 → -1
            a_val = 1 if self._alice_bits[i] == BitValue.ZERO else -1
            b_val = 1 if self._bob_results[i] == BitValue.ZERO else -1
            correlations[(ab, bb)].append(a_val * b_val)

        def mean_corr(pairs: list[float]) -> float:
            return sum(pairs) / len(pairs) if pairs else 0.0

        e_rr = mean_corr(correlations[(Basis.RECTILINEAR, Basis.RECTILINEAR)])
        e_rd = mean_corr(correlations[(Basis.RECTILINEAR, Basis.DIAGONAL)])
        e_dr = mean_corr(correlations[(Basis.DIAGONAL, Basis.RECTILINEAR)])
        e_dd = mean_corr(correlations[(Basis.DIAGONAL, Basis.DIAGONAL)])

        return abs(e_rr - e_rd) + abs(e_dr + e_dd)

    def _step_error_estimation(self) -> StepResult:
        """Compute error rate and CHSH inequality."""
        # Compute CHSH S value
        self._chsh_value = self._compute_chsh()

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

            # Detect eavesdropping via error rate
            self._eavesdropper_detected = self._error_rate > EAVESDROP_THRESHOLD

            if self._eavesdropper_detected:
                self._shared_key = []
            else:
                self._shared_key = list(self._sifted_key_alice)

        self._phase = ProtocolPhase.COMPLETE
        self._step_index += 1

        chsh_str = f"{self._chsh_value:.3f}"
        rate = f"{self._error_rate:.1%}"
        thresh = f"{EAVESDROP_THRESHOLD:.0%}"

        if self._eavesdropper_detected:
            desc = (
                f"Error rate: {rate} — above {thresh} threshold. "
                f"Correlation S = {chsh_str}. "
                f"Eavesdropping detected! Key is discarded."
            )
        else:
            desc = (
                f"Error rate: {rate} — below {thresh} threshold. "
                f"Correlation S = {chsh_str}. "
                f"No eavesdropping detected. Shared key: "
                f"{len(self._shared_key)} bits."
            )

        return self._make_step_result(desc)

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
            chsh_value=self._chsh_value if is_done else None,
            eve_intercepted=len(self._eve_bases) > 0,
            eve_bases=list(self._eve_bases),
            eve_results=list(self._eve_results),
        )
