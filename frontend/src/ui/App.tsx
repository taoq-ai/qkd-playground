import { useCallback, useState } from "react";
import type { StepResponse } from "../adapters";
import {
  createSimulation,
  resetSimulation,
  stepSimulation,
} from "../adapters";
import "./styles.css";

const PHASE_LABELS: Record<string, string> = {
  preparation: "Preparation",
  transmission: "Transmission",
  measurement: "Measurement",
  sifting: "Sifting",
  error_estimation: "Error Estimation",
  complete: "Complete",
};

const PHASE_ORDER = [
  "preparation",
  "transmission",
  "measurement",
  "sifting",
  "error_estimation",
  "complete",
];

function BasisBadge({ basis }: { basis: string }) {
  const isRect = basis === "rectilinear";
  return (
    <span
      className={`basis-badge ${isRect ? "basis-rect" : "basis-diag"}`}
      title={basis}
    >
      {isRect ? "+" : "×"}
    </span>
  );
}

function BitCell({ value, highlight }: { value: number; highlight?: boolean }) {
  return (
    <span className={`bit-cell ${highlight ? "bit-highlight" : ""}`}>
      {value}
    </span>
  );
}

function QubitTable({ step }: { step: StepResponse }) {
  const count = step.alice_bits.length;
  if (count === 0) return null;

  // Show max 20 qubits in the visual table
  const maxShow = Math.min(count, 20);
  const truncated = count > maxShow;

  return (
    <div className="qubit-table-wrapper">
      <div className="qubit-table">
        <div className="qubit-row">
          <span className="row-label">Alice&apos;s Bits</span>
          {step.alice_bits.slice(0, maxShow).map((b, i) => (
            <BitCell key={`ab-${i}`} value={b} />
          ))}
          {truncated && <span className="ellipsis">&hellip;</span>}
        </div>
        <div className="qubit-row">
          <span className="row-label">Alice&apos;s Bases</span>
          {step.alice_bases.slice(0, maxShow).map((b, i) => (
            <BasisBadge key={`abas-${i}`} basis={b} />
          ))}
          {truncated && <span className="ellipsis">&hellip;</span>}
        </div>
        {step.bob_bases.length > 0 && (
          <div className="qubit-row">
            <span className="row-label">Bob&apos;s Bases</span>
            {step.bob_bases.slice(0, maxShow).map((b, i) => (
              <BasisBadge key={`bbas-${i}`} basis={b} />
            ))}
            {truncated && <span className="ellipsis">&hellip;</span>}
          </div>
        )}
        {step.bob_results.length > 0 && (
          <div className="qubit-row">
            <span className="row-label">Bob&apos;s Results</span>
            {step.bob_results.slice(0, maxShow).map((b, i) => (
              <BitCell key={`br-${i}`} value={b} />
            ))}
            {truncated && <span className="ellipsis">&hellip;</span>}
          </div>
        )}
        {step.conclusive_mask.length > 0 && (
          <div className="qubit-row">
            <span className="row-label">Conclusive</span>
            {step.conclusive_mask.slice(0, maxShow).map((c, i) => (
              <span
                key={`c-${i}`}
                className={`match-cell ${c ? "match-yes" : "match-no"}`}
              >
                {c ? "✓" : "✗"}
              </span>
            ))}
            {truncated && <span className="ellipsis">&hellip;</span>}
          </div>
        )}
        {step.matching_bases.length > 0 && (
          <div className="qubit-row">
            <span className="row-label">Bases Match</span>
            {step.matching_bases.slice(0, maxShow).map((m, i) => (
              <span
                key={`m-${i}`}
                className={`match-cell ${m ? "match-yes" : "match-no"}`}
              >
                {m ? "✓" : "✗"}
              </span>
            ))}
            {truncated && <span className="ellipsis">&hellip;</span>}
          </div>
        )}
      </div>
    </div>
  );
}

function ProgressBar({ currentPhase }: { currentPhase: string }) {
  const currentIdx = PHASE_ORDER.indexOf(currentPhase);
  return (
    <div className="progress-bar">
      {PHASE_ORDER.map((phase, idx) => (
        <div
          key={phase}
          className={`progress-step ${idx < currentIdx ? "step-done" : ""} ${idx === currentIdx ? "step-active" : ""}`}
        >
          <div className="step-dot" />
          <span className="step-label">{PHASE_LABELS[phase]}</span>
        </div>
      ))}
    </div>
  );
}

function ResultsPanel({ step }: { step: StepResponse }) {
  if (step.error_rate === null) return null;
  const detected = step.eavesdropper_detected;
  return (
    <div className={`results-panel ${detected ? "results-danger" : "results-safe"}`}>
      <h3>Results</h3>
      <div className="results-grid">
        <div className="result-item">
          <span className="result-label">Error Rate</span>
          <span className="result-value">{(step.error_rate * 100).toFixed(1)}%</span>
        </div>
        <div className="result-item">
          <span className="result-label">Sifted Key Length</span>
          <span className="result-value">{step.sifted_key_alice.length}</span>
        </div>
        <div className="result-item">
          <span className="result-label">Shared Key Length</span>
          <span className="result-value">{step.shared_key.length}</span>
        </div>
        <div className="result-item">
          <span className="result-label">Eavesdropper</span>
          <span className={`result-value ${detected ? "text-danger" : "text-safe"}`}>
            {detected ? "⚠ Detected!" : "✓ Not detected"}
          </span>
        </div>
        {step.chsh_value !== null && (
          <div className="result-item">
            <span className="result-label">CHSH S Value</span>
            <span className={`result-value ${step.chsh_value >= 2 * Math.SQRT2 * 0.9 ? "text-safe" : "text-danger"}`}>
              {step.chsh_value.toFixed(3)}
            </span>
          </div>
        )}
      </div>
      {step.shared_key.length > 0 && (
        <div className="shared-key-display">
          <span className="result-label">Shared Key</span>
          <code className="key-bits">
            {step.shared_key.slice(0, 32).join("")}
            {step.shared_key.length > 32 ? "…" : ""}
          </code>
        </div>
      )}
    </div>
  );
}

const PROTOCOL_INFO: Record<string, { name: string; description: string }> = {
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
      "states: |0⟩ for bit 0 and |+⟩ for bit 1. Bob's conclusive measurements " +
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

export function App() {
  const [simId, setSimId] = useState<string | null>(null);
  const [steps, setSteps] = useState<StepResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [numQubits, setNumQubits] = useState(20);
  const [eavesdropper, setEavesdropper] = useState(false);
  const [protocol, setProtocol] = useState("bb84");
  const [error, setError] = useState<string | null>(null);

  const currentStep = steps.length > 0 ? steps[steps.length - 1] : null;
  const isComplete = currentStep?.is_complete ?? false;

  const handleCreate = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const id = await createSimulation(protocol, numQubits, eavesdropper);
      setSimId(id);
      setSteps([]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to create simulation");
    } finally {
      setLoading(false);
    }
  }, [protocol, numQubits, eavesdropper]);

  const handleStep = useCallback(async () => {
    if (!simId) return;
    setLoading(true);
    setError(null);
    try {
      const step = await stepSimulation(simId);
      setSteps((prev) => [...prev, step]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to step simulation");
    } finally {
      setLoading(false);
    }
  }, [simId]);

  const handleReset = useCallback(async () => {
    if (!simId) return;
    setLoading(true);
    setError(null);
    try {
      await resetSimulation(simId);
      setSteps([]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to reset simulation");
    } finally {
      setLoading(false);
    }
  }, [simId]);

  const handleNewSimulation = useCallback(() => {
    setSimId(null);
    setSteps([]);
    setError(null);
  }, []);

  return (
    <div className="app">
      <header className="app-header">
        <h1>
          <span className="logo-accent">QKD</span> Playground
        </h1>
        <p className="subtitle">
          Interactive Quantum Key Distribution Simulator
        </p>
      </header>

      <main className="app-main">
        {!simId ? (
          <div className="setup-panel">
            <h2>Configure Simulation</h2>
            <p className="setup-description">
              {PROTOCOL_INFO[protocol]?.description}
            </p>

            <div className="form-group">
              <label htmlFor="protocol-select">Protocol</label>
              <select
                id="protocol-select"
                className="protocol-select"
                value={protocol}
                onChange={(e) => setProtocol(e.target.value)}
              >
                <option value="bb84">BB84 — Bennett &amp; Brassard (1984)</option>
                <option value="b92">B92 — Bennett (1992)</option>
                <option value="e91">E91 — Ekert (1991)</option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="num-qubits">Number of Qubits</label>
              <input
                id="num-qubits"
                type="range"
                min={4}
                max={100}
                value={numQubits}
                onChange={(e) => setNumQubits(Number(e.target.value))}
              />
              <span className="range-value">{numQubits}</span>
            </div>

            <div className="form-group">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={eavesdropper}
                  onChange={(e) => setEavesdropper(e.target.checked)}
                />
                <span className="checkbox-text">
                  Enable Eavesdropper (Eve)
                </span>
              </label>
              {eavesdropper && (
                <p className="eve-warning">
                  Eve will intercept and re-send qubits, introducing ~25%
                  errors detectable by Alice and Bob.
                </p>
              )}
            </div>

            <button
              className="btn btn-primary"
              onClick={handleCreate}
              disabled={loading}
            >
              {loading ? "Creating…" : `Start ${PROTOCOL_INFO[protocol]?.name} Simulation`}
            </button>
          </div>
        ) : (
          <div className="simulation-panel">
            <ProgressBar
              currentPhase={currentStep?.phase ?? "preparation"}
            />

            <div className="controls">
              <button
                className="btn btn-primary"
                onClick={handleStep}
                disabled={loading || isComplete}
              >
                {loading
                  ? "Processing…"
                  : isComplete
                    ? "Complete"
                    : "Next Step →"}
              </button>
              <button
                className="btn btn-secondary"
                onClick={handleReset}
                disabled={loading}
              >
                Reset
              </button>
              <button
                className="btn btn-ghost"
                onClick={handleNewSimulation}
              >
                New Simulation
              </button>
            </div>

            {error && <div className="error-banner">{error}</div>}

            {currentStep && (
              <div className="step-display">
                <div className="step-header">
                  <span className="phase-badge">
                    {PHASE_LABELS[currentStep.phase] ?? currentStep.phase}
                  </span>
                  <span className="step-number">
                    Step {currentStep.step_index} of 5
                  </span>
                </div>
                <p className="step-description">{currentStep.description}</p>

                <QubitTable step={currentStep} />
                <ResultsPanel step={currentStep} />
              </div>
            )}

            {steps.length > 1 && (
              <div className="step-history">
                <h3>Step History</h3>
                {steps.slice(0, -1).map((s, i) => (
                  <div key={i} className="history-item">
                    <span className="history-phase">
                      {PHASE_LABELS[s.phase] ?? s.phase}
                    </span>
                    <span className="history-desc">{s.description}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </main>

      <footer className="app-footer">
        <p>
          Built by{" "}
          <a href="https://taoq.ai" target="_blank" rel="noopener noreferrer">
            TaoQ AI
          </a>{" "}
          &middot; Powered by Qiskit
        </p>
      </footer>
    </div>
  );
}
