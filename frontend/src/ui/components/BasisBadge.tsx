export function BasisBadge({ basis }: { basis: string }) {
  const isRect = basis === "rectilinear";
  return (
    <span className={`basis-badge ${isRect ? "basis-rect" : "basis-diag"}`} title={basis}>
      {isRect ? "+" : "\u00d7"}
    </span>
  );
}
