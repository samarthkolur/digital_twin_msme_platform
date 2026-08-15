import type { DigitalTwinState } from "./api";

// health_index threshold matches the ML calibration target in design.md §6.3
// ("<0.6 = alert threshold"). The temperature threshold has no pilot-machine
// calibration yet (no real DS18B20 deployment, design.md §24) — it's a
// placeholder default the operator can override, not a calibrated value.
export const DEFAULT_HEALTH_INDEX_ALERT_THRESHOLD = 0.6;
export const DEFAULT_TEMPERATURE_ALERT_THRESHOLD_C = 70;

export interface AlertThresholds {
  healthIndex: number;
  temperatureC: number;
}

export interface DashboardAlert {
  level: "warning" | "critical";
  message: string;
}

/**
 * Evaluates the alert module's configurable thresholds (design.md §6.5)
 * against a single state object. A health index below 75% of the threshold
 * is treated as critical rather than a warning; everything else that trips
 * a threshold is a warning. The model's own `alert_level` (once Phase 4
 * populates it) is surfaced as-is alongside the threshold-based checks
 * rather than replacing them.
 */
export function evaluateAlerts(
  state: DigitalTwinState,
  thresholds: AlertThresholds,
): DashboardAlert[] {
  const alerts: DashboardAlert[] = [];

  if (state.health_index !== null && state.health_index < thresholds.healthIndex) {
    const critical = state.health_index < thresholds.healthIndex * 0.75;
    alerts.push({
      level: critical ? "critical" : "warning",
      message: `Health index ${state.health_index.toFixed(2)} is below the ${thresholds.healthIndex.toFixed(2)} alert threshold`,
    });
  }

  if (state.temperature_c > thresholds.temperatureC) {
    alerts.push({
      level: "warning",
      message: `Temperature ${String(state.temperature_c)}°C exceeds the ${String(thresholds.temperatureC)}°C threshold`,
    });
  }

  if (state.alert_level !== null && state.alert_level !== "normal") {
    alerts.push({
      level: state.alert_level === "critical" ? "critical" : "warning",
      message: `Model-reported alert level: ${state.alert_level}`,
    });
  }

  return alerts;
}
