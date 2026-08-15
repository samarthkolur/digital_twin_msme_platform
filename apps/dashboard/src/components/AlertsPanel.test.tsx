import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { AlertsPanel } from "./AlertsPanel";
import type { DigitalTwinState } from "../api";

function state(overrides: Partial<DigitalTwinState> = {}): DigitalTwinState {
  return {
    asset_id: "motor_01",
    timestamp: "2026-07-01T09:32:15Z",
    vibration: {
      rms_g: 0.1,
      kurtosis: 3.0,
      crest_factor: 4.0,
      peak_to_peak_g: 1.0,
      sampling_hz: 3200,
    },
    temperature_c: 45,
    anomaly_score: null,
    health_index: null,
    model_confidence: null,
    alert_level: null,
    ...overrides,
  };
}

const thresholds = { healthIndex: 0.6, temperatureC: 70 };

describe("AlertsPanel", () => {
  it("shows a no-active-alerts message for a normal state", () => {
    render(<AlertsPanel state={state()} thresholds={thresholds} />);
    expect(screen.getByText(/no active alerts/i)).toBeInTheDocument();
  });

  it("renders each triggered alert as a role=alert item", () => {
    render(<AlertsPanel state={state({ temperature_c: 90 })} thresholds={thresholds} />);
    expect(screen.getByRole("alert")).toHaveTextContent(/temperature/i);
  });
});
