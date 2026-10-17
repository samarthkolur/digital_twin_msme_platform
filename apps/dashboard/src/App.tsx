import { useEffect, useState, type JSX } from "react";
import { fetchCurrentState, fetchStateHistory, NoStateError, type DigitalTwinState } from "./api";
import { HealthGauge } from "./components/HealthGauge";
import { TrendChart } from "./components/TrendChart";
import { AlertsPanel } from "./components/AlertsPanel";
import { HistoryLog } from "./components/HistoryLog";
import { RoiEstimator } from "./components/RoiEstimator";
import { SettingsPanel } from "./components/SettingsPanel";
import { CopilotPanel } from "./components/CopilotPanel";
import {
  DEFAULT_CONFIG,
  fetchConfig,
  updateConfig,
  withoutPhase2Fields,
  type AppConfig,
} from "./config";
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
  const [config, setConfig] = useState<AppConfig>(DEFAULT_CONFIG);
  const [configReachable, setConfigReachable] = useState(true);

  // Poll at the edge's publish interval, which now comes from the config
  // service (design.md DD-047); re-arms when that setting changes.
  const pollIntervalMs = config.publishIntervalSeconds * 1000;

  useEffect(() => {
    let cancelled = false;

    async function pollConfig(): Promise<void> {
      try {
        const latest = await fetchConfig();
        if (!cancelled) {
          setConfig(latest);
          setConfigReachable(true);
        }
      } catch {
        // Keep the last known config (Phase 1 defaults before the first
        // answer) rather than flipping features on and off with the network.
        if (!cancelled) setConfigReachable(false);
      }
    }

    async function poll(): Promise<void> {
      void pollConfig();
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
    const intervalId = setInterval(() => void poll(), pollIntervalMs);
    return () => {
      cancelled = true;
      clearInterval(intervalId);
    };
  }, [pollIntervalMs]);

  async function saveConfig(changes: Partial<AppConfig>): Promise<void> {
    setConfig(await updateConfig(changes));
  }

  const phase2 = config.enablePhase2;
  // In Phase 1 every view sees the state without its ML fields.
  const view = (s: DigitalTwinState): DigitalTwinState => (phase2 ? s : withoutPhase2Fields(s));

  return (
    <main>
      <h1>Digital Cousin</h1>
      <p aria-label="Active phase">
        {phase2 ? "Phase 1 + Phase 2 (AI-enabled digital cousin)" : "Phase 1 (edge monitoring)"}
      </p>
      {!configReachable && (
        <p role="status">Config service unreachable — showing the last known settings.</p>
      )}
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
            {phase2 && load.state.health_index === null && (
              <p>
                Anomaly detection isn&apos;t available yet — the ML pipeline (Phase 4) hasn&apos;t
                run.
              </p>
            )}
          </section>

          {phase2 && <HealthGauge healthIndex={load.state.health_index} />}

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
            state={view(load.state)}
            thresholds={{
              healthIndex: config.alertHealthIndex,
              temperatureC: config.alertTemperatureC,
              criticalFraction: config.alertCriticalFraction,
            }}
          />

          <HistoryLog history={load.history.map(view)} showPhase2={phase2} />
        </>
      )}

      {phase2 && <CopilotPanel />}

      <RoiEstimator />

      <SettingsPanel config={config} onSave={saveConfig} />
    </main>
  );
}
