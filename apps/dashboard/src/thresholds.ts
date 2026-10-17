import type { DigitalTwinState } from "./api";

// The thresholds themselves now come from the project config (config.ts,
// design.md DD-047): health_index 0.6 matches the ML calibration target in
// §6.3; the 70 °C temperature default has no pilot-machine calibration yet
// (§24) and is an operator-adjustable placeholder.

export interface AlertThresholds {
  healthIndex: number;
  temperatureC: number;
  /** A health index below healthIndex x this is critical, not a warning. */
  criticalFraction: number;
}

interface DashboardAlert {
  level: "warning" | "critical";
  message: string;
}

/**
 * Evaluates the alert module's configurable thresholds (design.md §6.5)
 * against a single state object. A health index below `criticalFraction` of
 * the threshold (the config's alertCriticalFraction, 0.75 by default) is
 * treated as critical rather than a warning; everything else that trips
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
    const critical = state.health_index < thresholds.healthIndex * thresholds.criticalFraction;
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
