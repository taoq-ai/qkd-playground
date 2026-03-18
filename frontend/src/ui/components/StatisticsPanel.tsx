import type { StepResponse } from "../../adapters";
import type { RunHistory } from "../../domain";
import { computeMetrics, EAVESDROP_THRESHOLDS } from "../../domain";
import { KeyEfficiencyChart } from "./KeyEfficiencyChart";
import { QBERGauge } from "./QBERGauge";
import { StatisticsGraphs } from "./StatisticsGraphs";

interface StatisticsPanelProps {
  currentStep: StepResponse;
  protocol: string;
  eavesdropperEnabled: boolean;
  runHistory: RunHistory[];
}

export function StatisticsPanel({
  currentStep,
  protocol,
  eavesdropperEnabled,
  runHistory,
}: StatisticsPanelProps) {
  // Only show after error estimation phase (when we have error_rate)
  if (currentStep.error_rate === null) return null;

  const metrics = computeMetrics(currentStep);
  const threshold = EAVESDROP_THRESHOLDS[protocol] ?? 0.11;

  return (
    <div className="statistics-panel">
      <h3>Statistics</h3>
      <div className="statistics-grid">
        <QBERGauge errorRate={metrics.errorRate} threshold={threshold} />
        <KeyEfficiencyChart metrics={metrics} />
      </div>
      <div className="statistics-summary">
        <div className="stat-item">
          <span className="stat-label">Sift Rate</span>
          <span className="stat-value">{(metrics.siftRate * 100).toFixed(1)}%</span>
        </div>
        <div className="stat-item">
          <span className="stat-label">Key Efficiency</span>
          <span className="stat-value">{(metrics.keyEfficiency * 100).toFixed(1)}%</span>
        </div>
      </div>
      <StatisticsGraphs
        currentStep={currentStep}
        protocol={protocol}
        eavesdropperEnabled={eavesdropperEnabled}
        runHistory={runHistory}
      />
    </div>
  );
}
