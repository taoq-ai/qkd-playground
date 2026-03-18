import { useCallback, useState } from "react";
import type { StepResponse } from "../adapters";
import { createSimulation, resetSimulation, stepSimulation } from "../adapters";
import { getConceptsForPhase } from "../domain";
import {
  BellTestPanel,
  CircuitDiagram,
  ComparisonView,
  ConceptPanel,
  EveAlert,
  EvePanel,
  PerformancePanel,
  ProgressBar,
  QubitTable,
  ResultsPanel,
  StatisticsPanel,
} from "./components";
import { PHASE_LABELS, PROTOCOL_INFO } from "./constants";
import "./styles.css";

type AppTab = "simulator" | "compare" | "bell-test" | "performance";

export function App() {
  const [activeTab, setActiveTab] = useState<AppTab>("simulator");
  const [simId, setSimId] = useState<string | null>(null);
  const [steps, setSteps] = useState<StepResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [numQubits, setNumQubits] = useState(20);
  const [eavesdropper, setEavesdropper] = useState(false);
  const [protocol, setProtocol] = useState("bb84");
  const [noiseLevel, setNoiseLevel] = useState(0);
  const [lossRate, setLossRate] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const currentStep = steps.length > 0 ? steps[steps.length - 1] : null;
  const isComplete = currentStep?.is_complete ?? false;

  const handleCreate = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const id = await createSimulation(
        protocol,
        numQubits,
        eavesdropper,
        noiseLevel / 100,
        lossRate / 100,
      );
      setSimId(id);
      setSteps([]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to create simulation");
    } finally {
      setLoading(false);
    }
  }, [protocol, numQubits, eavesdropper, noiseLevel, lossRate]);

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
        <p className="subtitle">Interactive Quantum Key Distribution Simulator</p>
        <nav className="app-nav">
          <button
            className={`nav-tab ${activeTab === "simulator" ? "nav-tab-active" : ""}`}
            onClick={() => setActiveTab("simulator")}
          >
            Simulator
          </button>
          <button
            className={`nav-tab ${activeTab === "compare" ? "nav-tab-active" : ""}`}
            onClick={() => setActiveTab("compare")}
          >
            Compare
          </button>
          <button
            className={`nav-tab ${activeTab === "bell-test" ? "nav-tab-active" : ""}`}
            onClick={() => setActiveTab("bell-test")}
          >
            Bell Test
          </button>
          <button
            className={`nav-tab ${activeTab === "performance" ? "nav-tab-active" : ""}`}
            onClick={() => setActiveTab("performance")}
          >
            Performance
          </button>
        </nav>
      </header>

      <main className="app-main">
        {activeTab === "performance" ? (
          <PerformancePanel />
        ) : activeTab === "compare" ? (
          <ComparisonView />
        ) : activeTab === "bell-test" ? (
          <BellTestPanel />
        ) : !simId ? (
          <div className="setup-panel">
            <h2>Configure Simulation</h2>
            <p className="setup-description">{PROTOCOL_INFO[protocol]?.description}</p>

            <div className="form-group">
              <label htmlFor="protocol-select">Protocol</label>
              <select
                id="protocol-select"
                className="protocol-select"
                value={protocol}
                onChange={(e) => setProtocol(e.target.value)}
              >
                <option value="bb84">BB84 &mdash; Bennett &amp; Brassard (1984)</option>
                <option value="b92">B92 &mdash; Bennett (1992)</option>
                <option value="e91">E91 &mdash; Ekert (1991)</option>
                <option value="sarg04">
                  SARG04 &mdash; Scarani, Acin, Ribordy &amp; Gisin (2004)
                </option>
                <option value="decoy_bb84">Decoy-State BB84 &mdash; Practical WCP Protocol</option>
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
                <span className="checkbox-text">Enable Eavesdropper (Eve)</span>
              </label>
              {eavesdropper && (
                <p className="eve-warning">
                  Eve will intercept and re-send qubits, introducing ~25% errors detectable by Alice
                  and Bob.
                </p>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="noise-level">Channel Noise (Depolarization)</label>
              <input
                id="noise-level"
                type="range"
                min={0}
                max={50}
                step={1}
                value={noiseLevel}
                onChange={(e) => setNoiseLevel(Number(e.target.value))}
              />
              <span className="range-value">{noiseLevel}%</span>
            </div>

            <div className="form-group">
              <label htmlFor="loss-rate">Photon Loss</label>
              <input
                id="loss-rate"
                type="range"
                min={0}
                max={50}
                step={1}
                value={lossRate}
                onChange={(e) => setLossRate(Number(e.target.value))}
              />
              <span className="range-value">{lossRate}%</span>
            </div>

            {(noiseLevel > 0 || lossRate > 0) && (
              <p className="noise-info">
                Channel imperfections will introduce errors even without an eavesdropper, modeling
                real-world fiber optic conditions.
              </p>
            )}

            <button className="btn btn-primary" onClick={handleCreate} disabled={loading}>
              {loading ? "Creating\u2026" : `Start ${PROTOCOL_INFO[protocol]?.name} Simulation`}
            </button>
          </div>
        ) : (
          <div className="simulation-panel">
            <ProgressBar currentPhase={currentStep?.phase ?? "preparation"} />

            <div className="controls">
              <button
                className="btn btn-primary"
                onClick={handleStep}
                disabled={loading || isComplete}
              >
                {loading ? "Processing\u2026" : isComplete ? "Complete" : "Next Step \u2192"}
              </button>
              <button className="btn btn-secondary" onClick={handleReset} disabled={loading}>
                Reset
              </button>
              <button className="btn btn-ghost" onClick={handleNewSimulation}>
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
                  <span className="step-number">Step {currentStep.step_index} of 7</span>
                </div>
                <p className="step-description">{currentStep.description}</p>

                <ConceptPanel concepts={getConceptsForPhase(currentStep.phase, protocol)} />

                <CircuitDiagram
                  step={currentStep}
                  protocol={protocol}
                  eavesdropper={eavesdropper}
                />
                <QubitTable step={currentStep} />
                <EvePanel step={currentStep} eavesdropperEnabled={eavesdropper} />
                <EveAlert
                  errorRate={currentStep.error_rate}
                  eavesdropperDetected={currentStep.eavesdropper_detected}
                  protocol={protocol}
                />
                <ResultsPanel step={currentStep} />
                <StatisticsPanel currentStep={currentStep} protocol={protocol} />
              </div>
            )}

            {steps.length > 1 && (
              <div className="step-history">
                <h3>Step History</h3>
                {steps.slice(0, -1).map((s, i) => (
                  <div key={i} className="history-item">
                    <span className="history-phase">{PHASE_LABELS[s.phase] ?? s.phase}</span>
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
