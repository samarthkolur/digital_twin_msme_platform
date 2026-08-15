import { afterEach, describe, expect, it, vi } from "vitest";
import { fetchCurrentState, fetchStateHistory, NoStateError } from "./api";

describe("fetchCurrentState", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("returns the parsed state on a successful response", async () => {
    const body = {
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
    };
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response(JSON.stringify(body), { status: 200 })),
    );

    const state = await fetchCurrentState();

    expect(state).toEqual(body);
  });

  it("throws NoStateError on a 404", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(null, { status: 404 })));

    await expect(fetchCurrentState()).rejects.toBeInstanceOf(NoStateError);
  });

  it("throws a generic error on other non-OK responses", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(null, { status: 500 })));

    await expect(fetchCurrentState()).rejects.toThrow("HTTP 500");
  });
});

describe("fetchStateHistory", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("returns the parsed history array on a successful response", async () => {
    const body = [
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
    ];
    const fetchMock = vi
      .fn()
      .mockResolvedValue(new Response(JSON.stringify(body), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    const history = await fetchStateHistory(200);

    expect(history).toEqual(body);
    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("limit=200"));
  });

  it("caps the requested limit at api's own maximum (1000)", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response("[]", { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    await fetchStateHistory(5000);

    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("limit=1000"));
  });

  it("returns an empty array on a 404 (no data recorded yet)", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(null, { status: 404 })));

    await expect(fetchStateHistory(100)).resolves.toEqual([]);
  });

  it("throws on other non-OK responses", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(null, { status: 500 })));

    await expect(fetchStateHistory(100)).rejects.toThrow("HTTP 500");
  });
});
