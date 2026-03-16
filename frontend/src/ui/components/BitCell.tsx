export function BitCell({ value, highlight }: { value: number; highlight?: boolean }) {
  return <span className={`bit-cell ${highlight ? "bit-highlight" : ""}`}>{value}</span>;
}
