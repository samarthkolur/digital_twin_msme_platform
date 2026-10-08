# Academic Project Plan — Phase 1

## Digital Cousin: A Low-Cost Agentic Digital Twin Platform for MSME Legacy Machine Monitoring

### Phase 1 — Low-Cost Edge Monitoring and Digital-Shadow Foundation

**Project Type:** Final Year Major Project / Capstone Research Project
**Domain:** Internet of Things (IoT), Edge AI, Cyber-Physical Systems, Natural Language Interfaces
**Academic Target:** Project Guide Review, Evaluation Committee, and Conference/Journal Publication
**Document status:** Revision 2 — corrected against `design.md` on 2026-10-08. See the revision note below.

---

### Revision note

Revision 1 of this plan contained several statements that did not match the implemented system. This
revision corrects them. Changes affecting Phase 1:

| #   | Revision 1 claimed                                                                      | Corrected to                                                                                                                                                                                                                 |
| --- | --------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Vibration sampled "up to 3,200 Hz ODR"; state object example showed `sampling_hz: 3200` | ADXL345 is configured at **800 Hz** (`BW_RATE` = `0x0D`) in 64-sample bursts. 3,200 Hz is the datasheet ceiling, not the implemented rate; continuous high-rate streaming is deliberately deferred (`design.md` DD-022, §24) |
| 2   | "temperature (1 Hz) and vibration kinematics (0.1–0.2 Hz)"                              | A **single 5 s publish cycle** reads both sensors in one call, so both are persisted at **0.2 Hz**. There is no separate 1 Hz temperature path                                                                               |
| 3   | State object omitted `remaining_useful_life`                                            | The canonical state object carries **`remaining_useful_life`** (`design.md` §6.0, DD-040). It is `null` in Phase 1, like the other ML fields                                                                                 |
| 4   | Dashboard "Port 5173"                                                                   | 5173 is the Vite **development** port. The production dashboard is served by nginx on **port 8080**                                                                                                                          |
| 5   | Hardware status "pending procurement"                                                   | Hardware is **procured** as of 2026-10-07; wiring is specified. Physical mounting on a pilot asset remains pending                                                                                                           |

---

## 0. Note on phase terminology

This document uses a **two-stage** academic narrative. The engineering source of truth, `design.md`
§10, uses a **six-phase** delivery plan. The two numbering schemes are not interchangeable, and the
mapping is:

| This document                                             | `design.md` §10 phases                                                               | Months |
| --------------------------------------------------------- | ------------------------------------------------------------------------------------ | ------ |
| **Phase 1** — Edge Monitoring & Digital-Shadow Foundation | Phase 1 (research & setup), Phase 2 (IoT data pipeline), Phase 3 (digital twin core) | M1–M4  |
| **Phase 2** — AI-Enabled Digital Cousin                   | Phase 4 (ML pipeline), Phase 5 (copilot & integration), part of Phase 6 (testing)    | M4–M8  |

**Important:** "Phase 2" in `design.md` means the IoT data pipeline (M2–M3), which is already
complete. "Phase 2" in this document means the ML and copilot work. When citing project state in a
review, name the scheme being used.

---

## 1. Project Overview & Research Context

### 1.1 Context and Problem Formulation

Indian Micro, Small, and Medium Enterprises (MSMEs) represent the backbone of industrial
manufacturing, yet they operate at approximately 18% of the productivity of large-scale enterprises,
with an average digital maturity index of only 2.4 out of 5.0. In brownfield manufacturing setups,
unscheduled downtime resulting from mechanical degradation in critical rotating machinery (induction
motors, centrifugal pumps, industrial blowers, compressors, and lathe drive spindles) accounts for
severe economic loss.

While state-of-the-art industrial monitoring platforms (Siemens Insights Hub, PTC ThingWorx, AWS IoT
TwinMaker) provide advanced telemetry and predictive maintenance capabilities, their adoption is
fundamentally obstructed by five structural barriers in the MSME sector:

1. **Cost barrier.** Commercial digital twin suites incur high initial capital expenditure and
   recurring software licensing fees (US$10,000+ per annum), financially prohibitive under
   constrained working capital.
2. **Brownfield barrier.** Legacy machinery lacks standardized OPC-UA interfaces, industrial
   fieldbuses, or embedded sensor networks.
3. **Skill and cognitive barrier.** Up to 72% of shop-floor operators and maintenance personnel lack
   specialized data analytics, signal processing, or SCADA interpretation training.
4. **Architectural scale mismatch.** Whole-factory, multi-node enterprise twins are computationally
   and structurally excessive for a single critical bottleneck asset.
5. **Infrastructure and connectivity constraints.** Cloud-dependent architectures face unreliable
   industrial internet connectivity, severe cloud ingress/egress latency, and heightened data
   security concerns.

### 1.2 Overarching Research Question & Objective

**Core research question.** _Can a single bottleneck rotating machine in an MSME facility be
retrofitted with a sub-₹10,000 non-invasive sensor package and monitored through an edge-native AI
pipeline and a retrieval-grounded natural-language copilot, operating completely offline with zero
software licensing overhead and requiring no specialized IT/OT personnel?_

**Primary research objective.** To conceptualize, engineer, validate, and document the **Digital
Cousin** paradigm — a single-asset, edge-native, natural-language-accessible cyber-physical digital
twin that transitions industrial machine monitoring from reactive manual inspection to proactive,
automated, and explainable health diagnostics on resource-constrained embedded platforms.

---

## 2. Phase 1 Academic Objectives

1. **Non-invasive sensor instrumentation.** Design and validate an ultra-low-cost, non-invasive
   retrofit hardware package using commercial off-the-shelf (COTS) sensors — triaxial vibration via
   ADXL345 over SPI, and surface temperature via DS18B20 over the 1-Wire protocol — requiring zero
   mechanical alteration or tapping of the host legacy machine.
2. **Deterministic edge data acquisition.** Implement an on-device sensor acquisition runtime
   capable of synchronous multi-sensor sampling, burst vibration buffering, and hardware-level
   register decoding.
3. **Statistical feature engineering.** Develop an edge-computed statistical feature extraction
   engine converting raw vibration time series into low-dimensional kinematic indicators (root mean
   square, kurtosis, crest factor, peak-to-peak amplitude).
4. **Local publish–subscribe messaging pipeline.** Establish an intra-device asynchronous messaging
   backbone via a locally hosted Mosquitto MQTT broker for reliable, decoupled inter-service
   telemetry transport.
5. **Persistence of the digital shadow.** Construct an embedded time-series storage schema using
   SQLite to maintain synchronized records of raw sensor acquisitions and historical machine states
   (`raw_readings` and `state_history`).
6. **Canonical digital twin state object definition.** Formalize the single-source-of-truth JSON
   state schema capturing synchronized mechanical indicators, establishing an immutable data
   contract across the edge, API, and presentation tiers.
7. **Offline-first visualization and threshold telemetry.** Develop an edge-hosted local REST
   service (FastAPI) and a responsive, offline-capable single-page application (React + Vite)
   providing real-time telemetry rendering, trend visualization, and deterministic threshold-based
   alerting.

---

## 3. Phase 1 Research & Engineering Methodology

```
+------------------------------------------------------------------------+
|                        PHYSICAL ASSET & SENSING                        |
|   Legacy Rotating Machine (Induction Motor / Pump / Compressor)        |
|   - ADXL345 Accelerometer   (SPI mode 3, 5 MHz, +/-16 g, full-res)     |
|       configured ODR 800 Hz; 64-sample burst per acquisition           |
|   - DS18B20 Digital Thermometer (1-Wire bus, +/-0.5 deg C accuracy)    |
+------------------------------------------------------------------------+
                       | Hardware GPIO / SPI / 1-Wire
+------------------------------------------------------------------------+
|                     PHASE 1: EDGE COMPUTING GATEWAY                    |
|   Raspberry Pi 4 (4 GB LPDDR4, Pi OS Lite 64-bit, Python 3.11)        |
|                                                                        |
|   1. Sensor Acquisition & Provider Abstraction:                        |
|      - spidev driver for multi-byte burst acceleration read            |
|      - w1-gpio kernel driver for thermal acquisition                   |
|      - SimulatedSensorProvider fallback for benchtop integration       |
|                                                                        |
|   2. Vibration Feature Extraction (per 64-sample window):              |
|      - RMS (vibrational energy)                                        |
|      - Kurtosis (impact / peakedness)                                  |
|      - Crest factor (impulsiveness)                                    |
|      - Peak-to-peak amplitude                                          |
|                                                                        |
|   3. Asynchronous Messaging & Local Persistence:                       |
|      - Local Mosquitto MQTT broker (port 1883)                         |
|      - Topic: digital-cousin/<asset_id>/raw                            |
|      - Topic: digital-cousin/<asset_id>/state                          |
|      - Embedded SQLite: raw_readings and state_history tables          |
|      - Single publish cycle every 5 s  ->  0.2 Hz for BOTH sensors     |
+------------------------------------------------------------------------+
                       | Local IPC / SQLite File Access
+------------------------------------------------------------------------+
|                  PHASE 1: APPLICATION & MONITORING LAYER               |
|                                                                        |
|   1. Local REST API (FastAPI, port 8000):                              |
|      - GET /state/current        (latest synchronized twin state)      |
|      - GET /state/history?limit=N (historical buffer, cap 1000 rows)   |
|                                                                        |
|   2. Offline-First Dashboard (React + Vite):                           |
|      - dev server port 5173; production served by nginx on port 8080   |
|      - Inline SVG health gauge and real-time telemetry polling         |
|      - Vibration and temperature polyline trend visualizations         |
|      - Configurable deterministic upper/lower threshold alerts         |
+------------------------------------------------------------------------+
```

### Detailed methodological breakdown

**Mechanical retrofit strategy.** Sensors are affixed via non-invasive industrial magnetic or
surface-clamp mounts positioned proximate to bearing housings, where mechanical vibrations couple
with minimal attenuation. The accelerometer must be rigidly coupled to the housing; a compliant
mount becomes its own resonator and corrupts the kurtosis and crest-factor features.

**Signal processing pipeline.** Vibration acceleration time-series windows _X_ = [*x*₁, *x*₂, …,
_x__N] of **N = 64** samples are captured per acquisition at an 800 Hz output data rate. The
acquisition computes the three-axis magnitude √(x² + y² + z²) per sample, then extracts:

- RMS = √( (1/N) · Σ xᵢ² )
- Kurtosis = [ (1/N) · Σ (xᵢ − x̄)⁴ ] / [ (1/N) · Σ (xᵢ − x̄)² ]²
- Crest factor = max(|xᵢ|) / RMS
- Peak-to-peak = max(xᵢ) − min(xᵢ)

_Design note._ N = 64 at 800 Hz is a deliberate, documented scoping decision (`design.md` DD-022),
not a hardware limit. Bit-banging a continuous 3,200 Hz stream reliably from Python inside an async
event loop is a real-time systems problem (buffering, jitter) that requires empirical tuning against
physical hardware. That tuning is an open task (`design.md` §24) and also gates any increase in the
Phase 2 autoencoder window length. The 64-sample burst is sufficient for first-order statistical
feature estimation of low-to-mid-frequency mechanical anomalies.

**Scope limitation (stated, not deferred).** High-frequency bearing fault signatures above 5 kHz —
which require sampling rates of 10 kHz and above — are explicitly outside the hardware scope of this
project and are declared as a limitation rather than an unmet target.

**Digital twin state formalization.** The digital shadow is structured as an immutable contract:

```json
{
  "asset_id": "motor_01",
  "timestamp": "2026-10-07T12:00:00Z",
  "vibration": {
    "rms_g": 0.42,
    "kurtosis": 3.12,
    "crest_factor": 4.15,
    "peak_to_peak_g": 2.1,
    "sampling_hz": 800
  },
  "temperature_c": 54.3,
  "anomaly_score": null,
  "health_index": null,
  "model_confidence": null,
  "alert_level": null,
  "remaining_useful_life": null
}
```

In Phase 1 all five machine-learning attributes remain explicitly `null`, providing structural
readiness for Phase 2 without requiring any schema migration. `remaining_useful_life` is part of the
canonical contract (`design.md` §6.0, DD-040) and is populated by the Phase 2 RUL regressor.

---

## 4. Phase 1 Expected Outcomes & Deliverables

1. **Validated hardware bill of materials.** Verified deployment package under ₹10,000 — actual
   prototype BOM ₹7,460 (`design.md` §6.2).
2. **Reproducible retrofit installation protocol.** Open-source engineering specification covering
   wiring, sensor pinouts, mounting guidelines, and calibration checklists.
3. **Continuous edge data ingestion system.** Operational edge daemon persisting vibration
   kinematics and surface temperature to a local SQLite store on a **single 5 s publish cycle
   (0.2 Hz)**, configurable via `PUBLISH_INTERVAL_SECONDS`.
4. **Local dashboard and REST interface.** Completely offline-functional web application rendering
   live machine status, historical trends, and deterministic threshold notifications without
   internet access.

---

## 5. Phase 1 Implementation Status (as of 2026-10-08)

| Component                                                | Verified status                                                                                                 |
| -------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| Architecture & PRD design specification                  | Fully completed and formally specified                                                                          |
| Software repository & monorepo tooling                   | Complete (Docker, pnpm workspaces, uv)                                                                          |
| Phase 1 software engine (edge + API)                     | Implemented and unit-tested; verified live end-to-end against the simulated provider                            |
| Phase 1 React/Vite dashboard                             | Implemented with live SVG telemetry gauges; verified in a real browser                                          |
| Sensor hardware procurement                              | **Complete** (2026-10-07): ADXL345 GY-291-type breakout, DS18B20 waterproof probe, Raspberry Pi 4               |
| Physical wiring specification                            | **Complete**: pin map, kernel overlays, orientation procedure, bring-up order                                   |
| Physical sensor mounting on pilot asset                  | **Pending** — pilot machine not yet secured                                                                     |
| `HardwareSensorProvider` validation against real silicon | **Pending** — register decode is written to the ADXL345 datasheet and unit-tested against a mocked SPI bus only |
| Validation against a reference accelerometer             | **Pending** — gated on the above                                                                                |

**Honest status summary.** Every Phase 1 software component is implemented and has been verified
running end-to-end, but that verification used the simulated sensor provider. No reading has yet
been taken from a physical sensor. Phase 1 cannot be declared complete until the pilot machine is
secured and `HardwareSensorProvider` is validated against a reference instrument.
