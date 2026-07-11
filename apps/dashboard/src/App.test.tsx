import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "./App";
import { fetchCurrentState, NoStateError } from "./api";

vi.mock("./api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("./api")>();
  return { ...actual, fetchCurrentState: vi.fn() };
});

const mockedFetchCurrentState = vi.mocked(fetchCurrentState);

describe("App", () => {
  beforeEach(() => {
    mockedFetchCurrentState.mockReset();
  });

  it("shows a loading message before the first response", () => {
    // eslint-disable-next-line @typescript-eslint/no-empty-function -- intentionally never resolves
    mockedFetchCurrentState.mockReturnValue(new Promise(() => {}));

    render(<App />);

    expect(screen.getByText(/loading current machine state/i)).toBeInTheDocument();
  });

  it("renders the current state once loaded", async () => {
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

    render(<App />);

    expect(await screen.findByRole("heading", { name: "motor_01" })).toBeInTheDocument();
    expect(screen.getByText("0.42 g")).toBeInTheDocument();
    expect(screen.getByText(/anomaly detection isn.t available yet/i)).toBeInTheDocument();
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
});
