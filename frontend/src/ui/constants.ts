export const PHASE_LABELS: Record<string, string> = {
  preparation: "Preparation",
  transmission: "Transmission",
  measurement: "Measurement",
  sifting: "Sifting",
  error_estimation: "Error Estimation",
  complete: "Complete",
};

export const PHASE_ORDER = [
  "preparation",
  "transmission",
  "measurement",
  "sifting",
  "error_estimation",
  "complete",
];

export const PROTOCOL_INFO: Record<string, { name: string; description: string }> = {
  bb84: {
    name: "BB84",
    description:
      "The original QKD protocol by Bennett & Brassard (1984). Alice sends " +
      "qubits encoded in two random bases; Bob measures in two random bases. " +
      "They keep bits where bases match (~50% sift rate).",
  },
  b92: {
    name: "B92",
    description:
      "A simplified protocol by Bennett (1992) using only two non-orthogonal " +
      "states: |0\u27E9 for bit 0 and |+\u27E9 for bit 1. Bob's conclusive measurements " +
      "(outcome = 1) reveal Alice's bit (~25% sift rate).",
  },
  e91: {
    name: "E91",
    description:
      "Ekert's entanglement-based protocol (1991). Alice and Bob share Bell " +
      "pairs and measure in random bases. Security is verified via CHSH " +
      "inequality violation.",
  },
};
