import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { SimulationMetrics } from "../../domain";

interface KeyEfficiencyChartProps {
  metrics: SimulationMetrics;
}

export function KeyEfficiencyChart({ metrics }: KeyEfficiencyChartProps) {
  const data = [
    { name: "Total Qubits", value: metrics.totalQubits, fill: "#4fd1c5" },
    { name: "Sifted Key", value: metrics.siftedKeyLength, fill: "#38b2ac" },
    { name: "Shared Key", value: metrics.sharedKeyLength, fill: "#81e6d9" },
  ];

  return (
    <div className="key-efficiency-chart">
      <h4 className="chart-title">Key Efficiency</h4>
      <ResponsiveContainer width="100%" height={180}>
        <BarChart data={data} margin={{ top: 5, right: 5, bottom: 5, left: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
          <XAxis
            dataKey="name"
            tick={{ fill: "#a1a1aa", fontSize: 10 }}
            tickLine={false}
            axisLine={false}
          />
          <YAxis tick={{ fill: "#a1a1aa", fontSize: 10 }} tickLine={false} axisLine={false} />
          <Tooltip
            contentStyle={{
              background: "#1a1a1a",
              border: "1px solid #27272a",
              borderRadius: 8,
              color: "#fafafa",
              fontSize: 12,
            }}
          />
          <Bar dataKey="value" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
