"""Measurement-Device-Independent QKD protocol implementation.

MDI-QKD eliminates all detector side-channel attacks by placing the
measurement device at an untrusted relay node (Charlie). Alice and Bob
both send qubits to Charlie, who performs Bell State Measurements (BSM)
on each pair. Even if Charlie is compromised or malicious, the protocol
remains secure because Charlie only learns BSM outcomes, never individual
qubit states.

Protocol steps:
1. Preparation: Alice and Bob independently choose random bits and bases,
   prepare qubits.
2. Transmission: Alice and Bob both send their qubits to Charlie through
   quantum channels (which may have eavesdroppers).
3. Measurement: Charlie performs Bell State Measurement on each pair.
   ~50% of BSMs succeed (only |Ψ-⟩ and |Ψ+⟩ are distinguishable with
   linear optics). Charlie announces which pairs succeeded and which
   Bell state was detected.
4. Sifting: Alice and Bob compare bases, keeping only pairs where they
   used the same basis AND Charlie got a successful BSM. Bob flips his
   bit when needed based on the Bell state Charlie announced.
5. Error estimation: Sample sifted key positions to estimate QBER.
6. Reconciliation: Use existing post-processing module.
7. Privacy amplification: Use existing post-processing module.
"""

from __future__ import annotations

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


class BellState(Enum):
    """Bell states that Charlie can detect."""

    PSI_MINUS = "psi_minus"  # |Ψ-⟩ = (|01⟩ - |10⟩)/√2
    PSI_PLUS = "psi_plus"  # |Ψ+⟩ = (|01⟩ + |10⟩)/√2


class MDIQKDProtocol(ProtocolPort):
    """MDI-QKD protocol with step-by-step execution.

    Three-party protocol: Alice, Bob, and Charlie (untrusted relay).
    Security does not depend on Charlie's honesty.
    """

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
        self._bob_bits: list[BitValue] = []
        self._bob_bases: list[Basis] = []
        self._bob_results: list[BitValue] = []
        self._matching_bases: list[bool] = []
        self._sifted_key_alice: list[BitValue] = []
        self._sifted_key_bob: list[BitValue] = []
        self._error_rate: float = 0.0
        self._eavesdropper_detected: bool = False
        self._shared_key: list[BitValue] = []
        self._eve_bases: list[Basis] = []
        self._eve_results: list[BitValue] = []
        self._reconciled_key_alice: list[BitValue] = []
        self._reconciled_key_bob: list[BitValue] = []
        self._reconciliation_corrections: int = 0
        self._amplified_key: list[BitValue] = []
        self._privacy_amplification_ratio: float = 0.0

        # MDI-specific state
        self._alice_qubits: list[Qubit] = []
        self._bob_qubits: list[Qubit] = []
        self._transmitted_alice_qubits: list[Qubit] = []
        self._transmitted_bob_qubits: list[Qubit] = []
        self._bsm_success: list[bool] = []
        self._bsm_results: list[BellState | None] = []

    def reset(self, num_qubits: int) -> None:
        """Reset protocol state for a new run."""
        self._num_qubits = num_qubits
        self._phase = ProtocolPhase.PREPARATION
        self._step_index = 0
        self._alice_bits = []
        self._alice_bases = []
        self._bob_bits = []
        self._bob_bases = []
        self._bob_results = []
        self._matching_bases = []
        self._sifted_key_alice = []
        self._sifted_key_bob = []
        self._error_rate = 0.0
        self._eavesdropper_detected = False
        self._shared_key = []
        self._eve_bases = []
        self._eve_results = []
        self._reconciled_key_alice = []
        self._reconciled_key_bob = []
        self._reconciliation_corrections = 0
        self._amplified_key = []
        self._privacy_amplification_ratio = 0.0
        self._alice_qubits = []
        self._bob_qubits = []
        self._transmitted_alice_qubits = []
        self._transmitted_bob_qubits = []
        self._bsm_success = []
        self._bsm_results = []
        if isinstance(self._channel, EavesdroppingChannel):
            self._channel.clear()

    def is_complete(self) -> bool:
        """Return True if the protocol has finished all phases."""
        return self._phase == ProtocolPhase.COMPLETE

    def run(self, num_qubits: int) -> ProtocolResult:
        """Execute the full MDI-QKD protocol."""
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

    def _step_preparation(self) -> StepResult:
        """Alice and Bob independently choose random bits and bases."""
        self._alice_bits = [
            self._randomness.random_bit() for _ in range(self._num_qubits)
        ]
        self._alice_bases = [
            self._randomness.random_basis() for _ in range(self._num_qubits)
        ]
        self._bob_bits = [
            self._randomness.random_bit() for _ in range(self._num_qubits)
        ]
        self._bob_bases = [
            self._randomness.random_basis() for _ in range(self._num_qubits)
        ]

        # Prepare qubits
        self._alice_qubits = [
            self._measurement.prepare(bit, basis)
            for bit, basis in zip(self._alice_bits, self._alice_bases, strict=True)
        ]
        self._bob_qubits = [
            self._measurement.prepare(bit, basis)
            for bit, basis in zip(self._bob_bits, self._bob_bases, strict=True)
        ]

        self._phase = ProtocolPhase.TRANSMISSION
        self._step_index += 1
        return self._make_step_result(
            "Alice and Bob independently prepare qubits: each chooses "
            "random bits and encodes them in randomly selected bases "
            "(rectilinear or diagonal). Neither knows the other's choices.",
        )

    def _step_transmission(self) -> StepResult:
        """Alice and Bob both send qubits to Charlie through quantum channels."""
        self._transmitted_alice_qubits = []
        self._transmitted_bob_qubits = []

        for qubit in self._alice_qubits:
            transmitted = self._channel.transmit(qubit)
            self._transmitted_alice_qubits.append(transmitted)

        # Record Eve's interception of Alice's qubits
        if isinstance(self._channel, EavesdroppingChannel):
            self._eve_bases = self._channel.eve_bases[:]
            self._eve_results = self._channel.eve_results[:]

        for qubit in self._bob_qubits:
            transmitted = self._channel.transmit(qubit)
            self._transmitted_bob_qubits.append(transmitted)

        self._phase = ProtocolPhase.MEASUREMENT
        self._step_index += 1
        return self._make_step_result(
            "Alice and Bob both send their qubits to Charlie (the "
            "untrusted relay) through quantum channels. If an "
            "eavesdropper is present, they may intercept qubits "
            "from either channel.",
        )

    def _step_measurement(self) -> StepResult:
        """Charlie performs Bell State Measurement on each pair."""
        self._bsm_success = []
        self._bsm_results = []

        for alice_q, bob_q in zip(
            self._transmitted_alice_qubits,
            self._transmitted_bob_qubits,
            strict=True,
        ):
            success, bell_state = self._perform_bsm(alice_q, bob_q)
            self._bsm_success.append(success)
            self._bsm_results.append(bell_state)

        n_success = sum(self._bsm_success)
        bsm_rate = n_success / self._num_qubits if self._num_qubits > 0 else 0.0

        self._phase = ProtocolPhase.SIFTING
        self._step_index += 1
        return self._make_step_result(
            f"Charlie performs Bell State Measurement on each pair "
            f"(one qubit from Alice, one from Bob). {n_success} of "
            f"{self._num_qubits} BSMs succeeded ({bsm_rate:.0%}). "
            f"Charlie announces which pairs succeeded and which "
            f"Bell state was detected.",
        )

    def _step_sifting(self) -> StepResult:
        """Alice and Bob compare bases; keep matching bases with successful BSM."""
        self._matching_bases = [
            a == b for a, b in zip(self._alice_bases, self._bob_bases, strict=True)
        ]

        self._sifted_key_alice = []
        self._sifted_key_bob = []
        self._bob_results = []  # Populate for step result compatibility

        for i in range(self._num_qubits):
            if self._matching_bases[i] and self._bsm_success[i]:
                alice_bit = self._alice_bits[i]
                bob_bit = self._bob_bits[i]

                # Bob flips his bit based on Bell state:
                # For |Ψ-⟩: Alice's bit and Bob's bit should be anti-correlated
                #   so Bob flips his bit to match Alice
                # For |Ψ+⟩: same anti-correlation with a phase difference
                #   Bob also flips his bit
                # In both cases, the BSM projects onto an anti-correlated state,
                # so Bob flips to get correlation with Alice.
                flipped_bob_bit = (
                    BitValue.ONE if bob_bit == BitValue.ZERO else BitValue.ZERO
                )

                self._sifted_key_alice.append(alice_bit)
                self._sifted_key_bob.append(flipped_bob_bit)

        # For UI compatibility, bob_results shows the flipped sifted key bits
        self._bob_results = list(self._sifted_key_bob)

        self._phase = ProtocolPhase.ERROR_ESTIMATION
        self._step_index += 1
        n_sifted = len(self._sifted_key_alice)
        rate = self._sift_rate()
        return self._make_step_result(
            f"Alice and Bob compare bases over a classical channel. "
            f"They keep {n_sifted} of {self._num_qubits} bits where "
            f"bases matched AND Charlie's BSM succeeded ({rate:.0%} "
            f"sift rate). Bob flips his bits based on the announced "
            f"Bell state to correlate with Alice.",
        )

    def _step_error_estimation(self) -> StepResult:
        """Estimate error rate from the sifted key."""
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
                f"Error rate is {rate} \u2014 above the "
                f"{thresh} threshold! Eavesdropping "
                f"detected. Key is discarded."
            )
        else:
            desc = (
                f"Error rate is {rate} \u2014 below the "
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

    def _perform_bsm(
        self, alice_qubit: Qubit, bob_qubit: Qubit
    ) -> tuple[bool, BellState | None]:
        """Simulate Charlie's Bell State Measurement.

        With linear optics, only |Psi-⟩ and |Psi+⟩ can be distinguished,
        giving ~50% BSM success rate.

        The BSM outcome depends on the actual qubit states:
        - When both qubits are in the same basis, the BSM result reveals
          the XOR of the two bit values.
        - When qubits are in different bases, the BSM result is random
          (but this case is filtered out during sifting anyway).

        For |Psi-⟩: alice_bit XOR bob_bit = 1 (anti-correlated)
        For |Psi+⟩: alice_bit XOR bob_bit = 1 (also anti-correlated
          in rectilinear basis, with a relative phase in diagonal)
        """
        # Linear optics can only distinguish 2 of 4 Bell states -> 50% success
        success = random.random() < 0.5  # noqa: S311
        if not success:
            return False, None

        # Determine the Bell state based on actual qubit values.
        # When both are in the same basis:
        #   - Different bit values -> |Psi-⟩ or |Psi+⟩ (anti-correlated)
        #   - Same bit values -> |Phi+⟩ or |Phi-⟩ (correlated)
        # With linear optics, |Phi+⟩ and |Phi-⟩ are indistinguishable,
        # so same-value pairs that "succeed" would be misidentified.
        # In practice, linear optics BSM only fires for anti-correlated
        # inputs in the same basis. For different bases, the result
        # is effectively random.
        if alice_qubit.basis == bob_qubit.basis:
            if alice_qubit.value != bob_qubit.value:
                # Anti-correlated: valid BSM detection
                bell_state = random.choice(  # noqa: S311
                    [BellState.PSI_MINUS, BellState.PSI_PLUS]
                )
                return True, bell_state
            else:
                # Same values -> |Phi+⟩ or |Phi-⟩, not distinguishable
                # by linear optics BSM. This "success" is actually a
                # false positive that would produce errors. For a correct
                # simulation, these should not succeed.
                return False, None
        else:
            # Different bases: BSM result is random. In a real implementation,
            # these are filtered out during sifting anyway, but the BSM
            # may still fire. We let it succeed randomly.
            bell_state = random.choice(  # noqa: S311
                [BellState.PSI_MINUS, BellState.PSI_PLUS]
            )
            return True, bell_state

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
    def bsm_success(self) -> list[bool]:
        """Return the BSM success flags for each pair."""
        return list(self._bsm_success)

    @property
    def bsm_results(self) -> list[BellState | None]:
        """Return the BSM results for each pair."""
        return list(self._bsm_results)
