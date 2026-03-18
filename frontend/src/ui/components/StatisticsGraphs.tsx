import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { StepResponse } from "../../adapters";
import type { RunHistory } from "../../domain";
import { EAVESDROP_THRESHOLDS, estimateEveInformation } from "../../domain";

const TOOLTIP_STYLE = {
  background: "#1a1a1a",
  border: "1px solid #27272a",
  borderRadius: 8,
  color: "#fafafa",
  fontSize: 12,
};

const AXIS_TICK = { fill: "#a1a1aa", fontSize: 10 };

interface StatisticsGraphsProps {
  currentStep: StepResponse;
  protocol: string;
  eavesdropperEnabled: boolean;
  runHistory: RunHistory[];
}

export function StatisticsGraphs({
  currentStep,
  protocol,
  eavesdropperEnabled,
  runHistory,
}: StatisticsGraphsProps) {
  const threshold = EAVESDROP_THRESHOLDS[protocol] ?? 0.11;

  return (
    <div className="statistics-graphs">
      {runHistory.length > 1 && <QBERLineChart history={runHistory} threshold={threshold} />}
      <KeyLengthBarChart step={currentStep} />
      <MeasurementHistogram step={currentStep} />
      {eavesdropperEnabled && currentStep.error_rate !== null && currentStep.error_rate > 0 && (
        <EveInformationDisplay errorRate={currentStep.error_rate} />
      )}
    </div>
  );
}

/* ---------- Multi-run QBER line chart ---------- */

function QBERLineChart({ history, threshold }: { history: RunHistory[]; threshold: number }) {
  const data = history.map((r) => ({
    run: r.runNumber,
    qber: parseFloat((r.qber * 100).toFixed(2)),
  }));

  return (
    <div className="chart-wrapper">
      <h4 className="chart-title">QBER Across Runs</h4>
      <p className="chart-description">
        Track quantum bit error rate across multiple simulation runs. The dashed line marks the
        eavesdropper detection threshold.
      </p>
      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
          <XAxis
            dataKey="run"
            tick={AXIS_TICK}
            tickLine={false}
            axisLine={false}
            label={{ value: "Run #", position: "insideBottomRight", offset: -5, ...AXIS_TICK }}
          />
          <YAxis
            tick={AXIS_TICK}
            tickLine={false}
            axisLine={false}
            label={{
              value: "QBER %",
              angle: -90,
              position: "insideLeft",
              offset: 10,
              ...AXIS_TICK,
            }}
          />
          <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v) => [`${v}%`, "QBER"]} />
          <ReferenceLine
            y={threshold * 100}
            stroke="#f87171"
            strokeDasharray="6 3"
            label={{
              value: `Threshold ${(threshold * 100).toFixed(0)}%`,
              fill: "#f87171",
              fontSize: 10,
              position: "right",
            }}
          />
          <Line
            type="monotone"
            dataKey="qber"
            stroke="#4fd1c5"
            strokeWidth={2}
            dot={{ fill: "#4fd1c5", r: 3 }}
            activeDot={{ r: 5 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

/* ---------- Key length comparison bar chart ---------- */

function KeyLengthBarChart({ step }: { step: StepResponse }) {
  const rawLength = step.alice_bits.length;
  const siftedLength = step.sifted_key_alice.length;
  const finalLength =
    step.amplified_key.length > 0 ? step.amplified_key.length : step.shared_key.length;

  const data = [
    { name: "Raw Key", length: rawLength },
    { name: "Sifted Key", length: siftedLength },
    { name: "Final Key", length: finalLength },
  ];

  return (
    <div className="chart-wrapper">
      <h4 className="chart-title">Key Length Comparison</h4>
      <p className="chart-description">
        Shows how key length decreases through sifting, reconciliation, and privacy amplification.
      </p>
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
          <XAxis dataKey="name" tick={AXIS_TICK} tickLine={false} axisLine={false} />
          <YAxis
            tick={AXIS_TICK}
            tickLine={false}
            axisLine={false}
            label={{ value: "Bits", angle: -90, position: "insideLeft", offset: 10, ...AXIS_TICK }}
          />
          <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v) => [`${v} bits`, "Length"]} />
          <Bar dataKey="length" fill="#38b2ac" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

/* ---------- Measurement outcome histogram ---------- */

function MeasurementHistogram({ step }: { step: StepResponse }) {
  const aliceBits = step.alice_bits;
  const bobBits = step.bob_results;

  const alice0 = aliceBits.filter((b) => b === 0).length;
  const alice1 = aliceBits.filter((b) => b === 1).length;
  const bob0 = bobBits.filter((b) => b === 0).length;
  const bob1 = bobBits.filter((b) => b === 1).length;

  const data = [
    { outcome: "0", Alice: alice0, Bob: bob0 },
    { outcome: "1", Alice: alice1, Bob: bob1 },
  ];

  return (
    <div className="chart-wrapper">
      <h4 className="chart-title">Measurement Outcomes</h4>
      <p className="chart-description">
        Distribution of 0s and 1s in Alice&apos;s prepared bits and Bob&apos;s measurement results.
      </p>
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
          <XAxis dataKey="outcome" tick={AXIS_TICK} tickLine={false} axisLine={false} />
          <YAxis
            tick={AXIS_TICK}
            tickLine={false}
            axisLine={false}
            label={{
              value: "Count",
              angle: -90,
              position: "insideLeft",
              offset: 10,
              ...AXIS_TICK,
            }}
          />
          <Tooltip contentStyle={TOOLTIP_STYLE} />
          <Legend wrapperStyle={{ fontSize: 11, color: "#a1a1aa" }} />
          <Bar dataKey="Alice" fill="#4fd1c5" radius={[4, 4, 0, 0]} />
          <Bar dataKey="Bob" fill="#81e6d9" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

/* ---------- Eve's information estimation ---------- */

function EveInformationDisplay({ errorRate }: { errorRate: number }) {
  const eveInfo = estimateEveInformation(errorRate);
  const percent = (eveInfo * 100).toFixed(1);
  const barWidth = Math.min(eveInfo * 100, 100);

  return (
    <div className="chart-wrapper eve-info-wrapper">
      <h4 className="chart-title">Eve&apos;s Estimated Information</h4>
      <p className="chart-description">
        Upper bound on Eve&apos;s information gain, derived from the error rate using the binary
        entropy bound: Info = 1 - H(e).
      </p>
      <div className="eve-info-display">
        <div className="eve-info-bar-track">
          <div
            className="eve-info-bar-fill"
            style={{ width: `${barWidth}%` }}
            role="progressbar"
            aria-valuenow={eveInfo * 100}
            aria-valuemin={0}
            aria-valuemax={100}
          />
        </div>
        <div className="eve-info-labels">
          <span className="eve-info-value">{percent}%</span>
          <span className="eve-info-caption">
            {eveInfo < 0.1
              ? "Low risk — Eve has minimal information"
              : eveInfo < 0.5
                ? "Moderate risk — privacy amplification needed"
                : "High risk — key may be compromised"}
          </span>
        </div>
      </div>
    </div>
  );
}
