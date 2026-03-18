import { useState, useMemo, useCallback } from "react";
import type { StepResponse } from "../../adapters";
import { BlochSphere } from "./BlochSphere";

type QubitState = "|0\u27E9" | "|1\u27E9" | "|+\u27E9" | "|-\u27E9";
type ViewMode = "preparation" | "measurement";

interface StateInfo {
  vector: readonly [number, number, number];
  basis: "Z" | "X";
  label: string;
  description: string;
}

const STATE_MAP: Record<QubitState, StateInfo> = {
  "|0\u27E9": {
    vector: [0, 0, 1],
    basis: "Z",
    label: "|0\u27E9",
    description:
      "North pole of the Bloch sphere. This is the ground state in the Z (rectilinear) " +
      "basis, representing a classical bit value of 0.",
  },
  "|1\u27E9": {
    vector: [0, 0, -1],
    basis: "Z",
    label: "|1\u27E9",
    description:
      "South pole of the Bloch sphere. This is the excited state in the Z (rectilinear) " +
      "basis, representing a classical bit value of 1.",
  },
  "|+\u27E9": {
    vector: [1, 0, 0],
    basis: "X",
    label: "|+\u27E9",
    description:
      "Positive X axis of the Bloch sphere. This is the +1 eigenstate of the X " +
      "(diagonal) basis, an equal superposition of |0\u27E9 and |1\u27E9.",
  },
  "|-\u27E9": {
    vector: [-1, 0, 0],
    basis: "X",
    label: "|-\u27E9",
    description:
      "Negative X axis of the Bloch sphere. This is the -1 eigenstate of the X " +
      "(diagonal) basis, an equal superposition of |0\u27E9 and |1\u27E9 with a relative phase.",
  },
};

const QUBIT_STATES: QubitState[] = ["|0\u27E9", "|1\u27E9", "|+\u27E9", "|-\u27E9"];

function getPreparationState(bit: number, basis: string): QubitState {
  if (basis === "+" || basis === "Z" || basis === "rectilinear") {
    return bit === 0 ? "|0\u27E9" : "|1\u27E9";
  }
  return bit === 0 ? "|+\u27E9" : "|-\u27E9";
}

function getMeasurementState(result: number, basis: string): QubitState {
  if (basis === "+" || basis === "Z" || basis === "rectilinear") {
    return result === 0 ? "|0\u27E9" : "|1\u27E9";
  }
  return result === 0 ? "|+\u27E9" : "|-\u27E9";
}

export interface BlochSpherePanelProps {
  readonly currentStep: StepResponse | null;
}

export function BlochSpherePanel({ currentStep }: BlochSpherePanelProps) {
  const [viewMode, setViewMode] = useState<ViewMode>("preparation");
  const [qubitIndex, setQubitIndex] = useState(0);
  const [manualState, setManualState] = useState<QubitState | null>(null);

  const numQubits = currentStep?.alice_bits?.length ?? 0;
  const hasSimulation = currentStep !== null && numQubits > 0;

  const clampedIndex = hasSimulation ? Math.min(qubitIndex, numQubits - 1) : 0;

  const simulationState = useMemo<QubitState | null>(() => {
    if (!hasSimulation || !currentStep) return null;
    const idx = clampedIndex;

    if (viewMode === "preparation") {
      const bit = currentStep.alice_bits[idx];
      const basis = currentStep.alice_bases[idx];
      if (bit === undefined || basis === undefined) return null;
      return getPreparationState(bit, basis);
    } else {
      const result = currentStep.bob_results[idx];
      const basis = currentStep.bob_bases[idx];
      if (result === undefined || basis === undefined) return null;
      return getMeasurementState(result, basis);
    }
  }, [hasSimulation, currentStep, clampedIndex, viewMode]);

  const activeState = manualState ?? simulationState ?? "|0\u27E9";
  const stateInfo = STATE_MAP[activeState];

  const handleQubitIndexChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const val = Math.max(0, Math.min(numQubits - 1, Number(e.target.value)));
      setQubitIndex(val);
      setManualState(null);
    },
    [numQubits],
  );

  const handleStateSelect = useCallback((state: QubitState) => {
    setManualState(state);
  }, []);

  const handleViewModeChange = useCallback((mode: ViewMode) => {
    setViewMode(mode);
    setManualState(null);
  }, []);

  return (
    <div className="bloch-panel">
      <h2>Bloch Sphere Visualization</h2>
      <p className="bloch-description">
        The Bloch sphere represents a single qubit state as a point on the surface of a unit sphere.
        The poles correspond to computational basis states, and the equator holds superposition
        states.
      </p>

      <div className="bloch-layout">
        <div className="bloch-sphere-wrapper">
          <BlochSphere stateVector={stateInfo.vector} basis={stateInfo.basis} />
        </div>

        <div className="bloch-controls">
          {/* State selector */}
          <div className="bloch-control-group">
            <label className="bloch-control-label">Select State</label>
            <div className="bloch-state-buttons">
              {QUBIT_STATES.map((s) => (
                <button
                  key={s}
                  className={`btn bloch-state-btn ${activeState === s ? "bloch-state-btn-active" : ""}`}
                  onClick={() => handleStateSelect(s)}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>

          {/* View mode toggle */}
          {hasSimulation && (
            <>
              <div className="bloch-control-group">
                <label className="bloch-control-label">View Mode</label>
                <div className="bloch-view-toggle">
                  <button
                    className={`btn bloch-toggle-btn ${viewMode === "preparation" ? "bloch-toggle-active" : ""}`}
                    onClick={() => handleViewModeChange("preparation")}
                  >
                    Preparation
                  </button>
                  <button
                    className={`btn bloch-toggle-btn ${viewMode === "measurement" ? "bloch-toggle-active" : ""}`}
                    onClick={() => handleViewModeChange("measurement")}
                  >
                    Measurement
                  </button>
                </div>
              </div>

              <div className="bloch-control-group">
                <label className="bloch-control-label">
                  Qubit Index: <strong>{clampedIndex}</strong> / {numQubits - 1}
                </label>
                <input
                  type="range"
                  min={0}
                  max={Math.max(0, numQubits - 1)}
                  value={clampedIndex}
                  onChange={handleQubitIndexChange}
                  className="bloch-qubit-slider"
                />
              </div>
            </>
          )}

          {/* Annotation */}
          <div className="bloch-annotation">
            <div className="bloch-annotation-header">
              <span
                className="bloch-basis-indicator"
                style={{ background: stateInfo.basis === "Z" ? "#4fd1c5" : "#c084fc" }}
              />
              <strong>{stateInfo.label}</strong>
              <span className="bloch-basis-label">
                {stateInfo.basis === "Z" ? "Z-basis (rectilinear)" : "X-basis (diagonal)"}
              </span>
            </div>
            <p className="bloch-annotation-text">{stateInfo.description}</p>
            <div className="bloch-coords">
              <span>x={stateInfo.vector[0].toFixed(1)}</span>
              <span>y={stateInfo.vector[1].toFixed(1)}</span>
              <span>z={stateInfo.vector[2].toFixed(1)}</span>
            </div>
          </div>

          {!hasSimulation && (
            <p className="bloch-no-sim">
              Start a simulation from the Simulator tab to visualize qubit states from your QKD
              session. You can also explore states manually using the buttons above.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
