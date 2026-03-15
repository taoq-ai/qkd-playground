import { ProtocolType } from "../domain";

export function App() {
  const protocols = Object.values(ProtocolType);

  return (
    <div>
      <h1>QKD Playground</h1>
      <p>Interactive Quantum Key Distribution Simulator</p>
      <h2>Available Protocols</h2>
      <ul>
        {protocols.map((p) => (
          <li key={p}>{p.toUpperCase()}</li>
        ))}
      </ul>
    </div>
  );
}
