/**
 * Statistics computation for QKD simulations.
 * Framework-agnostic — no React imports.
 */

export interface SimulationMetrics {
  readonly totalQubits: number;
  readonly siftedKeyLength: number;
  readonly sharedKeyLength: number;
  readonly amplifiedKeyLength: number;
  readonly errorRate: number;
  readonly siftRate: number;
  readonly keyEfficiency: number;
  readonly eavesdropperDetected: boolean;
}

export function computeMetrics(step: {
  alice_bits: number[];
  sifted_key_alice: number[];
  shared_key: number[];
  error_rate: number | null;
  eavesdropper_detected: boolean | null;
  amplified_key?: number[];
}): SimulationMetrics {
  const total = step.alice_bits.length;
  const sifted = step.sifted_key_alice.length;
  const shared = step.shared_key.length;
  const amplified = step.amplified_key?.length ?? 0;
  return {
    totalQubits: total,
    siftedKeyLength: sifted,
    sharedKeyLength: shared,
    amplifiedKeyLength: amplified,
    errorRate: step.error_rate ?? 0,
    siftRate: total > 0 ? sifted / total : 0,
    keyEfficiency: total > 0 ? shared / total : 0,
    eavesdropperDetected: step.eavesdropper_detected ?? false,
  };
}

export const EAVESDROP_THRESHOLDS: Record<string, number> = {
  bb84: 0.11,
  b92: 0.15,
  e91: 0.11,
  sarg04: 0.11,
  decoy_bb84: 0.11,
  mdi_qkd: 0.11,
};

/**
 * Tracks metrics across multiple simulation runs.
 */
export interface RunHistory {
  readonly runNumber: number;
  readonly qber: number;
  readonly siftRate: number;
  readonly keyLength: number;
  readonly protocol: string;
  readonly eavesdropper: boolean;
}

/**
 * Binary entropy function: H(p) = -p*log2(p) - (1-p)*log2(1-p).
 * Returns 0 for p=0 or p=1, and 1 for p=0.5.
 */
export function calculateBinaryEntropy(p: number): number {
  if (p <= 0 || p >= 1) return 0;
  return -(p * Math.log2(p) + (1 - p) * Math.log2(1 - p));
}

/**
 * Estimate Eve's information gain using a simplified bound.
 * If error rate e > 0, Eve's information ~ 1 - H(e).
 * Returns a value between 0 and 1 representing fraction of key information.
 */
export function estimateEveInformation(errorRate: number): number {
  if (errorRate <= 0) return 0;
  if (errorRate >= 0.5) return 1;
  return Math.max(0, 1 - calculateBinaryEntropy(errorRate));
}
