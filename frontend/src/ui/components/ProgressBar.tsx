import { PHASE_LABELS, PHASE_ORDER } from "../constants";

export function ProgressBar({ currentPhase }: { currentPhase: string }) {
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
