import type { StepResponse } from "../../adapters";
import { BasisBadge } from "./BasisBadge";
import { BitCell } from "./BitCell";

export function QubitTable({ step }: { step: StepResponse }) {
  const count = step.alice_bits.length;
  if (count === 0) return null;

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
              <span key={`c-${i}`} className={`match-cell ${c ? "match-yes" : "match-no"}`}>
                {c ? "\u2713" : "\u2717"}
              </span>
            ))}
            {truncated && <span className="ellipsis">&hellip;</span>}
          </div>
        )}
        {step.matching_bases.length > 0 && (
          <div className="qubit-row">
            <span className="row-label">Bases Match</span>
            {step.matching_bases.slice(0, maxShow).map((m, i) => (
              <span key={`m-${i}`} className={`match-cell ${m ? "match-yes" : "match-no"}`}>
                {m ? "\u2713" : "\u2717"}
              </span>
            ))}
            {truncated && <span className="ellipsis">&hellip;</span>}
          </div>
        )}
      </div>
    </div>
  );
}
