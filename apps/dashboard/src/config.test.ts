import { afterEach, describe, expect, it, vi } from "vitest";
import { DEFAULT_CONFIG, fetchConfig, updateConfig, withoutPhase2Fields } from "./config";
import { askCopilot } from "./copilot";
import type { DigitalTwinState } from "./api";

function respond(status: number, body: unknown): void {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify(body), { status })));
}

describe("config client", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("fetches the config", async () => {
    respond(200, DEFAULT_CONFIG);
    await expect(fetchConfig()).resolves.toEqual(DEFAULT_CONFIG);
  });

  it("rejects on a failed fetch", async () => {
    respond(500, {});
    await expect(fetchConfig()).rejects.toThrow("HTTP 500");
  });

  it("sends a PATCH with only the changes", async () => {
    respond(200, { ...DEFAULT_CONFIG, enablePhase2: true });
    await expect(updateConfig({ enablePhase2: true })).resolves.toMatchObject({
      enablePhase2: true,
    });
    const [, init] = vi.mocked(fetch).mock.calls[0] as [string, RequestInit];
    expect(init.method).toBe("PATCH");
    expect(init.body).toBe(JSON.stringify({ enablePhase2: true }));
  });

  it("rejects an invalid update", async () => {
    respond(422, {});
    await expect(updateConfig({ alertHealthIndex: 2 })).rejects.toThrow("HTTP 422");
  });

  it("maps a copilot 503 to a Phase 2 disabled message", async () => {
    respond(503, {});
    await expect(askCopilot("q")).rejects.toThrow(/phase 2 is disabled/i);
    respond(500, {});
    await expect(askCopilot("q")).rejects.toThrow("HTTP 500");
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));
    await expect(askCopilot("q")).rejects.toThrow(/make up/);
    respond(200, { answer: "ok", used_fallback: false, context_size: 1 });
    await expect(askCopilot("q")).resolves.toMatchObject({ answer: "ok" });
  });
});

describe("withoutPhase2Fields", () => {
  it("clears only the ML-derived fields", () => {
    const state: DigitalTwinState = {
      asset_id: "motor_01",
      timestamp: "t",
      vibration: { rms_g: 1, kurtosis: 3, crest_factor: 4, peak_to_peak_g: 2, sampling_hz: 800 },
      temperature_c: 50,
      anomaly_score: 0.9,
      health_index: 0.2,
      model_confidence: "high",
      alert_level: "critical",
    };
    expect(withoutPhase2Fields(state)).toEqual({
      ...state,
      anomaly_score: null,
      health_index: null,
      model_confidence: null,
      alert_level: null,
    });
  });
});
