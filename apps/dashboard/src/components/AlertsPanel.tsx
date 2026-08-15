import type { JSX } from "react";
import type { DigitalTwinState } from "../api";
import { evaluateAlerts, type AlertThresholds } from "../thresholds";

interface AlertsPanelProps {
  state: DigitalTwinState;
  thresholds: AlertThresholds;
}

export function AlertsPanel({ state, thresholds }: AlertsPanelProps): JSX.Element {
  const alerts = evaluateAlerts(state, thresholds);

  if (alerts.length === 0) {
    return (
      <section aria-label="Alerts">
        <h3>Alerts</h3>
        <p>No active alerts.</p>
      </section>
    );
  }

  return (
    <section aria-label="Alerts">
      <h3>Alerts</h3>
      <ul>
        {alerts.map((alert) => (
          <li key={alert.message} data-level={alert.level} role="alert">
            {alert.message}
          </li>
        ))}
      </ul>
    </section>
  );
}
