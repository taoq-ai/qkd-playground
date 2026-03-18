/**
 * API client adapter — connects to the FastAPI backend.
 */

export interface StepResponse {
  phase: string;
  step_index: number;
  description: string;
  alice_bits: number[];
  alice_bases: string[];
  bob_bases: string[];
  bob_results: number[];
  matching_bases: boolean[];
  sifted_key_alice: number[];
  sifted_key_bob: number[];
  error_rate: number | null;
  eavesdropper_detected: boolean | null;
  shared_key: number[];
  conclusive_mask: boolean[];
  chsh_value: number | null;
  eve_intercepted: boolean;
  eve_bases: string[];
  eve_results: number[];
  reconciled_key_alice: number[];
  reconciled_key_bob: number[];
  reconciliation_corrections: number;
  amplified_key: number[];
  privacy_amplification_ratio: number;
  is_complete: boolean;
}

export interface SimulationState {
  simulation_id: string;
  protocol: string;
  num_qubits: number;
  eavesdropper: boolean;
  noise_level: number;
  loss_rate: number;
  current_step: StepResponse | null;
  steps: StepResponse[];
  is_complete: boolean;
}

const BASE_URL = import.meta.env.DEV ? "/api" : "";

export async function createSimulation(
  protocol: string,
  numQubits: number,
  eavesdropper: boolean,
  noiseLevel: number = 0,
  lossRate: number = 0,
): Promise<string> {
  const resp = await fetch(`${BASE_URL}/simulation/create`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      protocol,
      num_qubits: numQubits,
      eavesdropper,
      noise_level: noiseLevel,
      loss_rate: lossRate,
    }),
  });
  const data = (await resp.json()) as { simulation_id: string };
  return data.simulation_id;
}

export async function stepSimulation(simulationId: string): Promise<StepResponse> {
  const resp = await fetch(`${BASE_URL}/simulation/${simulationId}/step`, {
    method: "POST",
  });
  return (await resp.json()) as StepResponse;
}

export async function getSimulationState(simulationId: string): Promise<SimulationState> {
  const resp = await fetch(`${BASE_URL}/simulation/${simulationId}/state`);
  return (await resp.json()) as SimulationState;
}

export async function resetSimulation(simulationId: string): Promise<void> {
  await fetch(`${BASE_URL}/simulation/${simulationId}/reset`, {
    method: "POST",
  });
}

export async function runSimulation(simulationId: string): Promise<StepResponse[]> {
  const resp = await fetch(`${BASE_URL}/simulation/${simulationId}/run`, {
    method: "POST",
  });
  const data = (await resp.json()) as { steps: StepResponse[] };
  return data.steps;
}

export interface RatePoint {
  distance: number;
  rate: number;
}

export interface PerformanceData {
  protocols: Record<string, RatePoint[]>;
  params: {
    max_distance: number;
    detector_efficiency: number;
    dark_count_rate: number;
  };
}

export async function getPerformanceData(
  protocols: string[],
  maxDistance: number,
  detectorEfficiency: number,
  darkCountRate: number,
): Promise<PerformanceData> {
  const params = new URLSearchParams({
    protocols: protocols.join(","),
    max_distance: maxDistance.toString(),
    detector_efficiency: detectorEfficiency.toString(),
    dark_count_rate: darkCountRate.toString(),
  });
  const resp = await fetch(`${BASE_URL}/performance?${params.toString()}`);
  return (await resp.json()) as PerformanceData;
}

export interface BellTestCorrelation {
  alice_angle: number;
  bob_angle: number;
  correlation: number;
  counts: Record<string, number>;
}

export interface BellTestResponse {
  correlations: BellTestCorrelation[];
  s_value: number;
  num_trials: number;
}

export async function runBellTest(
  aliceAngles: [number, number],
  bobAngles: [number, number],
  numTrials: number = 1000,
): Promise<BellTestResponse> {
  const resp = await fetch(`${BASE_URL}/bell-test`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      alice_angles: aliceAngles,
      bob_angles: bobAngles,
      num_trials: numTrials,
    }),
  });
  return (await resp.json()) as BellTestResponse;
}
