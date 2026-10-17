import type { DigitalTwinState } from "./api";

// Mirrors `services/config/src/appconfig/schema.py`'s AppConfig (design.md
// DD-047). No shared package between the TypeScript and Python sides, so this
// shape must be kept in sync by hand.
export type CopilotLlmMode = "local" | "api";

export interface AppConfig {
  enablePhase2: boolean;
  publishIntervalSeconds: number;
  alertHealthIndex: number;
  alertTemperatureC: number;
  alertCriticalFraction: number;
  copilotLlmMode: CopilotLlmMode;
  copilotStaleAfterSeconds: number;
  copilotContextSize: number;
}

/**
 * Used until the config service first answers, and whenever it can't be
 * reached: Phase 1 only, with the same defaults the config service seeds.
 */
export const DEFAULT_CONFIG: AppConfig = {
  enablePhase2: false,
  publishIntervalSeconds: 5,
  alertHealthIndex: 0.6,
  alertTemperatureC: 70,
  alertCriticalFraction: 0.75,
  copilotLlmMode: "local",
  copilotStaleAfterSeconds: 300,
  copilotContextSize: 10,
};

const CONFIG_URL = import.meta.env.VITE_CONFIG_URL;

export async function fetchConfig(): Promise<AppConfig> {
  const response = await fetch(`${CONFIG_URL}/config`);
  if (!response.ok) {
    throw new Error(`Failed to fetch config: HTTP ${String(response.status)}`);
  }
  return (await response.json()) as AppConfig;
}

export async function updateConfig(changes: Partial<AppConfig>): Promise<AppConfig> {
  const response = await fetch(`${CONFIG_URL}/config`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(changes),
  });
  if (!response.ok) {
    throw new Error(`Failed to save config: HTTP ${String(response.status)}`);
  }
  return (await response.json()) as AppConfig;
}

/**
 * The Phase 1 view of a state object: the ML-derived fields cleared, so a
 * reading stored while Phase 2 was on never surfaces a model output after it
 * has been turned off.
 */
export function withoutPhase2Fields(state: DigitalTwinState): DigitalTwinState {
  return {
    ...state,
    anomaly_score: null,
    health_index: null,
    model_confidence: null,
    alert_level: null,
  };
}
