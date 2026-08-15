import type { JSX } from "react";

interface TrendChartProps {
  label: string;
  unit: string;
  /** Chronological order (oldest first) — callers reverse api's most-recent-first history. */
  points: number[];
  width?: number;
  height?: number;
}

/**
 * A dependency-free SVG line chart (design.md §6.5 "vibration RMS trend
 * (rolling 1-hour window), temperature trend"). No charting library is
 * added for this — a single polyline is all either trend needs.
 */
export function TrendChart({
  label,
  unit,
  points,
  width = 320,
  height = 80,
}: TrendChartProps): JSX.Element {
  if (points.length === 0) {
    return (
      <figure>
        <figcaption>{label}</figcaption>
        <p>No trend data yet.</p>
      </figure>
    );
  }

  const min = Math.min(...points);
  const max = Math.max(...points);
  const range = max - min || 1;
  const step = points.length > 1 ? width / (points.length - 1) : 0;

  const coords = points
    .map((value, index) => {
      const x = index * step;
      const y = height - ((value - min) / range) * height;
      return `${String(x)},${String(y)}`;
    })
    .join(" ");

  const latest = points[points.length - 1] ?? 0;

  return (
    <figure>
      <figcaption>
        {label}: {latest.toFixed(2)} {unit} (last {points.length} reading
        {points.length === 1 ? "" : "s"})
      </figcaption>
      <svg
        width={width}
        height={height}
        viewBox={`0 0 ${String(width)} ${String(height)}`}
        role="img"
        aria-label={`${label} trend chart`}
      >
        <polyline points={coords} fill="none" stroke="currentColor" strokeWidth={2} />
      </svg>
    </figure>
  );
}
