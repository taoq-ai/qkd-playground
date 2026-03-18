/**
 * Domain types and interfaces for the QKD Playground.
 * These types are framework-agnostic and represent core QKD concepts.
 */

export enum Basis {
  Rectilinear = "rectilinear",
  Diagonal = "diagonal",
}

export enum BitValue {
  Zero = 0,
  One = 1,
}

export interface Qubit {
  readonly basis: Basis;
  readonly value: BitValue;
}

export interface Measurement {
  readonly basis: Basis;
  readonly outcome: BitValue;
  readonly qubit: Qubit;
}

export interface ProtocolResult {
  readonly sharedKey: BitValue[];
  readonly errorRate: number;
  readonly rawKeyLength: number;
  readonly siftedKeyLength: number;
  readonly eavesdropperDetected: boolean;
}

export enum ProtocolType {
  BB84 = "bb84",
  E91 = "e91",
  B92 = "b92",
  SARG04 = "sarg04",
}

export { type ConceptEntry, CONCEPTS, getConceptsForPhase } from "./concepts";
export { type SimulationMetrics, computeMetrics, EAVESDROP_THRESHOLDS } from "./statistics";

/** Port interface for the simulation API client. */
export interface SimulationPort {
  listProtocols(): Promise<{ name: string; label: string }[]>;
  createSimulation(protocol: ProtocolType, numQubits: number): Promise<string>;
  step(simulationId: string): Promise<Record<string, unknown>>;
  getState(simulationId: string): Promise<Record<string, unknown>>;
  reset(simulationId: string): Promise<void>;
}
