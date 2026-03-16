import type { StepResponse } from "../../adapters";

export function ResultsPanel({ step }: { step: StepResponse }) {
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
            {detected ? "\u26a0 Detected!" : "\u2713 Not detected"}
          </span>
        </div>
        {step.chsh_value !== null && (
          <div className="result-item">
            <span className="result-label">CHSH S Value</span>
            <span
              className={`result-value ${step.chsh_value >= 2 * Math.SQRT2 * 0.9 ? "text-safe" : "text-danger"}`}
            >
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
            {step.shared_key.length > 32 ? "\u2026" : ""}
          </code>
        </div>
      )}
    </div>
  );
}
