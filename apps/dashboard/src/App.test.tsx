import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "./App";
import { fetchCurrentState, fetchStateHistory, NoStateError, type DigitalTwinState } from "./api";
import { DEFAULT_CONFIG, fetchConfig } from "./config";

vi.mock("./api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("./api")>();
  return { ...actual, fetchCurrentState: vi.fn(), fetchStateHistory: vi.fn() };
});

vi.mock("./config", async (importOriginal) => {
  const actual = await importOriginal<typeof import("./config")>();
  return { ...actual, fetchConfig: vi.fn(), updateConfig: vi.fn() };
});

const mockedFetchCurrentState = vi.mocked(fetchCurrentState);
const mockedFetchStateHistory = vi.mocked(fetchStateHistory);
const mockedFetchConfig = vi.mocked(fetchConfig);

const ML_STATE: DigitalTwinState = {
  asset_id: "motor_01",
  timestamp: "2026-07-01T09:32:15Z",
  vibration: {
    rms_g: 0.42,
    kurtosis: 3.1,
    crest_factor: 4.8,
    peak_to_peak_g: 2.1,
    sampling_hz: 3200,
  },
  temperature_c: 54.3,
  anomaly_score: 0.9,
  health_index: 0.3,
  model_confidence: "high",
  alert_level: "critical",
};

describe("App", () => {
  beforeEach(() => {
    mockedFetchCurrentState.mockReset();
    mockedFetchStateHistory.mockReset();
    mockedFetchStateHistory.mockResolvedValue([]);
    mockedFetchConfig.mockReset();
    mockedFetchConfig.mockResolvedValue({ ...DEFAULT_CONFIG, enablePhase2: true });
  });

  it("shows a loading message before the first response", () => {
    // eslint-disable-next-line @typescript-eslint/no-empty-function -- intentionally never resolves
    mockedFetchCurrentState.mockReturnValue(new Promise(() => {}));

    render(<App />);

    expect(screen.getByText(/loading current machine state/i)).toBeInTheDocument();
  });

  it("renders the current state, gauge, trends, alerts, and ROI estimator once loaded", async () => {
    mockedFetchCurrentState.mockResolvedValue({
      asset_id: "motor_01",
      timestamp: "2026-07-01T09:32:15Z",
      vibration: {
        rms_g: 0.42,
        kurtosis: 3.1,
        crest_factor: 4.8,
        peak_to_peak_g: 2.1,
        sampling_hz: 3200,
      },
      temperature_c: 54.3,
      anomaly_score: null,
      health_index: null,
      model_confidence: null,
      alert_level: null,
    });
    mockedFetchStateHistory.mockResolvedValue([
      {
        asset_id: "motor_01",
        timestamp: "2026-07-01T09:32:15Z",
        vibration: {
          rms_g: 0.42,
          kurtosis: 3.1,
          crest_factor: 4.8,
          peak_to_peak_g: 2.1,
          sampling_hz: 3200,
        },
        temperature_c: 54.3,
        anomaly_score: null,
        health_index: null,
        model_confidence: null,
        alert_level: null,
      },
    ]);

    render(<App />);

    expect(await screen.findByRole("heading", { name: "motor_01" })).toBeInTheDocument();
    expect(screen.getByText("0.42 g")).toBeInTheDocument();
    expect(screen.getByText(/anomaly detection isn.t available yet/i)).toBeInTheDocument();
    expect(screen.getByText(/health index not available yet/i)).toBeInTheDocument();
    expect(screen.getByText(/no active alerts/i)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /roi estimator/i })).toBeInTheDocument();
  });

  it("shows a message when no state has been recorded yet", async () => {
    mockedFetchCurrentState.mockRejectedValue(new NoStateError());

    render(<App />);

    expect(await screen.findByText(/no sensor data recorded yet/i)).toBeInTheDocument();
  });

  it("shows an error message on fetch failure", async () => {
    mockedFetchCurrentState.mockRejectedValue(new Error("network down"));

    render(<App />);

    expect(await screen.findByRole("alert")).toHaveTextContent("network down");
  });

  it("shows only Phase 1 views while enablePhase2 is off", async () => {
    mockedFetchConfig.mockResolvedValue(DEFAULT_CONFIG);
    mockedFetchCurrentState.mockResolvedValue(ML_STATE);
    mockedFetchStateHistory.mockResolvedValue([ML_STATE]);

    render(<App />);

    expect(await screen.findByRole("heading", { name: "motor_01" })).toBeInTheDocument();
    expect(screen.getByLabelText("Active phase")).toHaveTextContent("Phase 1 (edge monitoring)");
    expect(screen.queryByLabelText(/health index gauge/i)).not.toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: /ask the copilot/i })).not.toBeInTheDocument();
    expect(screen.queryByText(/model-reported alert level/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/health index 0.30/i)).not.toBeInTheDocument();
    expect(screen.queryByRole("columnheader", { name: /health index/i })).not.toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /settings/i })).toBeInTheDocument();
  });

  it("shows the Phase 2 views when enablePhase2 is on", async () => {
    mockedFetchCurrentState.mockResolvedValue(ML_STATE);
    mockedFetchStateHistory.mockResolvedValue([ML_STATE]);

    render(<App />);

    expect(await screen.findByText(/model-reported alert level: critical/i)).toBeInTheDocument();
    expect(screen.getByLabelText("Active phase")).toHaveTextContent("Phase 2");
    expect(screen.getByRole("heading", { name: /ask the copilot/i })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: /health index/i })).toBeInTheDocument();
  });

  it("falls back to Phase 1 and says so when the config service is unreachable", async () => {
    mockedFetchConfig.mockRejectedValue(new Error("down"));
    mockedFetchCurrentState.mockResolvedValue(ML_STATE);

    render(<App />);

    expect(await screen.findByRole("status")).toHaveTextContent(/config service unreachable/i);
    expect(screen.getByLabelText("Active phase")).toHaveTextContent("Phase 1 (edge monitoring)");
  });
});
