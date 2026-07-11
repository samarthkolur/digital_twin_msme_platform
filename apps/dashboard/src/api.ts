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
