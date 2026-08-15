// Mirrors `services/api/src/api/main.py`'s `StateResponse`/`VibrationFeaturesResponse`
// (design.md §6.0, DD-026 duplication rationale) — no shared package between the
// TypeScript and Python sides, so this shape must be kept in sync by hand.
export interface VibrationFeatures {
  rms_g: number;
  kurtosis: number;
  crest_factor: number;
  peak_to_peak_g: number;
  sampling_hz: number;
}

export interface DigitalTwinState {
  asset_id: string;
  timestamp: string;
  vibration: VibrationFeatures;
  temperature_c: number;
  anomaly_score: number | null;
  health_index: number | null;
  model_confidence: string | null;
  alert_level: string | null;
}

export class NoStateError extends Error {
  constructor() {
    super("No state recorded yet for this asset");
    this.name = "NoStateError";
  }
}

const API_URL = import.meta.env.VITE_API_URL;

export async function fetchCurrentState(): Promise<DigitalTwinState> {
  const response = await fetch(`${API_URL}/state/current`);

  if (response.status === 404) {
    throw new NoStateError();
  }
  if (!response.ok) {
    throw new Error(`Failed to fetch current state: HTTP ${String(response.status)}`);
  }

  return (await response.json()) as DigitalTwinState;
}

// api's Query(default=100, ge=1, le=1000) — see services/api/src/api/main.py.
const MAX_HISTORY_LIMIT = 1000;

/**
 * Fetches up to `limit` most-recent state objects (api returns most-recent-first).
 * A 404 (no data recorded yet) is treated the same as an empty history rather
 * than an error — the dashboard's trend charts render an empty state either way.
 */
export async function fetchStateHistory(limit: number): Promise<DigitalTwinState[]> {
  const cappedLimit = Math.min(limit, MAX_HISTORY_LIMIT);
  const response = await fetch(`${API_URL}/state/history?limit=${String(cappedLimit)}`);

  if (response.status === 404) {
    return [];
  }
  if (!response.ok) {
    throw new Error(`Failed to fetch state history: HTTP ${String(response.status)}`);
  }

  return (await response.json()) as DigitalTwinState[];
}
