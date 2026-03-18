/**
 * Quantum computing concept explanations for the QKD Playground.
 * Framework-agnostic — no React imports.
 */

export interface ConceptEntry {
  readonly id: string;
  readonly title: string;
  readonly summary: string;
  readonly detail: string;
  readonly relatedPhases: readonly string[];
  readonly protocols: readonly string[];
}

export const CONCEPTS: readonly ConceptEntry[] = [
  {
    id: "qubits",
    title: "What is a Qubit?",
    summary:
      "A qubit is the quantum version of a classical bit. While a classical " +
      "bit is always 0 or 1, a qubit can exist in a superposition of both " +
      "states simultaneously.",
    detail:
      "In QKD, Alice encodes her secret key bits into qubits. The quantum " +
      "properties of qubits \u2014 superposition and the inability to be " +
      "copied \u2014 are what make the key exchange secure. When a qubit is " +
      "measured, it collapses to either 0 or 1, destroying any superposition.",
    relatedPhases: ["preparation"],
    protocols: ["all"],
  },
  {
    id: "superposition",
    title: "Superposition & Bases",
    summary:
      "A qubit can be measured in different bases. In the rectilinear (+) " +
      "basis, states are |0\u27E9 and |1\u27E9. In the diagonal (\u00d7) " +
      "basis, states are |+\u27E9 and |\u2212\u27E9.",
    detail:
      "When Alice prepares a qubit in one basis and Bob measures in a " +
      "different basis, the result is completely random (50/50). This is " +
      "why basis matching is essential for key agreement \u2014 only " +
      "measurements in the same basis produce correlated results.",
    relatedPhases: ["preparation", "measurement"],
    protocols: ["all"],
  },
  {
    id: "channel-noise",
    title: "Channel Noise & Photon Loss",
    summary:
      "Real quantum channels (like fiber optic cables) introduce errors " +
      "through depolarization and photon loss, degrading the transmitted " +
      "qubit states even without an eavesdropper.",
    detail:
      "Depolarizing noise randomly scrambles qubit states with some " +
      "probability, replacing the intended state with a random one. " +
      "Photon loss occurs when photons are absorbed or scattered in " +
      "the fiber, resulting in missing detections that appear as random " +
      "noise. These imperfections make eavesdropper detection harder, " +
      "since some errors are expected even on a secure channel. QKD " +
      "protocols must distinguish natural channel noise from eavesdropping.",
    relatedPhases: ["transmission"],
    protocols: ["all"],
  },
  {
    id: "no-cloning",
    title: "The No-Cloning Theorem",
    summary:
      "Quantum mechanics forbids making a perfect copy of an unknown " +
      "quantum state. This is the foundation of QKD security.",
    detail:
      "An eavesdropper (Eve) cannot simply copy the qubits as they pass " +
      "through the channel. She must measure them, which disturbs their " +
      "state. This disturbance is detectable by Alice and Bob when they " +
      "compare their results, making eavesdropping fundamentally detectable.",
    relatedPhases: ["transmission"],
    protocols: ["all"],
  },
  {
    id: "measurement-collapse",
    title: "Measurement Collapse",
    summary:
      "Measuring a qubit irreversibly collapses its quantum state. If " +
      "measured in the wrong basis, the original information is lost.",
    detail:
      "When Bob measures a qubit, its superposition collapses to a " +
      "definite value. If his basis matches Alice\u2019s, he gets the " +
      "correct bit. If not, he gets a random result. This is why they " +
      "must publicly compare bases afterward and keep only the matching ones.",
    relatedPhases: ["measurement"],
    protocols: ["all"],
  },
  {
    id: "key-sifting",
    title: "Key Sifting",
    summary:
      "Alice and Bob publicly compare which bases they used (but not " +
      "their results). They keep only the bits where they chose the same basis.",
    detail:
      "In BB84, about 50% of bases match randomly, yielding a ~50% sift " +
      "rate. In B92, only conclusive measurements are kept (~25% sift " +
      "rate). The sifted key forms the raw shared secret before error checking.",
    relatedPhases: ["sifting"],
    protocols: ["all"],
  },
  {
    id: "eavesdropping-detection",
    title: "Detecting Eavesdropping",
    summary:
      "Alice and Bob sacrifice a portion of their sifted key to estimate " +
      "the error rate. A high error rate reveals an eavesdropper.",
    detail:
      "Eve\u2019s intercept-resend attack introduces ~25% errors on " +
      "average. If the error rate exceeds a protocol-specific threshold " +
      "(11% for BB84, 15% for B92), Alice and Bob discard the key and " +
      "know the channel was compromised.",
    relatedPhases: ["error_estimation"],
    protocols: ["bb84", "b92"],
  },
  {
    id: "entanglement",
    title: "Quantum Entanglement",
    summary:
      "Two entangled qubits share a special correlation: measuring one " +
      "instantly determines the other, regardless of distance.",
    detail:
      "In E91, Alice and Bob share Bell pairs |\u03A6+\u27E9 = (|00\u27E9 " +
      "+ |11\u27E9)/\u221A2. When both measure in the same basis, they " +
      "always get the same result. This perfect correlation is the basis " +
      "for their shared key. An eavesdropper breaks the entanglement, " +
      "destroying these correlations.",
    relatedPhases: ["preparation", "transmission"],
    protocols: ["e91"],
  },
  {
    id: "bell-inequality",
    title: "Bell Inequality & CHSH Test",
    summary:
      "The CHSH test measures quantum correlations between entangled " +
      "particles. A value of S > 2 proves genuine quantum entanglement.",
    detail:
      "Non-matching basis measurements are used to compute the CHSH " +
      "correlation coefficient S. For perfectly entangled pairs, S can " +
      "reach 2\u221A2 \u2248 2.83, violating the classical limit of 2. " +
      "If Eve intercepts the qubits, entanglement is broken and S drops " +
      "toward the classical bound, revealing her presence.",
    relatedPhases: ["error_estimation"],
    protocols: ["e91"],
  },
  {
    id: "shared-key",
    title: "The Shared Secret Key",
    summary:
      "After sifting and error checking, Alice and Bob share an " +
      "identical random bit string that can be used for encryption.",
    detail:
      "The final shared key is provably secure: any eavesdropping " +
      "attempt would have been detected by the error rate check. " +
      "This key can then be used with a one-time pad or other symmetric " +
      "cipher for perfectly secure communication.",
    relatedPhases: ["complete"],
    protocols: ["all"],
  },
];

/**
 * Get concepts relevant to a specific phase and protocol.
 */
export function getConceptsForPhase(phase: string, protocol: string): ConceptEntry[] {
  return CONCEPTS.filter(
    (c) =>
      c.relatedPhases.includes(phase) &&
      (c.protocols.includes("all") || c.protocols.includes(protocol)),
  );
}
