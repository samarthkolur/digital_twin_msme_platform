import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { HistoryLog } from "./HistoryLog";
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

describe("HistoryLog", () => {
  it("shows a no-match message for an empty history", () => {
    render(<HistoryLog history={[]} />);
    expect(screen.getByText(/no readings match/i)).toBeInTheDocument();
  });

  it("renders one row per history entry", () => {
    render(
      <HistoryLog
        history={[
          state({ timestamp: "t1", alert_level: "normal" }),
          state({ timestamp: "t2", alert_level: "warning" }),
        ]}
      />,
    );
    expect(screen.getAllByRole("row")).toHaveLength(3); // header + 2 rows
  });

  it("filters rows by the selected alert level", () => {
    render(
      <HistoryLog
        history={[
          state({ timestamp: "t1", alert_level: "normal" }),
          state({ timestamp: "t2", alert_level: "warning" }),
        ]}
      />,
    );

    fireEvent.change(screen.getByLabelText(/filter by alert level/i), {
      target: { value: "warning" },
    });

    expect(screen.getAllByRole("row")).toHaveLength(2); // header + 1 matching row
    expect(screen.getByText("t2")).toBeInTheDocument();
    expect(screen.queryByText("t1")).not.toBeInTheDocument();
  });
});
