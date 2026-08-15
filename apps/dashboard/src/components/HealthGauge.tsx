import type { JSX } from "react";

interface HealthGaugeProps {
  healthIndex: number | null;
}

const SIZE = 120;
const STROKE = 12;
const RADIUS = (SIZE - STROKE) / 2;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

function gaugeColor(value: number): string {
  if (value >= 0.8) return "#2e7d32"; // healthy
  if (value >= 0.6) return "#ed6c02"; // warning (matches the §6.3 <0.6 alert threshold)
  return "#c62828"; // critical
}

export function HealthGauge({ healthIndex }: HealthGaugeProps): JSX.Element {
  if (healthIndex === null) {
    return (
      <div role="status" aria-label="Health index gauge">
        <p>Health index not available yet — the ML pipeline hasn&apos;t produced a reading.</p>
      </div>
    );
  }

  const clamped = Math.max(0, Math.min(1, healthIndex));
  const offset = CIRCUMFERENCE * (1 - clamped);

  return (
    <div role="img" aria-label={`Health index gauge: ${clamped.toFixed(2)} out of 1.00`}>
      <svg width={SIZE} height={SIZE} viewBox={`0 0 ${String(SIZE)} ${String(SIZE)}`}>
        <circle
          cx={SIZE / 2}
          cy={SIZE / 2}
          r={RADIUS}
          fill="none"
          stroke="#e0e0e0"
          strokeWidth={STROKE}
        />
        <circle
          cx={SIZE / 2}
          cy={SIZE / 2}
          r={RADIUS}
          fill="none"
          stroke={gaugeColor(clamped)}
          strokeWidth={STROKE}
          strokeDasharray={CIRCUMFERENCE}
          strokeDashoffset={offset}
          strokeLinecap="round"
          transform={`rotate(-90 ${String(SIZE / 2)} ${String(SIZE / 2)})`}
        />
        <text x="50%" y="50%" textAnchor="middle" dominantBaseline="middle" fontSize="24">
          {clamped.toFixed(2)}
        </text>
      </svg>
    </div>
  );
}
