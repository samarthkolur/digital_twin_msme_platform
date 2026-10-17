import { useState, type JSX, type SubmitEvent } from "react";
import type { AppConfig, CopilotLlmMode } from "../config";

interface SettingsPanelProps {
  config: AppConfig;
  /** Persists the changes; rejects with an Error the panel shows inline. */
  onSave: (changes: Partial<AppConfig>) => Promise<void>;
}

type NumericSetting = {
  [K in keyof AppConfig]: AppConfig[K] extends number ? K : never;
}[keyof AppConfig];

/** Compares every setting, so one added later can't be silently skipped. */
function sameConfig(a: AppConfig, b: AppConfig): boolean {
  return (Object.keys(a) as (keyof AppConfig)[]).every((key) => a[key] === b[key]);
}

interface NumberFieldProps {
  label: string;
  value: number;
  min: number;
  max: number;
  step: number;
  onChange: (value: number) => void;
}

function NumberField({ label, value, min, max, step, onChange }: NumberFieldProps): JSX.Element {
  return (
    <label>
      {label}
      <input
        type="number"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(event) => {
          onChange(Number(event.target.value));
        }}
      />
    </label>
  );
}

/**
 * Edits the project-wide config (design.md DD-047). enablePhase2 switches the
 * whole system between Phase 1 only and Phase 1 + Phase 2; the services pick
 * the change up within a few seconds, without a restart. Phase 2 settings
 * are shown only while Phase 2 is enabled.
 */
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

  function setter(key: NumericSetting): (value: number) => void {
    return (value) => {
      setDraft((current) => ({ ...current, [key]: value }));
    };
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
        <NumberField
          label="Publish interval (s)"
          value={draft.publishIntervalSeconds}
          min={0.5}
          max={3600}
          step={0.5}
          onChange={setter("publishIntervalSeconds")}
        />
        <NumberField
          label="Temperature alert threshold (°C)"
          value={draft.alertTemperatureC}
          min={-40}
          max={150}
          step={1}
          onChange={setter("alertTemperatureC")}
        />
        {draft.enablePhase2 && (
          <fieldset>
            <legend>Phase 2</legend>
            <NumberField
              label="Health index alert threshold"
              value={draft.alertHealthIndex}
              min={0}
              max={1}
              step={0.05}
              onChange={setter("alertHealthIndex")}
            />
            <NumberField
              label="Critical below this fraction of the threshold"
              value={draft.alertCriticalFraction}
              min={0.05}
              max={1}
              step={0.05}
              onChange={setter("alertCriticalFraction")}
            />
            <label>
              Copilot language model
              <select
                value={draft.copilotLlmMode}
                onChange={(event) => {
                  const mode = event.target.value as CopilotLlmMode;
                  setDraft((current) => ({ ...current, copilotLlmMode: mode }));
                }}
              >
                <option value="local">Local (TinyLlama, no API key)</option>
                <option value="api">API (Anthropic/OpenAI, needs a key)</option>
              </select>
            </label>
            <NumberField
              label="Copilot: ignore readings older than (s)"
              value={draft.copilotStaleAfterSeconds}
              min={10}
              max={86400}
              step={10}
              onChange={setter("copilotStaleAfterSeconds")}
            />
            <NumberField
              label="Copilot: readings used as context"
              value={draft.copilotContextSize}
              min={1}
              max={1000}
              step={1}
              onChange={setter("copilotContextSize")}
            />
          </fieldset>
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
