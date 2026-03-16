import type { ConceptEntry } from "../../domain";

interface ConceptPanelProps {
  concepts: ConceptEntry[];
}

export function ConceptPanel({ concepts }: ConceptPanelProps) {
  if (concepts.length === 0) return null;

  return (
    <div className="concept-panels">
      {concepts.map((concept, i) => (
        <details key={concept.id} className="concept-panel" open={i === 0}>
          <summary className="concept-summary">
            <span className="concept-title">{concept.title}</span>
          </summary>
          <p className="concept-text">{concept.summary}</p>
          <p className="concept-detail">{concept.detail}</p>
        </details>
      ))}
    </div>
  );
}
