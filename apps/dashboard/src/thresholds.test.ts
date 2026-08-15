import { describe, expect, it } from "vitest";
import { evaluateAlerts } from "./thresholds";
import type { DigitalTwinState } from "./api";

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

describe("evaluateAlerts", () => {
  it("returns no alerts for a normal reading", () => {
    expect(evaluateAlerts(state(), thresholds)).toEqual([]);
  });

  it("flags a warning when health index is below threshold but above 75% of it", () => {
    const alerts = evaluateAlerts(state({ health_index: 0.5 }), thresholds);
    expect(alerts).toHaveLength(1);
    expect(alerts[0]).toMatchObject({ level: "warning" });
  });

  it("flags critical when health index is below 75% of the threshold", () => {
    const alerts = evaluateAlerts(state({ health_index: 0.3 }), thresholds);
    expect(alerts[0]).toMatchObject({ level: "critical" });
  });

  it("does not flag anything when health index is null (not yet available)", () => {
    expect(evaluateAlerts(state({ health_index: null }), thresholds)).toEqual([]);
  });

  it("flags high temperature", () => {
    const alerts = evaluateAlerts(state({ temperature_c: 90 }), thresholds);
    expect(alerts.some((a) => a.message.includes("Temperature"))).toBe(true);
  });

  it("surfaces a non-normal model-reported alert_level", () => {
    const alerts = evaluateAlerts(state({ alert_level: "critical" }), thresholds);
    expect(alerts.some((a) => a.message.includes("Model-reported"))).toBe(true);
    expect(alerts.find((a) => a.message.includes("Model-reported"))?.level).toBe("critical");
  });

  it("does not flag a normal model-reported alert_level", () => {
    const alerts = evaluateAlerts(state({ alert_level: "normal" }), thresholds);
    expect(alerts.some((a) => a.message.includes("Model-reported"))).toBe(false);
  });

  it("can return multiple simultaneous alerts", () => {
    const alerts = evaluateAlerts(
      state({ health_index: 0.2, temperature_c: 95, alert_level: "critical" }),
      thresholds,
    );
    expect(alerts).toHaveLength(3);
  });
});
