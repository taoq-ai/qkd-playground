"""BB84 Quantum Key Distribution protocol implementation.

The BB84 protocol was proposed by Bennett and Brassard in 1984. It uses the
quantum properties of single qubits to establish a shared secret key between
two parties (Alice and Bob). Security relies on the no-cloning theorem —
any eavesdropper measuring qubits disturbs them detectably.

Protocol steps:
1. Preparation: Alice chooses random bits and random bases, prepares qubits.
2. Transmission: Qubits sent through quantum channel to Bob.
3. Measurement: Bob chooses random bases and measures each qubit.
4. Sifting: Alice and Bob compare bases (classical channel), keep matching.
5. Error estimation: Sample subset of sifted key to estimate error rate.
6. Complete: If error rate < threshold, remaining bits form the shared key.
"""

from __future__ import annotations

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


class BB84Protocol(ProtocolPort):
    """BB84 QKD protocol with step-by-step execution."""

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
        self._matching_bases: list[bool] = []
        self._sifted_key_alice: list[BitValue] = []
        self._sifted_key_bob: list[BitValue] = []
        self._error_rate: float = 0.0
        self._eavesdropper_detected: bool = False
        self._shared_key: list[BitValue] = []
        self._transmitted_qubits: list[Qubit] = []

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

    def is_complete(self) -> bool:
        """Return True if the protocol has finished all phases."""
        return self._phase == ProtocolPhase.COMPLETE

    def run(self, num_qubits: int) -> ProtocolResult:
        """Execute the full BB84 protocol."""
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
        return self._make_step_result(
            "Protocol is complete.",
        )

    def _step_preparation(self) -> StepResult:
        """Alice chooses random bits and bases, prepares qubits."""
        self._alice_bits = [
            self._randomness.random_bit() for _ in range(self._num_qubits)
        ]
        self._alice_bases = [
            self._randomness.random_basis() for _ in range(self._num_qubits)
        ]
        self._phase = ProtocolPhase.TRANSMISSION
        self._step_index += 1
        return self._make_step_result(
            "Alice prepares qubits: chooses random bits and "
            "encodes each in a randomly selected basis "
            "(rectilinear or diagonal).",
        )

    def _step_transmission(self) -> StepResult:
        """Qubits are transmitted through the quantum channel."""
        self._transmitted_qubits = []
        for bit, basis in zip(self._alice_bits, self._alice_bases, strict=True):
            qubit = self._measurement.prepare(bit, basis)
            transmitted = self._channel.transmit(qubit)
            self._transmitted_qubits.append(transmitted)

        self._phase = ProtocolPhase.MEASUREMENT
        self._step_index += 1
        return self._make_step_result(
            "Alice sends qubits to Bob through the quantum "
            "channel. If an eavesdropper is present, they may "
            "intercept and disturb the qubits.",
        )

    def _step_measurement(self) -> StepResult:
        """Bob measures each qubit in a randomly chosen basis."""
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
            "Bob measures each received qubit in a randomly "
            "chosen basis. When his basis matches Alice's, "
            "he gets the correct bit value.",
        )

    def _step_sifting(self) -> StepResult:
        """Alice and Bob compare bases and keep matching."""
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
        n_sifted = len(self._sifted_key_alice)
        rate = self._sift_rate()
        return self._make_step_result(
            f"Alice and Bob compare bases over a classical "
            f"channel. They keep {n_sifted} of "
            f"{self._num_qubits} bits where bases matched "
            f"({rate:.0%} sift rate).",
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

        self._phase = ProtocolPhase.COMPLETE
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
        )
