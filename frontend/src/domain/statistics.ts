/**
 * Statistics computation for QKD simulations.
 * Framework-agnostic — no React imports.
 */

export interface SimulationMetrics {
  readonly totalQubits: number;
  readonly siftedKeyLength: number;
  readonly sharedKeyLength: number;
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
}): SimulationMetrics {
  const total = step.alice_bits.length;
  const sifted = step.sifted_key_alice.length;
  const shared = step.shared_key.length;
  return {
    totalQubits: total,
    siftedKeyLength: sifted,
    sharedKeyLength: shared,
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
};
