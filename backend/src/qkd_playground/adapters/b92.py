"""B92 Quantum Key Distribution protocol implementation.

The B92 protocol was proposed by Bennett in 1992. It is a simplified version
of BB84 that uses only two non-orthogonal states instead of four.

Alice encodes:
  - bit 0 → |0⟩ (rectilinear basis)
  - bit 1 → |+⟩ (diagonal basis)

Bob measures in a randomly chosen basis. A result is "conclusive" only when
Bob gets outcome 1 in his chosen basis — this confirms what Alice sent.
Inconclusive results (~75%) are discarded.

Protocol steps:
1. Preparation: Alice chooses random bits, encodes in 2 non-orthogonal states.
2. Transmission: Qubits sent through quantum channel to Bob.
3. Measurement: Bob measures each qubit in a randomly chosen basis.
4. Sifting: Bob announces which positions gave conclusive results.
5. Error estimation: Compare a sample of the sifted key for error rate.
"""

from __future__ import annotations

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

# B92 is more sensitive to eavesdropping than BB84
EAVESDROP_THRESHOLD = 0.15


class B92Protocol(ProtocolPort):
    """B92 QKD protocol with step-by-step execution."""

    def __init__(
        self,
        measurement: MeasurementPort,
        channel: QuantumChannelPort,
        randomness: RandomnessPort,
    ) -> None:
        self._measurement = measurement
        self._channel = channel
        self._randomness = randomness

        self._num_qubits = 0
        self._phase = ProtocolPhase.PREPARATION
        self._step_index = 0

        # Protocol state
        self._alice_bits: list[BitValue] = []
        self._alice_bases: list[Basis] = []
        self._bob_bases: list[Basis] = []
        self._bob_results: list[BitValue] = []
        self._conclusive_mask: list[bool] = []
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

    def reset(self, num_qubits: int) -> None:
        """Reset protocol state for a new run."""
        self._num_qubits = num_qubits
        self._phase = ProtocolPhase.PREPARATION
        self._step_index = 0
        self._alice_bits = []
        self._alice_bases = []
        self._bob_bases = []
        self._bob_results = []
        self._conclusive_mask = []
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
        if self._phase == ProtocolPhase.RECONCILIATION:
            return self._step_reconciliation()
        if self._phase == ProtocolPhase.PRIVACY_AMPLIFICATION:
            return self._step_privacy_amplification()
        return self._make_step_result("Protocol is complete.")

    def _step_preparation(self) -> StepResult:
        """Alice chooses random bits and encodes in non-orthogonal states.

        bit 0 → |0⟩ (rectilinear basis, value ZERO)
        bit 1 → |+⟩ (diagonal basis, value ONE — since H|0⟩ = |+⟩)
        """
        self._alice_bits = [
            self._randomness.random_bit() for _ in range(self._num_qubits)
        ]
        # In B92, the basis is determined by the bit value
        self._alice_bases = [
            (Basis.RECTILINEAR if bit == BitValue.ZERO else Basis.DIAGONAL)
            for bit in self._alice_bits
        ]

        self._phase = ProtocolPhase.TRANSMISSION
        self._step_index += 1
        return self._make_step_result(
            "Alice prepares qubits using two non-orthogonal "
            "states: |0⟩ for bit 0, |+⟩ for bit 1.",
        )

    def _step_transmission(self) -> StepResult:
        self._transmitted_qubits = []
        for _bit, basis in zip(self._alice_bits, self._alice_bases, strict=True):
            # B92 encoding: bit 0 → |0⟩, bit 1 → |+⟩
            # For bit 0: prepare ZERO in RECTILINEAR = |0⟩
            # For bit 1: prepare ZERO in DIAGONAL = |+⟩ (H|0⟩)
            value = BitValue.ZERO
            qubit = self._measurement.prepare(value, basis)
            transmitted = self._channel.transmit(qubit)
            self._transmitted_qubits.append(transmitted)

        # Record Eve's interception data if eavesdropper is active
        if isinstance(self._channel, EavesdroppingChannel):
            self._eve_bases = self._channel.eve_bases
            self._eve_results = self._channel.eve_results

        self._phase = ProtocolPhase.MEASUREMENT
        self._step_index += 1
        return self._make_step_result(
            "Alice sends qubits to Bob through the quantum "
            "channel. If an eavesdropper is present, they may "
            "intercept and disturb the qubits.",
        )

    def _step_measurement(self) -> StepResult:
        """Bob measures each qubit in a randomly chosen basis.

        A measurement is conclusive when Bob gets outcome ONE:
        - Measuring |0⟩ in diagonal gives random result
        - Measuring |+⟩ in rectilinear gives random result
        - Getting ONE confirms the state was NOT the eigenstate
          of Bob's basis → reveals Alice's bit.
        """
        self._bob_bases = [
            self._randomness.random_basis() for _ in range(self._num_qubits)
        ]
        self._bob_results = []
        self._conclusive_mask = []

        for qubit, basis in zip(self._transmitted_qubits, self._bob_bases, strict=True):
            m = self._measurement.measure(qubit, basis)
            self._bob_results.append(m.outcome)
            # Conclusive only when result is ONE
            self._conclusive_mask.append(m.outcome == BitValue.ONE)

        self._phase = ProtocolPhase.SIFTING
        self._step_index += 1
        n_conclusive = sum(self._conclusive_mask)
        return self._make_step_result(
            f"Bob measures each qubit in a random basis. "
            f"{n_conclusive} of {self._num_qubits} measurements "
            f"are conclusive (outcome = 1).",
        )

    def _step_sifting(self) -> StepResult:
        """Keep only positions where Bob got conclusive results."""
        # matching_bases tracks which positions are kept (conclusive)
        self._matching_bases = list(self._conclusive_mask)

        # For conclusive measurements, Bob can infer Alice's bit:
        # If Bob measured in DIAGONAL and got 1 → Alice sent |0⟩ → bit 0
        # If Bob measured in RECTILINEAR and got 1 → Alice sent |+⟩ → bit 1
        self._sifted_key_alice = [
            bit
            for bit, kept in zip(self._alice_bits, self._conclusive_mask, strict=True)
            if kept
        ]
        # Bob infers Alice's bit from his basis choice
        self._sifted_key_bob = [
            (BitValue.ZERO if basis == Basis.DIAGONAL else BitValue.ONE)
            for basis, kept in zip(self._bob_bases, self._conclusive_mask, strict=True)
            if kept
        ]

        self._phase = ProtocolPhase.ERROR_ESTIMATION
        self._step_index += 1
        n_sifted = len(self._sifted_key_alice)
        rate = n_sifted / self._num_qubits if self._num_qubits > 0 else 0.0
        return self._make_step_result(
            f"Bob announces which measurements were conclusive. "
            f"They keep {n_sifted} of {self._num_qubits} bits "
            f"({rate:.0%} sift rate).",
        )

    def _step_error_estimation(self) -> StepResult:
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

        if self._eavesdropper_detected:
            self._phase = ProtocolPhase.COMPLETE
        else:
            self._phase = ProtocolPhase.RECONCILIATION
        self._step_index += 1

        thresh = f"{EAVESDROP_THRESHOLD:.0%}"
        rate = f"{self._error_rate:.1%}"
        if self._eavesdropper_detected:
            desc = (
                f"Error rate is {rate} — above the "
                f"{thresh} threshold! Eavesdropping "
                f"detected. Key is discarded."
            )
        else:
            desc = (
                f"Error rate is {rate} — below the "
                f"{thresh} threshold. No eavesdropping "
                f"detected. Shared key: "
                f"{len(self._shared_key)} bits."
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
        """Privacy amplification: compress key to remove Eve's information."""
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
            f"{n_after} bits ({ratio} retention) using universal hashing. "
            f"Eve's information has been removed."
        )

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
            conclusive_mask=list(self._conclusive_mask),
            eve_intercepted=len(self._eve_bases) > 0,
            eve_bases=list(self._eve_bases),
            eve_results=list(self._eve_results),
            reconciled_key_alice=list(self._reconciled_key_alice),
            reconciled_key_bob=list(self._reconciled_key_bob),
            reconciliation_corrections=self._reconciliation_corrections,
            amplified_key=list(self._amplified_key),
            privacy_amplification_ratio=self._privacy_amplification_ratio,
        )
