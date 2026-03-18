import { useCallback, useEffect, useState } from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { PerformanceData } from "../../adapters";
import { getPerformanceData } from "../../adapters";
import { getConceptsForPhase } from "../../domain";
import { ConceptPanel } from "./ConceptPanel";

const PROTOCOL_COLORS: Record<string, string> = {
  bb84: "#4fd1c5",
  b92: "#c084fc",
  e91: "#f59e0b",
  sarg04: "#f87171",
  plob_bound: "#a1a1aa",
};

const PROTOCOL_LABELS: Record<string, string> = {
  bb84: "BB84",
  b92: "B92",
  e91: "E91",
  sarg04: "SARG04",
  plob_bound: "PLOB Bound",
};

const ALL_PROTOCOLS = ["bb84", "b92", "e91", "sarg04"] as const;

interface MergedPoint {
  distance: number;
  [key: string]: number | null;
}

function mergeProtocolData(data: PerformanceData, enabledProtocols: string[]): MergedPoint[] {
  const allKeys = [...enabledProtocols, "plob_bound"];
  const distanceCount = data.protocols["plob_bound"]?.length ?? 0;
  if (distanceCount === 0) return [];

  const merged: MergedPoint[] = [];
  for (let i = 0; i < distanceCount; i++) {
    const point: MergedPoint = {
      distance: data.protocols["plob_bound"][i].distance,
    };
    for (const key of allKeys) {
      const pts = data.protocols[key];
      if (pts && pts[i]) {
        // Use null for zero rates so they don't appear on log scale
        point[key] = pts[i].rate > 0 ? pts[i].rate : null;
      }
    }
    merged.push(point);
  }
  return merged;
}

export function PerformancePanel() {
  const [enabledProtocols, setEnabledProtocols] = useState<string[]>(["bb84", "b92", "sarg04"]);
  const [detectorEfficiency, setDetectorEfficiency] = useState(0.1);
  const [darkCountRate, setDarkCountRate] = useState(1e-6);
  const [maxDistance] = useState(200);
  const [data, setData] = useState<PerformanceData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    if (enabledProtocols.length === 0) return;
    setLoading(true);
    setError(null);
    try {
      const result = await getPerformanceData(
        enabledProtocols,
        maxDistance,
        detectorEfficiency,
        darkCountRate,
      );
      setData(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to fetch performance data");
    } finally {
      setLoading(false);
    }
  }, [enabledProtocols, maxDistance, detectorEfficiency, darkCountRate]);

  useEffect(() => {
    void fetchData();
  }, [fetchData]);

  const toggleProtocol = (proto: string) => {
    setEnabledProtocols((prev) =>
      prev.includes(proto) ? prev.filter((p) => p !== proto) : [...prev, proto],
    );
  };

  const chartData = data ? mergeProtocolData(data, enabledProtocols) : [];
  const concepts = getConceptsForPhase("performance", "all");

  return (
    <div className="performance-panel">
      <h2>Performance Analysis</h2>
      <p className="performance-subtitle">
        Secure key rate vs. channel distance for different QKD protocols
      </p>

      <div className="performance-controls">
        <div className="performance-protocols">
          <span className="control-label">Protocols</span>
          <div className="protocol-toggles">
            {ALL_PROTOCOLS.map((proto) => (
              <label key={proto} className="protocol-toggle">
                <input
                  type="checkbox"
                  checked={enabledProtocols.includes(proto)}
                  onChange={() => toggleProtocol(proto)}
                />
                <span className="protocol-toggle-label" style={{ color: PROTOCOL_COLORS[proto] }}>
                  {PROTOCOL_LABELS[proto]}
                </span>
              </label>
            ))}
          </div>
        </div>

        <div className="performance-params">
          <div className="param-group">
            <label htmlFor="detector-eff" className="control-label">
              Detector Efficiency
            </label>
            <input
              id="detector-eff"
              type="range"
              min={0.01}
              max={1.0}
              step={0.01}
              value={detectorEfficiency}
              onChange={(e) => setDetectorEfficiency(Number(e.target.value))}
            />
            <span className="range-value">{(detectorEfficiency * 100).toFixed(0)}%</span>
          </div>

          <div className="param-group">
            <label htmlFor="dark-count" className="control-label">
              Dark Count Rate
            </label>
            <select
              id="dark-count"
              className="protocol-select"
              value={darkCountRate}
              onChange={(e) => setDarkCountRate(Number(e.target.value))}
            >
              <option value={1e-5}>10⁻⁵</option>
              <option value={1e-6}>10⁻⁶</option>
              <option value={1e-7}>10⁻⁷</option>
              <option value={1e-8}>10⁻⁸</option>
            </select>
          </div>
        </div>
      </div>

      {error && <div className="error-banner">{error}</div>}

      <div className="performance-chart-wrapper">
        {loading && <div className="performance-loading">Loading...</div>}
        {chartData.length > 0 && (
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={chartData} margin={{ top: 10, right: 20, bottom: 10, left: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
              <XAxis
                dataKey="distance"
                tick={{ fill: "#a1a1aa", fontSize: 11 }}
                tickLine={false}
                axisLine={{ stroke: "#27272a" }}
                label={{
                  value: "Distance (km)",
                  position: "insideBottomRight",
                  offset: -5,
                  fill: "#a1a1aa",
                  fontSize: 12,
                }}
              />
              <YAxis
                scale="log"
                domain={[1e-10, 1]}
                allowDataOverflow
                tick={{ fill: "#a1a1aa", fontSize: 11 }}
                tickLine={false}
                axisLine={{ stroke: "#27272a" }}
                tickFormatter={(v: number) => {
                  if (v === 0) return "0";
                  const exp = Math.log10(v);
                  return `10^${Math.round(exp)}`;
                }}
                label={{
                  value: "Key Rate (bits/pulse)",
                  angle: -90,
                  position: "insideLeft",
                  offset: 10,
                  fill: "#a1a1aa",
                  fontSize: 12,
                }}
              />
              <Tooltip
                contentStyle={{
                  background: "#1a1a1a",
                  border: "1px solid #27272a",
                  borderRadius: 8,
                  color: "#fafafa",
                  fontSize: 12,
                }}
                formatter={(value, name) => [
                  value != null ? Number(value).toExponential(3) : "N/A",
                  PROTOCOL_LABELS[String(name)] ?? String(name),
                ]}
                labelFormatter={(label) => `${String(label)} km`}
              />
              <Legend
                formatter={(value: string) => PROTOCOL_LABELS[value] ?? value}
                wrapperStyle={{ fontSize: 12, color: "#a1a1aa" }}
              />
              <Line
                key="plob_bound"
                type="monotone"
                dataKey="plob_bound"
                stroke={PROTOCOL_COLORS["plob_bound"]}
                strokeDasharray="6 3"
                strokeWidth={1.5}
                dot={false}
                connectNulls={false}
                name="plob_bound"
              />
              {enabledProtocols.map((proto) => (
                <Line
                  key={proto}
                  type="monotone"
                  dataKey={proto}
                  stroke={PROTOCOL_COLORS[proto]}
                  strokeWidth={2}
                  dot={false}
                  connectNulls={false}
                  name={proto}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>

      <ConceptPanel concepts={concepts} />

      <div className="performance-info">
        <h3>About This Chart</h3>
        <p>
          This chart shows the theoretical secure key generation rate as a function of fiber
          distance. As distance increases, photon loss in the optical fiber reduces the key rate
          exponentially. The dashed PLOB bound line represents the fundamental upper limit for any
          point-to-point QKD protocol without quantum repeaters.
        </p>
        <p>
          BB84 and E91 share the same theoretical key rate with a 50% sift factor. B92 and SARG04
          have a lower 25% sift factor but offer other advantages: B92 uses fewer states, while
          SARG04 is more resilient to photon-number-splitting attacks. Adjust the hardware
          parameters above to see how detector quality affects maximum transmission distance.
        </p>
      </div>
    </div>
  );
}
