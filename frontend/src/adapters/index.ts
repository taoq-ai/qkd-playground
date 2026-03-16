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
  is_complete: boolean;
}

export interface SimulationState {
  simulation_id: string;
  protocol: string;
  num_qubits: number;
  eavesdropper: boolean;
  current_step: StepResponse | null;
  steps: StepResponse[];
  is_complete: boolean;
}

const BASE_URL = "/api";

export async function createSimulation(
  protocol: string,
  numQubits: number,
  eavesdropper: boolean,
): Promise<string> {
  const resp = await fetch(`${BASE_URL}/simulation/create`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      protocol,
      num_qubits: numQubits,
      eavesdropper,
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
