import { useState, type JSX, type SubmitEvent } from "react";
import type { AppConfig } from "../config";

interface SettingsPanelProps {
  config: AppConfig;
  /** Persists the changes; rejects with an Error the panel shows inline. */
  onSave: (changes: Partial<AppConfig>) => Promise<void>;
}

/**
 * Edits the project-wide config (design.md DD-047). enablePhase2 switches the
 * whole system between Phase 1 only and Phase 1 + Phase 2; the services pick
 * the change up within a few seconds, without a restart.
 */
function sameConfig(a: AppConfig, b: AppConfig): boolean {
  return (
    a.enablePhase2 === b.enablePhase2 &&
    a.publishIntervalSeconds === b.publishIntervalSeconds &&
    a.alertHealthIndex === b.alertHealthIndex &&
    a.alertTemperatureC === b.alertTemperatureC
  );
}

export function SettingsPanel({ config, onSave }: SettingsPanelProps): JSX.Element {
  const [draft, setDraft] = useState<AppConfig>(config);
  const [base, setBase] = useState<AppConfig>(config);
  const [status, setStatus] = useState<{
    kind: "idle" | "saving" | "saved" | "error";
    message?: string | undefined;
  }>({
    kind: "idle",
  });

  // Follow changes made elsewhere (another browser, `make phase2-on`), but
  // only while there are no unsaved edits, so a background poll never
  // overwrites what the user is typing. Adjusting state during render, per
  // https://react.dev/learn/you-might-not-need-an-effect.
  if (!sameConfig(config, base)) {
    setBase(config);
    if (sameConfig(draft, base)) setDraft(config);
  }

  async function handleSubmit(event: SubmitEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setStatus({ kind: "saving" });
    try {
      await onSave(draft);
      setStatus({
        kind: "saved",
        message:
          draft.enablePhase2 === base.enablePhase2
            ? undefined
            : "Running services switch within a few seconds. Run `make up` to start or stop the Phase 2 containers (the copilot).",
      });
    } catch (err) {
      setStatus({ kind: "error", message: err instanceof Error ? err.message : "Unknown error" });
    }
  }

  function setNumber(key: keyof Omit<AppConfig, "enablePhase2">, value: string): void {
    setDraft((current) => ({ ...current, [key]: Number(value) }));
  }

  return (
    <section aria-label="Settings">
      <h3>Settings</h3>
      <form onSubmit={(event) => void handleSubmit(event)}>
        <label>
          <input
            type="checkbox"
            checked={draft.enablePhase2}
            onChange={(event) => {
              setDraft((current) => ({ ...current, enablePhase2: event.target.checked }));
            }}
          />
          Enable Phase 2 (ML anomaly detection, health index, NL copilot)
        </label>
        <label>
          Publish interval (s)
          <input
            type="number"
            min={0.5}
            max={3600}
            step={0.5}
            value={draft.publishIntervalSeconds}
            onChange={(event) => {
              setNumber("publishIntervalSeconds", event.target.value);
            }}
          />
        </label>
        <label>
          Temperature alert threshold (°C)
          <input
            type="number"
            min={-40}
            max={150}
            step={1}
            value={draft.alertTemperatureC}
            onChange={(event) => {
              setNumber("alertTemperatureC", event.target.value);
            }}
          />
        </label>
        {draft.enablePhase2 && (
          <label>
            Health index alert threshold
            <input
              type="number"
              min={0}
              max={1}
              step={0.05}
              value={draft.alertHealthIndex}
              onChange={(event) => {
                setNumber("alertHealthIndex", event.target.value);
              }}
            />
          </label>
        )}
        <button type="submit" disabled={status.kind === "saving"}>
          Save settings
        </button>
        {status.kind === "saved" && (
          <p>Settings saved.{status.message !== undefined && ` ${status.message}`}</p>
        )}
        {status.kind === "error" && <p role="alert">Could not save settings: {status.message}</p>}
      </form>
    </section>
  );
}
