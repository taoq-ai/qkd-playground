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
      "(11% for BB84 and SARG04, 15% for B92), Alice and Bob discard " +
      "the key and know the channel was compromised.",
    relatedPhases: ["error_estimation"],
    protocols: ["bb84", "b92", "sarg04"],
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
      "particles. A value of S > 2 proves genuine quantum entanglement " +
      "and rules out local hidden variable theories.",
    detail:
      "The CHSH inequality uses four measurement settings: Alice chooses " +
      "between angles a and a', Bob between b and b'. The parameter " +
      "S = E(a,b) - E(a,b') + E(a',b) + E(a',b') is bounded by 2 for " +
      "any classical (local hidden variable) model. Quantum mechanics " +
      "allows S up to 2\u221A2 \u2248 2.83. The optimal angles for " +
      "maximal violation are a=0\u00B0, a'=45\u00B0, b=22.5\u00B0, b'=67.5\u00B0.",
    relatedPhases: ["error_estimation"],
    protocols: ["e91"],
  },
  {
    id: "tsirelson-bound",
    title: "Tsirelson's Bound",
    summary:
      "Tsirelson's bound is the maximum value of the CHSH parameter " +
      "allowed by quantum mechanics: S \u2264 2\u221A2 \u2248 2.828.",
    detail:
      "While classical physics limits CHSH correlations to S \u2264 2, " +
      "quantum mechanics allows up to S = 2\u221A2. This upper limit, " +
      "proved by Boris Tsirelson in 1980, cannot be exceeded even with " +
      "entanglement. It sits between the classical bound (2) and the " +
      "algebraic maximum (4), showing that quantum correlations are " +
      "stronger than classical but not as strong as mathematically possible.",
    relatedPhases: ["error_estimation"],
    protocols: ["e91"],
  },
  {
    id: "pns-resistance",
    title: "PNS Attack Resistance",
    summary:
      "SARG04 is designed to resist photon number splitting (PNS) attacks " +
      "where an eavesdropper exploits multi-photon pulses in practical " +
      "implementations.",
    detail:
      "In real-world QKD, laser sources sometimes emit more than one " +
      "photon per pulse. An attacker can split off extra photons and " +
      "measure them without disturbing the signal. SARG04 counters this " +
      "by announcing non-orthogonal state pairs instead of bases during " +
      "sifting. This makes it harder for Eve to exploit multi-photon " +
      "pulses, at the cost of a lower sift rate (~25% vs BB84\u2019s ~50%).",
    relatedPhases: ["sifting"],
    protocols: ["sarg04"],
  },
  {
    id: "information-reconciliation",
    title: "Information Reconciliation",
    summary:
      "After sifting, Alice and Bob's keys may still contain a few errors. " +
      "Information reconciliation uses error-correction techniques to fix " +
      "these discrepancies without revealing the key.",
    detail:
      "A Cascade-inspired protocol divides the key into blocks and compares " +
      "parities over the classical channel. When a parity mismatch is found, " +
      "a binary search within the block locates and corrects the error bit. " +
      "This reveals some information (the parities), which must be accounted " +
      "for in the subsequent privacy amplification step.",
    relatedPhases: ["reconciliation"],
    protocols: ["all"],
  },
  {
    id: "privacy-amplification",
    title: "Privacy Amplification",
    summary:
      "Privacy amplification compresses the reconciled key to eliminate any " +
      "information an eavesdropper may have gained during transmission or " +
      "error correction.",
    detail:
      "Using universal hashing (based on the Shannon entropy bound), the " +
      "key is shortened to a length where Eve's information is negligible. " +
      "The compression ratio depends on the error rate: higher errors mean " +
      "more bits must be sacrificed. The result is a shorter but provably " +
      "secure final key.",
    relatedPhases: ["privacy_amplification"],
    protocols: ["all"],
  },
  {
    id: "weak-coherent-pulses",
    title: "Weak Coherent Pulses",
    summary:
      "Real laser sources emit coherent light pulses whose photon number follows " +
      "a Poisson distribution. Most pulses contain zero or one photon, but some " +
      "contain multiple photons, creating a security vulnerability.",
    detail:
      "An ideal QKD source would emit exactly one photon per pulse, but real lasers " +
      "produce weak coherent states with mean photon number \u03bc. The probability " +
      "of an n-photon pulse follows Poisson statistics. Multi-photon pulses " +
      "allow an eavesdropper to split off extra photons (PNS attack) without disturbing " +
      "the signal. The decoy-state technique overcomes this by using multiple intensities " +
      "to monitor the channel's response to different photon-number distributions.",
    relatedPhases: ["preparation", "transmission"],
    protocols: ["decoy_bb84"],
  },
  {
    id: "decoy-states",
    title: "Decoy States",
    summary:
      "Decoy-state QKD uses pulses at multiple intensity levels (signal, decoy, vacuum) " +
      "to estimate single-photon transmission statistics and detect photon number " +
      "splitting attacks.",
    detail:
      "Alice randomly chooses between signal (\u03bc\u22480.5), decoy (\u03bd\u22480.1), " +
      "and vacuum (\u03c9\u22480) intensity levels for each pulse. After transmission, she " +
      "announces which intensity was used. By comparing detection rates across intensity " +
      "classes, Alice and Bob can tightly bound the single-photon yield and QBER. A PNS " +
      "attacker would affect multi-photon pulses differently from single-photon pulses, " +
      "creating detectable differences between signal and decoy statistics. The GLLP " +
      "formula then uses these bounds to compute a secure key rate.",
    relatedPhases: ["preparation", "sifting", "error_estimation"],
    protocols: ["decoy_bb84"],
  },
  {
    id: "protocol-comparison",
    title: "Protocol Comparison",
    summary:
      "Different QKD protocols make different trade-offs between sift rate, " +
      "security assumptions, and implementation complexity. Comparing them " +
      "side-by-side highlights these differences.",
    detail:
      "BB84 offers ~50% sift rate with well-understood security proofs. B92 " +
      "uses only two states for simpler implementation but has a lower ~25% " +
      "sift rate. E91 leverages entanglement, providing security guaranteed " +
      "by Bell inequality violations, at the cost of requiring entangled " +
      "photon sources. SARG04 trades sift rate (~25%) for resistance to " +
      "photon-number-splitting attacks in practical multi-photon sources. " +
      "Running protocols under identical conditions reveals how these " +
      "trade-offs affect QBER, key efficiency, and final key length.",
    relatedPhases: ["complete"],
    protocols: ["all"],
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
  {
    id: "rate-distance-tradeoff",
    title: "Rate-Distance Trade-off",
    summary:
      "The secure key generation rate decreases exponentially with " +
      "channel distance due to photon loss in optical fibers.",
    detail:
      "Standard optical fiber attenuates signals at ~0.2 dB/km, meaning " +
      "roughly half the photons are lost every 15 km. As distance " +
      "increases, fewer photons reach the detector while dark counts " +
      "remain constant, degrading the signal-to-noise ratio until no " +
      "secure key can be extracted. This is why practical QKD links are " +
      "currently limited to a few hundred kilometres without quantum " +
      "repeaters.",
    relatedPhases: ["performance"],
    protocols: ["all"],
  },
  {
    id: "plob-bound",
    title: "PLOB Bound",
    summary:
      "The Pirandola-Laurenza-Ottaviani-Banchi (PLOB) bound is the " +
      "fundamental upper limit on key rate for any point-to-point QKD " +
      "protocol without quantum repeaters.",
    detail:
      "The PLOB bound equals -log2(1 - eta), where eta is the channel " +
      "transmittance. No QKD protocol can exceed this rate over a lossy " +
      "channel without quantum repeaters or other intermediate trusted " +
      "nodes. Overcoming this limit is one of the main motivations for " +
      "developing quantum repeater technology.",
    relatedPhases: ["performance"],
    protocols: ["all"],
  },
  {
    id: "bloch-sphere",
    title: "The Bloch Sphere",
    summary:
      "The Bloch sphere is a geometric representation of a single qubit state " +
      "as a point on the surface of a unit sphere. The north and south poles " +
      "represent |0\u27E9 and |1\u27E9, while equatorial points represent superpositions.",
    detail:
      "Any pure single-qubit state can be written as cos(\u03B8/2)|0\u27E9 + " +
      "e^{i\u03C6}sin(\u03B8/2)|1\u27E9, where \u03B8 is the polar angle from " +
      "the Z axis and \u03C6 is the azimuthal angle in the XY plane. The Z axis " +
      "corresponds to the computational (rectilinear) basis, the X axis to the " +
      "diagonal basis, and the Y axis to the circular basis. Measurement in a " +
      "given basis projects the state onto that axis, with probabilities " +
      "determined by the angle between the state vector and the measurement axis.",
    relatedPhases: ["preparation", "measurement"],
    protocols: ["all"],
  },
  {
    id: "measurement-bases-bloch",
    title: "Measurement Bases on the Bloch Sphere",
    summary:
      "Different measurement bases correspond to different axes of the Bloch " +
      "sphere. The Z-basis (rectilinear) uses the vertical axis, while the " +
      "X-basis (diagonal) uses the horizontal axis.",
    detail:
      "When measuring a qubit, the outcome probabilities depend on the angle " +
      "between the state vector and the measurement axis. Measuring a |+\u27E9 " +
      "state (on the X axis) in the Z-basis gives a 50/50 random result because " +
      "the state is equidistant from both poles. This geometric picture explains " +
      "why mismatched bases in QKD produce random results and why basis " +
      "reconciliation is essential for key agreement.",
    relatedPhases: ["preparation", "measurement"],
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
