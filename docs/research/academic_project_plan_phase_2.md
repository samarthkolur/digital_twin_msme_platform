# Academic Project Plan — Phase 2

## Digital Cousin: A Low-Cost Agentic Digital Twin Platform for MSME Legacy Machine Monitoring

### Phase 2 — AI-Enabled Digital Cousin and Cognitive Decision Support

**Project Type:** Final Year Major Project / Capstone Research Project
**Domain:** Internet of Things (IoT), Edge AI, Cyber-Physical Systems, Natural Language Interfaces
**Academic Target:** Project Guide Review, Evaluation Committee, and Conference/Journal Publication
**Document status:** Revision 2 — corrected against `design.md` on 2026-10-08. See the revision note below.

---

### Revision note

Revision 1 of this plan contained statements that did not match the implemented system, including
two that overclaimed capability and two that understated completed work. This revision corrects
them. Changes affecting Phase 2:

| #   | Severity | Revision 1 claimed                                                                                       | Corrected to                                                                                                                                                                                                                      |
| --- | -------- | -------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | High     | Remaining-useful-life regression was absent from the objectives, the metrics table, and the state object | RUL is an **implemented, measured Phase 2 component** (`design.md` DD-040) with its own objective (§1.5), its own metrics row, and its field in the state contract                                                                |
| 2   | High     | "Downsampling pipeline: resample 12/48 kHz bench data to 3,200 Hz"                                       | **No such pipeline exists.** The CWRU-to-edge sampling-rate difference is an open, documented domain gap (`design.md` DD-039), stated here as a limitation rather than a solved component                                         |
| 3   | High     | "Held-out CWRU Test F1-Score ≥ 0.80 / ≥ 0.85"                                                            | The reported F1 scores are **self-evaluated, not computed on a disjoint held-out split** (`design.md` §26). Stated honestly, with the genuine held-out evaluation (RUL, by-file split) identified as the only one in the pipeline |
| 4   | High     | Status: "Real CWRU/IMS Calibration — Code Ready; Dataset Pending"                                        | Both datasets are **downloaded and training**: 64 real CWRU `.mat` files (~187 MB) and the full IMS run-to-failure archive (~9 GB extracted)                                                                                      |
| 5   | Medium   | Status: "ML Codebase — Implemented with ONNX Export & Synthetic Run"                                     | Real dual-dataset training has been executed with **real measured results**; the synthetic path is an explicit opt-in for pipeline development only                                                                               |
| 6   | Low      | Model size target "≤ 5 MB (TFLite)"                                                                      | **ONNX** — DD-031 superseded the original TFLite target                                                                                                                                                                           |

---

## 0. Note on phase terminology

This document uses a **two-stage** academic narrative. The engineering source of truth, `design.md`
§10, uses a **six-phase** delivery plan. The mapping is:

| This document                                             | `design.md` §10 phases                                                               | Months |
| --------------------------------------------------------- | ------------------------------------------------------------------------------------ | ------ |
| **Phase 1** — Edge Monitoring & Digital-Shadow Foundation | Phase 1 (research & setup), Phase 2 (IoT data pipeline), Phase 3 (digital twin core) | M1–M4  |
| **Phase 2** — AI-Enabled Digital Cousin                   | Phase 4 (ML pipeline), Phase 5 (copilot & integration), part of Phase 6 (testing)    | M4–M8  |

**Important:** "Phase 2" in `design.md` means the IoT data pipeline (M2–M3), already complete.
"Phase 2" in this document means the ML and copilot work.

---

## 1. Phase 2 Academic Objectives

1. **Two-stage machine learning anomaly detection.** Formulate and train an edge-optimized
   two-stage pipeline combining:
   - a statistical baseline (_Isolation Forest_) trained on tabular vibration features for rapid,
     low-complexity outlier partitioning;
   - a deep neural feature reconstructor (_1D convolutional autoencoder_) operating on raw
     vibration windows to capture non-linear, incipient bearing degradation signatures.
2. **Edge-feasible model compression and unified runtime.** Export trained models to Open Neural
   Network Exchange (ONNX) format, enabling low-latency inference on embedded ARM architecture via
   `onnxruntime` under strict compute budgets.
3. **Decoupled uncertainty quantification (out-of-distribution detection).** Implement a
   lightweight, statistical two-tailed percentile bounding mechanism that flags out-of-distribution
   sensor readings, decoupling model confidence from anomaly score.
4. **Scalar health index formulation.** Engineer a calibrated, continuous health index metric
   (HI ∈ [0.0, 1.0]) normalizing multi-channel reconstruction errors and statistical anomalies
   relative to a healthy baseline signature.
5. **Remaining-useful-life (RUL) regression.** Train a deliberately minimal regressor (`Ridge`) over
   the same four statistical features the Isolation Forest already computes, on real run-to-failure
   data, producing a continuous life-fraction-remaining estimate at effectively zero additional
   edge inference cost. _(New in Revision 2 — this objective was implemented but omitted from
   Revision 1.)_
6. **Retrieval-augmented small language model (SLM) copilot.** Deploy an edge-hosted, 4-bit
   quantized small language model (TinyLlama-1.1B Q4_K_M via `llama.cpp`) operating as an
   interactive copilot, architecturally constrained to answer operator queries solely on the basis
   of retrieved state telemetry.
7. **SensorRAG faithfulness evaluation protocol.** Pioneer and execute a benchmarking methodology
   quantifying numeric diagnostic claim grounding, hallucination refusal rates, and deterministic
   fallback enforcement over structured telemetry contexts.
8. **Economic decision-support module.** Integrate an operational return-on-investment and
   downtime-loss estimator translating anomaly severity into projected cost avoidance.

---

## 2. Phase 2 Research & Engineering Methodology

```
+------------------------------------------------------------------------+
|                 OFFLINE TRAINING & MODEL OPTIMIZATION                  |
|   Workstation / CI Environment (NOT the Raspberry Pi)                 |
|                                                                        |
|   Benchmark datasets (both real, downloaded, wired into the pipeline): |
|     - CWRU Bearing Dataset: 64 real .mat files, ~187 MB, 12 kHz        |
|         drive-end fault data + normal baseline                         |
|     - IMS Bearing Dataset: full run-to-failure archive, ~9 GB          |
|         extracted, 3 test runs, 20 kHz                                 |
|                                                                        |
|   Each dataset trains its own designed role -- they are NOT            |
|   interchangeable and are NOT cross-fed:                               |
|     - CWRU  -> Isolation Forest + 1D conv autoencoder                  |
|     - IMS   -> remaining-useful-life Ridge regressor                   |
|                                                                        |
|   Models:                                                             |
|     - Model 1: Isolation Forest (RMS, kurtosis, crest factor, P2P)     |
|     - Model 2: 1D conv autoencoder (raw 64-sample vibration windows)   |
|     - Model 3: Ridge RUL regressor (same 4 features as Model 1)        |
|   Calibration: 30-min normal-operation baseline on the pilot asset     |
|     (PENDING -- see limitations)                                       |
|   Artifact export: skl2onnx + PyTorch ONNX Dynamo -> ONNX runtime      |
+------------------------------------------------------------------------+
                       | ONNX models + manifest.json
+------------------------------------------------------------------------+
|                  PHASE 2: EMBEDDED EDGE INFERENCE ENGINE               |
|   Raspberry Pi 4 runtime (onnxruntime + Python)                       |
|                                                                        |
|   1. Anomaly inference:                                               |
|      - raw window -> 1D conv autoencoder -> reconstruction error      |
|      - extracted features -> Isolation Forest -> decision score       |
|      - extracted features -> Ridge -> life fraction remaining         |
|                                                                        |
|   2. Uncertainty & health formulation:                                |
|      - OOD evaluator: feature vector vs [P_0.5, P_99.5] bounds        |
|      - low-confidence flag asserted if OOD detected                   |
|      - health index = weighted combination of reconstruction error    |
|          and Isolation Forest score (default 50/50)                   |
|      - populates: anomaly_score, health_index, model_confidence,      |
|          alert_level, remaining_useful_life                            |
+------------------------------------------------------------------------+
                       | Synchronized state injection
+------------------------------------------------------------------------+
|             PHASE 2: COGNITIVE COPILOT & SENSORRAG BENCHMARK           |
|                                                                        |
|   1. Telemetry retrieval & context construction:                      |
|      - fetch last N = 10 state vectors from the local REST API        |
|      - validate temporal freshness (reject if delta_t > 300 s) and    |
|          OOD status                                                    |
|                                                                        |
|   2. Constrained copilot execution:                                   |
|      - TinyLlama-1.1B Q4_K_M via llama.cpp (~700 MB RAM)              |
|      - system prompt enforces zero-hallucination constraint           |
|      - deterministic rule-based fallback on missing/stale telemetry    |
|                                                                        |
|   3. SensorRAG faithfulness benchmark:                                |
|      - held-out query suite across nominal, anomalous & fault states  |
|      - numeric extraction verifying all claims against retrieved state|
|      - verification of 100% fallback trigger under telemetry denial    |
+------------------------------------------------------------------------+
```

### Detailed methodological breakdown

**Two-stage anomaly detection pipeline.**

1. _Stage 1 (statistical partitioning)._ An Isolation Forest isolates outliers across the
   multidimensional kinematic feature space with low computational overhead. The contamination
   parameter currently remains at the scikit-learn default and has not been tuned.
2. _Stage 2 (deep latent representation)._ A 1D convolutional autoencoder learns temporal-spatial
   correlations in vibration waveforms, minimizing reconstruction loss
   L_recon(x, x̂) = (1/M) · Σ (x_j − x̂_j)². High reconstruction loss indicates deviation from normal
   cyclic rotation without requiring explicit anomalous training labels. The window length is
   **64 samples**, matching the edge acquisition burst size exactly, so the exported model consumes
   the edge sampling output directly without a buffering redesign.

**Remaining-useful-life regression.** A `Ridge` linear regressor over the same four statistical
features — deliberately a linear model rather than a neural network, so the edge can evaluate it on
the feature vector already computed per reading at effectively no extra cost. The exported
`rul.onnx` artifact is **252 bytes**. Training uses real IMS run-to-failure data: each snapshot's
position in its run's chronological file list becomes a 1.0 → 0.0 life-fraction-remaining proxy
target, split **by file** (not by window) into a genuine held-out test set. This is the only
genuinely held-out evaluation in the pipeline.

**Lightweight out-of-distribution bounding.** To prevent overconfident predictions when machines
enter unprecedented regimes (structural resonance, sensor dislodgement), empirical bounds are fitted
during calibration:

> OOD is asserted if ∃ feature _f_k_ such that _f_k_ < P₀.₅(_f_k_) or _f_k_ > P₉₉.₅(_f_k_)

This is a symmetric two-tailed 99% interval, not a one-sided upper bound — an anomalously _low_
value is flagged too. When asserted, the system sets `model_confidence = "low"` rather than
suppressing the prediction, ensuring operators are notified of uncertain readings instead of
receiving a false-normal.

**On-device small language model architecture.**

- _Runtime._ `llama.cpp` with 4-bit medium quantization (Q4_K_M), requiring ~700 MB RAM and
  achieving 1–3 tokens/second on ARM Cortex-A72.
- _Context window._ Strictly injected with serialized JSON telemetry from the past N = 10 states.
- _Fallback policy._ If sensor data is absent, stale (Δt > 300 s), or marked OOD, the engine
  automatically bypasses the LLM and emits a deterministic rule-based response.

**SensorRAG faithfulness evaluation methodology.** Conventional RAG benchmarks (RAGAs, FaithBench)
measure unstructured textual overlap. SensorRAG evaluates **numeric telemetry grounding**, passing
controlled synthetic and historical states through the copilot to evaluate:

1. _Numerical truthfulness rate._ Fraction of generated numbers that directly match contextual JSON
   attributes. Any numeric claim not traceable to retrieved context counts as a hallucination,
   regardless of whether it happens to be plausible.
2. _Context adherence / refusal rate._ Frequency of correct refusal or fallback when telemetry is
   withheld or degraded (target 100%).

---

## 3. Known methodological limitations

These are stated explicitly rather than deferred. Each is tracked in `design.md`.

1. **The reported F1 scores are self-evaluated, not held-out.** The normal-class windows used to fit
   the anomaly-score threshold are the same windows included in the F1 calculation (`design.md`
   §26). A proper fix means holding out a stratified ~20% of windows before any threshold or OOD
   bounds fitting, then scoring F1 only on that slice. This is mechanically straightforward now that
   real CWRU data exists to split, and is an open task. The RUL regressor's by-file split is the
   pattern to follow.
2. **A CWRU-to-edge sampling-rate domain gap exists and is unresolved.** CWRU is recorded at 12 kHz;
   the edge acquires at 800 Hz. **No resampling or downsampling stage is implemented.** This is a
   real limitation of transferring CWRU-trained model performance to the pilot asset and must not be
   presented as solved (`design.md` DD-039).
3. **RUL predictive power is modest and reported as such.** Held-out MAE = 0.247, R² = 0.187. A
   life-fraction proxy derived from four statistical features, via a linear model, on real noisy
   accelerometer data across a highly non-linear degradation curve, is a hard problem. These numbers
   are reported as measured rather than tuned or selected to look better, and are not claimed as
   production-grade RUL.
4. **Health-index calibration is not yet sourced from a real machine.** §6.3's intended source is a
   30-minute normal-operation recording from the pilot asset, which does not yet exist. Calibration
   currently derives from whichever dataset trained the anomaly models. IMS early-life windows are
   deliberately **not** cross-fed for calibration, because doing so would compound the rate mismatch
   in item 2 with a second unvalidated assumption (`design.md` DD-040).
5. **No real LLM inference has been performed.** The copilot's retrieval, context-validity, prompt
   construction, and fallback paths are unit-tested and verified live, and the LLM call sits behind
   an injectable client interface. But no TinyLlama weights have been downloaded and no API key is
   configured, so the SensorRAG numbers obtainable today are measured against fake clients, not a
   real faithfulness measurement.
6. **Inference latency and peak memory have not been measured on a Raspberry Pi.** The targets below
   are design budgets, not observations.

---

## 4. Phase 2 Target Metrics and Measured Results

| Subsystem                              | Evaluation metric                                 | Target                                   | Measured                                                        |
| -------------------------------------- | ------------------------------------------------- | ---------------------------------------- | --------------------------------------------------------------- |
| Statistical anomaly (Isolation Forest) | F1-score on CWRU                                  | ≥ 0.80                                   | **0.908** — self-evaluated, not a held-out split (limitation 1) |
| Deep anomaly (1D conv autoencoder)     | F1-score on CWRU                                  | ≥ 0.85                                   | **0.906** — same caveat                                         |
| RUL regression                         | MAE / R² on a real, file-level held-out IMS split | No formal target set in the original PRD | **MAE = 0.247, R² = 0.187** — genuinely held-out                |
| Model footprint                        | Exported artifact size                            | ≤ 5 MB (ONNX, per DD-031)                | Isolation Forest < 1 MB; `rul.onnx` 252 bytes                   |
| Edge compute footprint                 | Peak memory consumption (Pi 4)                    | ≤ 1.65 GB of 4 GB available              | Not yet measured on hardware                                    |
| Inference efficiency                   | Single-window edge latency                        | ≤ 100 ms on ARM Cortex-A72               | Not yet measured on hardware                                    |
| Uncertainty quantification             | OOD flag recall on perturbed data                 | ≥ 0.90                                   | Not yet measured                                                |
| Copilot responsiveness                 | Local query inference latency                     | 5–15 s per diagnostic query              | Not yet measured (no weights)                                   |
| SensorRAG faithfulness                 | Grounded numerical accuracy                       | ≥ 90% on 50 ground-truth scenarios       | Harness built; measured only against injected fake LLM clients  |
| Safety invariance                      | Fallback trigger rate on stale data               | 100% deterministic rule enforcement      | Verified live for the non-LLM path                              |

---

## 5. Architectural Evolution: How Phase 2 Extends Phase 1

The transition represents a shift from a passive **digital shadow** to an active, cognitive
**Digital Cousin**.

| Aspect                | Phase 1: digital-shadow foundation                                             | Phase 2: cognitive extension                                                                                                                           |
| --------------------- | ------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Data flow             | Unidirectional (physical → cyber); mirrors physical state passively            | Bidirectional and cognitive (physical → cyber → insights → human decision support loop)                                                                |
| Health assessment     | Static threshold comparisons (health index 0.6, temperature 70 °C placeholder) | Multi-dimensional representation learning (Isolation Forest + 1D conv autoencoder) detecting micro-wear before thermal rise                            |
| Prognostics           | None                                                                           | Continuous remaining-useful-life estimate from a run-to-failure-trained regressor                                                                      |
| Uncertainty handling  | None; assumes raw measurements are always valid and representative             | Statistical OOD detection decoupling prediction from confidence, to avert false-negative operational safety failures                                   |
| User interaction      | Graphical inspection (interpreting RMS and kurtosis time-series plots)         | Plain-language dialogue via a quantized SLM copilot, explaining machine health directly to shop-floor workers                                          |
| State object contract | Populates telemetry fields; ML attributes remain `null`                        | Activates embedded ONNX models to populate `anomaly_score`, `health_index`, `model_confidence`, `alert_level`, and `remaining_useful_life` dynamically |

### Specific technical continuities and expansions

1. **Contract integrity via the digital twin state schema.** Phase 1 establishes the canonical JSON
   schema. Phase 2 populates the dormant machine-learning attributes without altering database
   tables, REST API contracts, or dashboard rendering endpoints. This is the strongest structural
   argument for the two-stage split.
2. **From reaction to incipient warning.** Phase 1 alerts only when vibration energy crosses gross
   safety margins, often indicating advanced damage. Phase 2 uses latent autoencoder reconstruction
   error to identify subsurface bearing degradation earlier, and adds an explicit life-fraction
   estimate rather than a binary alert.
3. **Democratizing diagnostics.** Phase 1 requires an experienced maintenance engineer to analyze
   kurtosis elevations. Phase 2 allows a junior operator to ask _"Is the motor vibrating normally?"_
   and receive a verified, telemetry-grounded explanation.

---

## 6. Overall Research Contributions

1. **The Digital Cousin architectural paradigm.** Formulates, implements, and evaluates the first
   formal definition of a "Digital Cousin" — a single-asset, edge-native,
   natural-language-accessible cyber-physical twin — demonstrating that scoped, decentralized twins
   are structurally better suited to resource-constrained manufacturing than scaled-down enterprise
   digital twins.
2. **Empirical low-cost retrofit methodology.** Delivers a verified, reproducible hardware
   interfacing protocol showing that legacy, non-connected rotary machines can be integrated into
   modern condition-monitoring architectures using sub-₹10,000 off-the-shelf components without
   mechanical modification.
3. **Edge-feasible decoupled uncertainty quantification.** Proposes a lightweight two-tailed
   percentile bounding method providing operational confidence flagging for embedded models without
   the memory and computational burdens of Bayesian neural networks or Monte Carlo dropout.
4. **SensorRAG faithfulness evaluation framework.** Establishes a structured benchmarking protocol
   evaluating the factual grounding and hallucination rate of small language models operating over
   industrial _numerical_ telemetry — a context not covered by existing text-passage RAG
   faithfulness benchmarks — providing a safety metric for LLM adoption in industrial OT
   environments.

---

## 7. Implementation Status & Academic Integrity Disclosure

Current project status as of **2026-10-08**, stated transparently:

| Component                                  | Verified status                                                                                                                                  |
| ------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| Architecture & PRD design specification    | Fully completed and formally specified                                                                                                           |
| Software repository & monorepo tooling     | Complete (Docker, pnpm workspaces, uv)                                                                                                           |
| Phase 1 software engine (edge + API)       | Implemented, unit-tested, verified live against the simulated provider                                                                           |
| Phase 1 React/Vite dashboard               | Implemented with live SVG telemetry gauges; verified in a real browser                                                                           |
| Phase 1 physical hardware hookup           | Hardware **procured** and wiring specified; physical mounting on a pilot asset **pending**                                                       |
| Phase 2 ML codebase architecture           | Implemented, with ONNX export; an opt-in synthetic path exists for pipeline development only                                                     |
| Phase 2 real CWRU / IMS training           | **Complete** — both datasets downloaded (64 CWRU `.mat` files ~187 MB; IMS archive ~9 GB extracted) and training for real, with measured results |
| Phase 2 anomaly-detection results          | **Measured** — F1 0.908 / 0.906, self-evaluated (limitation 1)                                                                                   |
| Phase 2 RUL regression                     | **Measured** — held-out MAE 0.247, R² 0.187; verified end-to-end against a live stack                                                            |
| Health-index calibration on a real machine | **Pending** — requires the pilot-asset baseline recording                                                                                        |
| Phase 2 copilot architecture               | Implemented with retrieval and fallback logic; verified live                                                                                     |
| Phase 2 local SLM weight execution         | **Pending** — architecture ready, GGUF weights not downloaded; no real LLM call has ever been made                                               |
| SensorRAG benchmarking harness             | Test suite built and passing against injected fake clients; live baseline **pending**                                                            |
| Inference latency / peak memory on Pi 4    | **Not yet measured**                                                                                                                             |

**Integrity statement.** This plan distinguishes throughout between what is implemented and
measured, what is implemented but validated only against synthetic or simulated inputs, and what
remains pending. Where a target has been exceeded, the measurement methodology and its known
weaknesses are stated alongside the number. Where a component was described in Revision 1 but does
not exist, it has been removed rather than retained as an aspiration.
