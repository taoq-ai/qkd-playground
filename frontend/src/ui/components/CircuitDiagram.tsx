import type { StepResponse } from "../../adapters";

const ROW_HEIGHT = 36;
const HEADER_HEIGHT = 30;
const ALICE_X = 60;
const GATE_W = 28;
const GATE_H = 24;
const CHANNEL_START = 130;
const CHANNEL_END = 480;
const BOB_X = 520;
const SVG_WIDTH = 620;
const RESULT_X = 570;

const PHASE_IDX: Record<string, number> = {
  preparation: 0,
  transmission: 1,
  measurement: 2,
  sifting: 3,
  error_estimation: 4,
  complete: 5,
};

function basisColor(basis: string): string {
  return basis === "rectilinear" ? "#4fd1c5" : "#c084fc";
}

function basisSymbol(basis: string): string {
  return basis === "rectilinear" ? "+" : "\u00d7";
}

interface CircuitDiagramProps {
  step: StepResponse;
  protocol: string;
  eavesdropper: boolean;
  maxQubits?: number;
}

export function CircuitDiagram({
  step,
  protocol,
  eavesdropper,
  maxQubits = 8,
}: CircuitDiagramProps) {
  const totalQubits = step.alice_bits.length;
  if (totalQubits === 0) return null;

  const showCount = Math.min(totalQubits, maxQubits);
  const truncated = totalQubits > showCount;
  const phaseIdx = PHASE_IDX[step.phase] ?? 0;

  const svgHeight = HEADER_HEIGHT + showCount * ROW_HEIGHT + (truncated ? 28 : 8);

  const showChannel = phaseIdx >= 1;
  const showBob = phaseIdx >= 2;
  const showSifting = phaseIdx >= 3;

  return (
    <div className="circuit-diagram-wrapper">
      <svg
        viewBox={`0 0 ${SVG_WIDTH} ${svgHeight}`}
        className="circuit-diagram"
        role="img"
        aria-label={`Quantum circuit diagram — ${protocol.toUpperCase()} ${step.phase} phase`}
      >
        {/* Column headers */}
        <text
          x={ALICE_X + GATE_W / 2}
          y={16}
          textAnchor="middle"
          className="circuit-header"
          fill="#4fd1c5"
          fontSize="11"
          fontWeight="600"
        >
          Alice
        </text>
        <text
          x={(CHANNEL_START + CHANNEL_END) / 2}
          y={16}
          textAnchor="middle"
          className="circuit-header"
          fill={eavesdropper ? "#f87171" : "#a1a1aa"}
          fontSize="11"
          fontWeight="600"
        >
          {eavesdropper ? "Channel (Eve)" : "Channel"}
        </text>
        <text
          x={BOB_X + GATE_W / 2}
          y={16}
          textAnchor="middle"
          className="circuit-header"
          fill="#4fd1c5"
          fontSize="11"
          fontWeight="600"
        >
          Bob
        </text>

        {/* Qubit wires */}
        {Array.from({ length: showCount }, (_, i) => {
          const y = HEADER_HEIGHT + i * ROW_HEIGHT + ROW_HEIGHT / 2;
          const aliceBasis = step.alice_bases[i];
          const bobBasis = step.bob_bases[i];
          const isMatched = step.matching_bases[i];
          const dimmed = showSifting && !isMatched;
          const opacity = dimmed ? 0.2 : 1;

          return (
            <g key={i} opacity={opacity}>
              {/* Qubit index */}
              <text x={12} y={y + 4} fill="#a1a1aa" fontSize="9" fontFamily="monospace">
                q{i}
              </text>

              {/* Alice's gate */}
              <rect
                x={ALICE_X}
                y={y - GATE_H / 2}
                width={GATE_W}
                height={GATE_H}
                rx={4}
                fill={aliceBasis ? basisColor(aliceBasis) + "20" : "#27272a"}
                stroke={aliceBasis ? basisColor(aliceBasis) : "#27272a"}
                strokeWidth={1}
              />
              {aliceBasis && (
                <text
                  x={ALICE_X + GATE_W / 2}
                  y={y + 4}
                  textAnchor="middle"
                  fill={basisColor(aliceBasis)}
                  fontSize="12"
                  fontWeight="700"
                >
                  {basisSymbol(aliceBasis)}
                </text>
              )}
              {/* Alice's bit value above gate */}
              {step.alice_bits[i] !== undefined && (
                <text
                  x={ALICE_X + GATE_W / 2}
                  y={y - GATE_H / 2 - 4}
                  textAnchor="middle"
                  fill="#a1a1aa"
                  fontSize="8"
                  fontFamily="monospace"
                >
                  {step.alice_bits[i]}
                </text>
              )}

              {/* Quantum channel wire */}
              {showChannel && (
                <line
                  x1={ALICE_X + GATE_W + 4}
                  y1={y}
                  x2={showBob ? BOB_X - 4 : CHANNEL_END}
                  y2={y}
                  stroke={eavesdropper ? "#f8717160" : "#27272a"}
                  strokeWidth={1.5}
                  strokeDasharray={eavesdropper ? "4 3" : "none"}
                />
              )}

              {/* Eve interception marker */}
              {showChannel && eavesdropper && (
                <g>
                  <polygon
                    points={`${(CHANNEL_START + CHANNEL_END) / 2},${y - 8} ${(CHANNEL_START + CHANNEL_END) / 2 + 6},${y} ${(CHANNEL_START + CHANNEL_END) / 2},${y + 8} ${(CHANNEL_START + CHANNEL_END) / 2 - 6},${y}`}
                    fill="#f87171"
                    opacity={0.7}
                  />
                </g>
              )}

              {/* Bob's gate */}
              {showBob && bobBasis && (
                <>
                  <rect
                    x={BOB_X}
                    y={y - GATE_H / 2}
                    width={GATE_W}
                    height={GATE_H}
                    rx={4}
                    fill={basisColor(bobBasis) + "20"}
                    stroke={basisColor(bobBasis)}
                    strokeWidth={1}
                  />
                  <text
                    x={BOB_X + GATE_W / 2}
                    y={y + 4}
                    textAnchor="middle"
                    fill={basisColor(bobBasis)}
                    fontSize="12"
                    fontWeight="700"
                  >
                    {basisSymbol(bobBasis)}
                  </text>
                </>
              )}

              {/* Bob's result */}
              {showBob && step.bob_results[i] !== undefined && (
                <text
                  x={RESULT_X}
                  y={y + 4}
                  textAnchor="middle"
                  fill="#fafafa"
                  fontSize="10"
                  fontFamily="monospace"
                  fontWeight="600"
                >
                  {step.bob_results[i]}
                </text>
              )}

              {/* Match indicator after sifting */}
              {showSifting && step.matching_bases[i] !== undefined && (
                <circle
                  cx={RESULT_X + 24}
                  cy={y}
                  r={5}
                  fill={isMatched ? "#4ade80" : "#f87171"}
                  opacity={isMatched ? 1 : 0.4}
                />
              )}
            </g>
          );
        })}

        {/* Truncation indicator */}
        {truncated && (
          <text
            x={SVG_WIDTH / 2}
            y={svgHeight - 6}
            textAnchor="middle"
            fill="#a1a1aa"
            fontSize="10"
          >
            \u2026 {totalQubits - showCount} more qubits
          </text>
        )}
      </svg>
    </div>
  );
}
