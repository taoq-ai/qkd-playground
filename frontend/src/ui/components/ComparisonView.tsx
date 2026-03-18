import { useCallback, useState } from "react";
import type { StepResponse } from "../../adapters";
import { createSimulation, resetSimulation, runSimulation, stepSimulation } from "../../adapters";
import { computeMetrics } from "../../domain";
import { PHASE_LABELS, PROTOCOL_INFO } from "../constants";

interface PanelState {
  simId: string | null;
  steps: StepResponse[];
  loading: boolean;
  error: string | null;
}

const PROTOCOLS = ["bb84", "b92", "e91", "sarg04"] as const;

const PRESETS: { label: string; left: string; right: string }[] = [
  { label: "BB84 vs B92", left: "bb84", right: "b92" },
  { label: "BB84 vs SARG04", left: "bb84", right: "sarg04" },
];

const INITIAL_PANEL: PanelState = {
  simId: null,
  steps: [],
  loading: false,
  error: null,
};

function formatPercent(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

interface MetricRow {
  label: string;
  leftValue: string;
  rightValue: string;
  leftNumeric: number;
  rightNumeric: number;
  /** true when higher is better */
  higherIsBetter: boolean;
}

function MetricComparison({ rows }: { rows: MetricRow[] }) {
  return (
    <div className="comparison-metrics">
      <h3>Comparison Summary</h3>
      <table className="comparison-table">
        <thead>
          <tr>
            <th>Metric</th>
            <th>Left</th>
            <th>Right</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => {
            const leftBetter = row.higherIsBetter
              ? row.leftNumeric > row.rightNumeric
              : row.leftNumeric < row.rightNumeric;
            const rightBetter = row.higherIsBetter
              ? row.rightNumeric > row.leftNumeric
              : row.rightNumeric < row.leftNumeric;
            return (
              <tr key={row.label}>
                <td className="metric-label">{row.label}</td>
                <td className={leftBetter ? "metric-winner" : ""}>{row.leftValue}</td>
                <td className={rightBetter ? "metric-winner" : ""}>{row.rightValue}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function AllProtocolsSummary({ results }: { results: Record<string, StepResponse> }) {
  const protocols = Object.keys(results);
  return (
    <div className="comparison-metrics">
      <h3>All Protocols Summary</h3>
      <table className="comparison-table comparison-table-wide">
        <thead>
          <tr>
            <th>Metric</th>
            {protocols.map((p) => (
              <th key={p}>{PROTOCOL_INFO[p]?.name ?? p}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {(
            [
              { key: "errorRate", label: "QBER", fmt: formatPercent, higherBetter: false },
              { key: "siftRate", label: "Sift Rate", fmt: formatPercent, higherBetter: true },
              {
                key: "sharedKeyLength",
                label: "Final Key Length",
                fmt: (v: number) => String(v),
                higherBetter: true,
              },
              {
                key: "keyEfficiency",
                label: "Key Efficiency",
                fmt: formatPercent,
                higherBetter: true,
              },
            ] as const
          ).map((metric) => {
            const values = protocols.map((p) => {
              const m = computeMetrics(results[p]);
              return m[metric.key];
            });
            const best = metric.higherBetter ? Math.max(...values) : Math.min(...values);
            return (
              <tr key={metric.label}>
                <td className="metric-label">{metric.label}</td>
                {protocols.map((p, i) => (
                  <td key={p} className={values[i] === best ? "metric-winner" : ""}>
                    {metric.fmt(values[i])}
                  </td>
                ))}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function PanelDisplay({ protocol, panel }: { protocol: string; panel: PanelState }) {
  const currentStep = panel.steps.length > 0 ? panel.steps[panel.steps.length - 1] : null;

  return (
    <div className="comparison-panel">
      <h3 className="comparison-panel-title">{PROTOCOL_INFO[protocol]?.name ?? protocol}</h3>
      {panel.error && <div className="error-banner">{panel.error}</div>}
      {currentStep ? (
        <div className="comparison-panel-content">
          <div className="comparison-stat">
            <span className="stat-label">Phase</span>
            <span className="phase-badge">
              {PHASE_LABELS[currentStep.phase] ?? currentStep.phase}
            </span>
          </div>
          <div className="comparison-stat">
            <span className="stat-label">Step</span>
            <span className="stat-value">{currentStep.step_index} / 7</span>
          </div>
          <div className="comparison-stat">
            <span className="stat-label">Sifted Key</span>
            <span className="stat-value">
              {currentStep.sifted_key_alice.length > 0
                ? currentStep.sifted_key_alice.join("")
                : "\u2014"}
            </span>
          </div>
          <div className="comparison-stat">
            <span className="stat-label">Error Rate</span>
            <span className="stat-value">
              {currentStep.error_rate != null ? formatPercent(currentStep.error_rate) : "\u2014"}
            </span>
          </div>
          <div className="comparison-stat">
            <span className="stat-label">Final Key Length</span>
            <span className="stat-value">{currentStep.shared_key.length}</span>
          </div>
        </div>
      ) : (
        <p className="comparison-panel-empty">
          {panel.loading ? "Creating simulation\u2026" : "Not started"}
        </p>
      )}
    </div>
  );
}

export function ComparisonView() {
  const [leftProtocol, setLeftProtocol] = useState("bb84");
  const [rightProtocol, setRightProtocol] = useState("b92");
  const [numQubits, setNumQubits] = useState(20);
  const [eavesdropper, setEavesdropper] = useState(false);
  const [left, setLeft] = useState<PanelState>(INITIAL_PANEL);
  const [right, setRight] = useState<PanelState>(INITIAL_PANEL);
  const [allProtocolsResults, setAllProtocolsResults] = useState<Record<
    string,
    StepResponse
  > | null>(null);
  const [allProtocolsLoading, setAllProtocolsLoading] = useState(false);

  const isRunning = left.loading || right.loading;
  const leftCurrent = left.steps.length > 0 ? left.steps[left.steps.length - 1] : null;
  const rightCurrent = right.steps.length > 0 ? right.steps[right.steps.length - 1] : null;
  const bothStarted = left.simId !== null && right.simId !== null;
  const bothComplete = (leftCurrent?.is_complete ?? false) && (rightCurrent?.is_complete ?? false);

  const ensureSimulations = useCallback(async (): Promise<{
    leftId: string;
    rightId: string;
  } | null> => {
    let leftId = left.simId;
    let rightId = right.simId;

    if (!leftId) {
      setLeft((p) => ({ ...p, loading: true, error: null }));
      try {
        leftId = await createSimulation(leftProtocol, numQubits, eavesdropper);
        setLeft((p) => ({ ...p, simId: leftId, steps: [] }));
      } catch (e) {
        setLeft((p) => ({
          ...p,
          loading: false,
          error: e instanceof Error ? e.message : "Failed to create simulation",
        }));
        return null;
      }
    }

    if (!rightId) {
      setRight((p) => ({ ...p, loading: true, error: null }));
      try {
        rightId = await createSimulation(rightProtocol, numQubits, eavesdropper);
        setRight((p) => ({ ...p, simId: rightId, steps: [] }));
      } catch (e) {
        setRight((p) => ({
          ...p,
          loading: false,
          error: e instanceof Error ? e.message : "Failed to create simulation",
        }));
        return null;
      }
    }

    return { leftId: leftId!, rightId: rightId! };
  }, [left.simId, right.simId, leftProtocol, rightProtocol, numQubits, eavesdropper]);

  const handleStepBoth = useCallback(async () => {
    const ids = await ensureSimulations();
    if (!ids) return;

    setLeft((p) => ({ ...p, loading: true, error: null }));
    setRight((p) => ({ ...p, loading: true, error: null }));

    const [leftResult, rightResult] = await Promise.allSettled([
      stepSimulation(ids.leftId),
      stepSimulation(ids.rightId),
    ]);

    if (leftResult.status === "fulfilled") {
      setLeft((p) => ({ ...p, loading: false, steps: [...p.steps, leftResult.value] }));
    } else {
      setLeft((p) => ({
        ...p,
        loading: false,
        error: leftResult.reason instanceof Error ? leftResult.reason.message : "Step failed",
      }));
    }

    if (rightResult.status === "fulfilled") {
      setRight((p) => ({ ...p, loading: false, steps: [...p.steps, rightResult.value] }));
    } else {
      setRight((p) => ({
        ...p,
        loading: false,
        error: rightResult.reason instanceof Error ? rightResult.reason.message : "Step failed",
      }));
    }
  }, [ensureSimulations]);

  const handleRunBoth = useCallback(async () => {
    const ids = await ensureSimulations();
    if (!ids) return;

    setLeft((p) => ({ ...p, loading: true, error: null }));
    setRight((p) => ({ ...p, loading: true, error: null }));

    const [leftResult, rightResult] = await Promise.allSettled([
      runSimulation(ids.leftId),
      runSimulation(ids.rightId),
    ]);

    if (leftResult.status === "fulfilled") {
      setLeft((p) => ({ ...p, loading: false, steps: leftResult.value }));
    } else {
      setLeft((p) => ({
        ...p,
        loading: false,
        error: leftResult.reason instanceof Error ? leftResult.reason.message : "Run failed",
      }));
    }

    if (rightResult.status === "fulfilled") {
      setRight((p) => ({ ...p, loading: false, steps: rightResult.value }));
    } else {
      setRight((p) => ({
        ...p,
        loading: false,
        error: rightResult.reason instanceof Error ? rightResult.reason.message : "Run failed",
      }));
    }
  }, [ensureSimulations]);

  const handleReset = useCallback(async () => {
    const promises: Promise<void>[] = [];
    if (left.simId) {
      setLeft((p) => ({ ...p, loading: true }));
      promises.push(
        resetSimulation(left.simId).then(() =>
          setLeft({ simId: null, steps: [], loading: false, error: null }),
        ),
      );
    } else {
      setLeft(INITIAL_PANEL);
    }
    if (right.simId) {
      setRight((p) => ({ ...p, loading: true }));
      promises.push(
        resetSimulation(right.simId).then(() =>
          setRight({ simId: null, steps: [], loading: false, error: null }),
        ),
      );
    } else {
      setRight(INITIAL_PANEL);
    }
    setAllProtocolsResults(null);
    await Promise.allSettled(promises);
  }, [left.simId, right.simId]);

  const handleRunAllProtocols = useCallback(async () => {
    setAllProtocolsLoading(true);
    setAllProtocolsResults(null);

    try {
      const results: Record<string, StepResponse> = {};
      const entries = await Promise.all(
        PROTOCOLS.map(async (proto) => {
          const id = await createSimulation(proto, numQubits, eavesdropper);
          const steps = await runSimulation(id);
          return [proto, steps[steps.length - 1]] as [string, StepResponse];
        }),
      );
      for (const [proto, step] of entries) {
        results[proto] = step;
      }
      setAllProtocolsResults(results);
    } catch (e) {
      setLeft((p) => ({
        ...p,
        error: e instanceof Error ? e.message : "Failed to run all protocols",
      }));
    } finally {
      setAllProtocolsLoading(false);
    }
  }, [numQubits, eavesdropper]);

  const applyPreset = useCallback(
    (preset: (typeof PRESETS)[number]) => {
      setLeftProtocol(preset.left);
      setRightProtocol(preset.right);
      if (left.simId || right.simId) {
        setLeft(INITIAL_PANEL);
        setRight(INITIAL_PANEL);
      }
    },
    [left.simId, right.simId],
  );

  // Build comparison metrics when both panels have data
  const comparisonRows: MetricRow[] | null =
    leftCurrent && rightCurrent
      ? (() => {
          const lm = computeMetrics(leftCurrent);
          const rm = computeMetrics(rightCurrent);
          return [
            {
              label: "QBER",
              leftValue: formatPercent(lm.errorRate),
              rightValue: formatPercent(rm.errorRate),
              leftNumeric: lm.errorRate,
              rightNumeric: rm.errorRate,
              higherIsBetter: false,
            },
            {
              label: "Sift Rate",
              leftValue: formatPercent(lm.siftRate),
              rightValue: formatPercent(rm.siftRate),
              leftNumeric: lm.siftRate,
              rightNumeric: rm.siftRate,
              higherIsBetter: true,
            },
            {
              label: "Final Key Length",
              leftValue: String(lm.sharedKeyLength),
              rightValue: String(rm.sharedKeyLength),
              leftNumeric: lm.sharedKeyLength,
              rightNumeric: rm.sharedKeyLength,
              higherIsBetter: true,
            },
            {
              label: "Key Efficiency",
              leftValue: formatPercent(lm.keyEfficiency),
              rightValue: formatPercent(rm.keyEfficiency),
              leftNumeric: lm.keyEfficiency,
              rightNumeric: rm.keyEfficiency,
              higherIsBetter: true,
            },
          ];
        })()
      : null;

  return (
    <div className="comparison-container">
      <h2>Protocol Comparison</h2>
      <p className="setup-description">
        Run two protocols side-by-side with identical parameters to compare their performance.
      </p>

      <div className="comparison-controls">
        <div className="comparison-selectors">
          <div className="form-group">
            <label htmlFor="left-protocol">Left Protocol</label>
            <select
              id="left-protocol"
              className="protocol-select"
              value={leftProtocol}
              onChange={(e) => {
                setLeftProtocol(e.target.value);
                if (left.simId) setLeft(INITIAL_PANEL);
              }}
              disabled={isRunning}
            >
              {PROTOCOLS.map((p) => (
                <option key={p} value={p}>
                  {PROTOCOL_INFO[p]?.name ?? p}
                </option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label htmlFor="right-protocol">Right Protocol</label>
            <select
              id="right-protocol"
              className="protocol-select"
              value={rightProtocol}
              onChange={(e) => {
                setRightProtocol(e.target.value);
                if (right.simId) setRight(INITIAL_PANEL);
              }}
              disabled={isRunning}
            >
              {PROTOCOLS.map((p) => (
                <option key={p} value={p}>
                  {PROTOCOL_INFO[p]?.name ?? p}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="cmp-num-qubits">Number of Qubits</label>
          <input
            id="cmp-num-qubits"
            type="range"
            min={4}
            max={100}
            value={numQubits}
            onChange={(e) => setNumQubits(Number(e.target.value))}
            disabled={bothStarted || isRunning}
          />
          <span className="range-value">{numQubits}</span>
        </div>

        <div className="form-group">
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={eavesdropper}
              onChange={(e) => setEavesdropper(e.target.checked)}
              disabled={bothStarted || isRunning}
            />
            <span className="checkbox-text">Enable Eavesdropper (Eve)</span>
          </label>
        </div>

        <div className="comparison-presets">
          {PRESETS.map((preset) => (
            <button
              key={preset.label}
              className="btn btn-secondary"
              onClick={() => applyPreset(preset)}
              disabled={isRunning}
            >
              {preset.label}
            </button>
          ))}
          <button
            className="btn btn-secondary"
            onClick={handleRunAllProtocols}
            disabled={isRunning || allProtocolsLoading}
          >
            {allProtocolsLoading ? "Running\u2026" : "All Protocols"}
          </button>
        </div>

        <div className="comparison-actions">
          <button
            className="btn btn-primary"
            onClick={handleStepBoth}
            disabled={isRunning || bothComplete}
          >
            {isRunning ? "Processing\u2026" : "Step Both"}
          </button>
          <button
            className="btn btn-primary"
            onClick={handleRunBoth}
            disabled={isRunning || bothComplete}
          >
            {isRunning ? "Running\u2026" : "Run Both"}
          </button>
          <button className="btn btn-secondary" onClick={handleReset} disabled={isRunning}>
            Reset
          </button>
        </div>
      </div>

      <div className="comparison-panels">
        <PanelDisplay protocol={leftProtocol} panel={left} />
        <PanelDisplay protocol={rightProtocol} panel={right} />
      </div>

      {comparisonRows && <MetricComparison rows={comparisonRows} />}

      {allProtocolsResults && <AllProtocolsSummary results={allProtocolsResults} />}
    </div>
  );
}
