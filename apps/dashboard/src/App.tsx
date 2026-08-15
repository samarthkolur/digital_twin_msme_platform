import { useEffect, useState, type JSX } from "react";
import { fetchCurrentState, fetchStateHistory, NoStateError, type DigitalTwinState } from "./api";
import { HealthGauge } from "./components/HealthGauge";
import { TrendChart } from "./components/TrendChart";
import { AlertsPanel } from "./components/AlertsPanel";
import { HistoryLog } from "./components/HistoryLog";
import { RoiEstimator } from "./components/RoiEstimator";
import {
  DEFAULT_HEALTH_INDEX_ALERT_THRESHOLD,
  DEFAULT_TEMPERATURE_ALERT_THRESHOLD_C,
} from "./thresholds";

// Matches the edge service's default PUBLISH_INTERVAL_SECONDS (design.md §17).
const POLL_INTERVAL_MS = 5000;
// api's GET /state/history caps at 1000 rows (services/api/src/api/main.py
// Query(le=1000)) — this is the largest window both the trend charts and the
// historical log can show without api gaining pagination/time-range support.
const HISTORY_LIMIT = 1000;

type LoadState =
  | { status: "loading" }
  | { status: "no-data" }
  | { status: "error"; message: string }
  | { status: "ready"; state: DigitalTwinState; history: DigitalTwinState[] };

export function App(): JSX.Element {
  const [load, setLoad] = useState<LoadState>({ status: "loading" });

  useEffect(() => {
    let cancelled = false;

    async function poll(): Promise<void> {
      try {
        const [state, history] = await Promise.all([
          fetchCurrentState(),
          fetchStateHistory(HISTORY_LIMIT),
        ]);
        if (!cancelled) setLoad({ status: "ready", state, history });
      } catch (err) {
        if (cancelled) return;
        if (err instanceof NoStateError) {
          setLoad({ status: "no-data" });
        } else {
          setLoad({
            status: "error",
            message: err instanceof Error ? err.message : "Unknown error",
          });
        }
      }
    }

    void poll();
    const intervalId = setInterval(() => void poll(), POLL_INTERVAL_MS);
    return () => {
      cancelled = true;
      clearInterval(intervalId);
    };
  }, []);

  return (
    <main>
      <h1>Digital Cousin</h1>
      {load.status === "loading" && <p>Loading current machine state…</p>}
      {load.status === "no-data" && <p>No sensor data recorded yet.</p>}
      {load.status === "error" && <p role="alert">Could not reach the API: {load.message}</p>}
      {load.status === "ready" && (
        <>
          <section aria-label="Current state">
            <h2>{load.state.asset_id}</h2>
            <p>Last updated: {load.state.timestamp}</p>
            <dl>
              <dt>Vibration RMS</dt>
              <dd>{load.state.vibration.rms_g} g</dd>
              <dt>Kurtosis</dt>
              <dd>{load.state.vibration.kurtosis}</dd>
              <dt>Crest factor</dt>
              <dd>{load.state.vibration.crest_factor}</dd>
              <dt>Peak-to-peak</dt>
              <dd>{load.state.vibration.peak_to_peak_g} g</dd>
              <dt>Temperature</dt>
              <dd>{load.state.temperature_c} °C</dd>
            </dl>
            {load.state.health_index === null && (
              <p>
                Anomaly detection isn&apos;t available yet — the ML pipeline (Phase 4) hasn&apos;t
                run.
              </p>
            )}
          </section>

          <HealthGauge healthIndex={load.state.health_index} />

          <TrendChart
            label="Vibration RMS"
            unit="g"
            points={[...load.history].reverse().map((s) => s.vibration.rms_g)}
          />
          <TrendChart
            label="Temperature"
            unit="°C"
            points={[...load.history].reverse().map((s) => s.temperature_c)}
          />

          <AlertsPanel
            state={load.state}
            thresholds={{
              healthIndex: DEFAULT_HEALTH_INDEX_ALERT_THRESHOLD,
              temperatureC: DEFAULT_TEMPERATURE_ALERT_THRESHOLD_C,
            }}
          />

          <HistoryLog history={load.history} />
        </>
      )}

      <RoiEstimator />
    </main>
  );
}
