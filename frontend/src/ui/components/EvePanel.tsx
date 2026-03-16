import type { StepResponse } from "../../adapters";
import { BasisBadge } from "./BasisBadge";
import { BitCell } from "./BitCell";

interface EvePanelProps {
  step: StepResponse;
  eavesdropperEnabled: boolean;
}

export function EvePanel({ step, eavesdropperEnabled }: EvePanelProps) {
  if (!eavesdropperEnabled || !step.eve_intercepted) return null;

  const count = step.eve_bases.length;
  if (count === 0) return null;

  const maxShow = Math.min(count, 20);
  const truncated = count > maxShow;

  // Calculate how many of Eve's bases matched Alice's
  const correctGuesses = step.eve_bases.filter((b, i) => step.alice_bases[i] === b).length;
  const guessRate = count > 0 ? ((correctGuesses / count) * 100).toFixed(0) : "0";

  return (
    <div className="eve-panel">
      <div className="eve-panel-header">
        <span className="eve-icon">{"\u{1f441}"}</span>
        <h3>Eve&apos;s Interception</h3>
        <span className="eve-stats">
          {count} qubits intercepted &middot; {guessRate}% basis match
        </span>
      </div>

      <div className="qubit-table-wrapper">
        <div className="qubit-table">
          <div className="qubit-row">
            <span className="row-label">Eve&apos;s Bases</span>
            {step.eve_bases.slice(0, maxShow).map((b, i) => (
              <BasisBadge key={`eb-${i}`} basis={b} />
            ))}
            {truncated && <span className="ellipsis">&hellip;</span>}
          </div>
          <div className="qubit-row">
            <span className="row-label">Eve&apos;s Results</span>
            {step.eve_results.slice(0, maxShow).map((r, i) => (
              <BitCell key={`er-${i}`} value={r} />
            ))}
            {truncated && <span className="ellipsis">&hellip;</span>}
          </div>
          {step.alice_bases.length > 0 && (
            <div className="qubit-row">
              <span className="row-label">Basis Match</span>
              {step.eve_bases.slice(0, maxShow).map((b, i) => (
                <span
                  key={`em-${i}`}
                  className={`match-cell ${b === step.alice_bases[i] ? "match-yes" : "match-no"}`}
                >
                  {b === step.alice_bases[i] ? "\u2713" : "\u2717"}
                </span>
              ))}
              {truncated && <span className="ellipsis">&hellip;</span>}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
