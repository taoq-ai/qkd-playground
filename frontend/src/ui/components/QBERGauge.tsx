interface QBERGaugeProps {
  errorRate: number;
  threshold: number;
}

export function QBERGauge({ errorRate, threshold }: QBERGaugeProps) {
  const maxRate = 0.5;
  const radius = 60;
  const strokeWidth = 10;
  const cx = 80;
  const cy = 75;

  // Arc from 180° to 0° (left to right semicircle)
  const startAngle = Math.PI;
  const endAngle = 0;
  const range = startAngle - endAngle;

  const rateAngle = startAngle - (Math.min(errorRate, maxRate) / maxRate) * range;
  const threshAngle = startAngle - (threshold / maxRate) * range;

  const arcX = (angle: number) => cx + radius * Math.cos(angle);
  const arcY = (angle: number) => cy - radius * Math.sin(angle);

  // Background arc
  const bgPath = `M ${arcX(startAngle)} ${arcY(startAngle)} A ${radius} ${radius} 0 0 1 ${arcX(endAngle)} ${arcY(endAngle)}`;

  // Value arc
  const largeArc = errorRate / maxRate > 0.5 ? 1 : 0;
  const valuePath = `M ${arcX(startAngle)} ${arcY(startAngle)} A ${radius} ${radius} 0 ${largeArc} 1 ${arcX(rateAngle)} ${arcY(rateAngle)}`;

  const isAbove = errorRate > threshold;

  return (
    <div className="qber-gauge">
      <svg viewBox="0 0 160 95" className="qber-gauge-svg">
        {/* Background arc */}
        <path
          d={bgPath}
          fill="none"
          stroke="#27272a"
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        />

        {/* Value arc */}
        {errorRate > 0 && (
          <path
            d={valuePath}
            fill="none"
            stroke={isAbove ? "#f87171" : "#4ade80"}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
          />
        )}

        {/* Threshold marker */}
        <line
          x1={arcX(threshAngle)}
          y1={arcY(threshAngle) - 8}
          x2={arcX(threshAngle)}
          y2={arcY(threshAngle) + 8}
          stroke="#a1a1aa"
          strokeWidth={2}
        />

        {/* Value text */}
        <text
          x={cx}
          y={cy - 8}
          textAnchor="middle"
          fill={isAbove ? "#f87171" : "#4ade80"}
          fontSize="20"
          fontWeight="700"
        >
          {(errorRate * 100).toFixed(1)}%
        </text>
        <text x={cx} y={cy + 8} textAnchor="middle" fill="#a1a1aa" fontSize="8">
          QBER
        </text>

        {/* Threshold label */}
        <text
          x={arcX(threshAngle)}
          y={arcY(threshAngle) + 18}
          textAnchor="middle"
          fill="#a1a1aa"
          fontSize="7"
        >
          {(threshold * 100).toFixed(0)}%
        </text>
      </svg>
    </div>
  );
}
