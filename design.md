# Product Requirements Document
## Digital Cousin: A Low-Cost Agentic Digital Twin Platform for MSME Legacy Machine Monitoring

**Version 2.0 | Capstone Project | Domain: IoT, Edge AI, Natural Language Interfaces**
**Department of Computer Science & Technology, Dayananda Sagar University**

---

## 1. Executive Summary

Indian Micro, Small, and Medium Enterprises (MSMEs) operate at roughly 18% of the productivity of large enterprises, with a digital maturity score of just 2.4 out of 5 [EY India, 2023]. Enterprise-grade industrial monitoring platforms — Siemens Insights Hub, PTC ThingWorx, AWS IoT TwinMaker — solve real-time monitoring and predictive maintenance for large, digitally mature factories, but assume modern OPC-UA-compliant machinery, dedicated IT/OT staff, and five-figure annual software budgets. None of these conditions hold for a typical Indian MSME.

**Digital Cousin** is a low-cost, retrofittable digital twin platform targeting a single high-risk bottleneck machine in an MSME facility. It combines a non-invasive vibration and temperature sensor retrofit kit, an edge-deployed lightweight anomaly detection model, and a retrieval-grounded natural-language copilot interface — enabling a floor worker with no data science background to monitor and interpret machine health in real time, entirely offline.

This document defines the problem, scope, system architecture, technology stack, hardware specifications, and 8-month delivery plan.

---

## 2. Problem Statement

Indian MSMEs cannot detect machine failures before they happen. They rely on manual inspection and reactive maintenance, resulting in unplanned downtime that directly erodes productivity. Five structural barriers prevent adoption of existing industrial monitoring solutions:

- **Cost barrier**: Enterprise digital twin platforms cost $10,000+ per year in software licensing — unaffordable given India's ₹30 lakh crore MSME credit deficit [CII, 2024]. Digital Cousin targets a total hardware cost below ₹10,000 using commercially available off-the-shelf components, with zero software licensing fees.
- **Brownfield barrier**: MSMEs predominantly operate legacy, non-connected machinery with no standardized data interfaces (no OPC-UA, no Modbus). Commercial platforms require native protocol support and do not support retrofitting.
- **Skill barrier**: Up to 72% of manufacturers lack in-house IT/OT expertise to configure, calibrate, or interpret outputs from a digital twin system [Raj et al., 2020].
- **Scale barrier**: Whole-factory digital twins are computationally and financially unviable for a business monitoring one or two critical machines with no dedicated server infrastructure.
- **Policy gap**: Government schemes (ZED, SAMARTH Udyog) fund training and subsidies but do not fund physical hardware retrofitting, leaving a persistent gap between policy intent and ground-level implementation [CII, 2024].

**Core research question**: Can a single bottleneck machine in an MSME be retrofitted with a sub-₹10,000 vibration and temperature sensor kit and monitored through an edge-AI and retrieval-grounded natural-language interface, without cloud dependency, recurring licensing costs, or specialized staff?

---

## 3. Objectives

1. Design and build a non-invasive sensor retrofit kit — ADXL345/MPU6050 accelerometer (SPI mode, up to 3,200 Hz) and DS18B20 temperature sensor — for legacy machinery requiring no hardware modification to the host machine.
2. Implement an edge-deployed, two-stage anomaly detection pipeline: an Isolation Forest statistical baseline for rapid deployment, followed by a 1D convolutional autoencoder for improved sensitivity, both trained on CWRU Bearing and IMS Bearing datasets and calibrated to the pilot machine's baseline vibration signature.
3. Build a retrieval-grounded natural-language copilot, running a quantized 1B-parameter LLM (TinyLlama-1.1B, Q4_K_M quantization, ~700 MB RAM) via llama.cpp on the Raspberry Pi 4, with responses strictly constrained to retrieved sensor readings and model outputs — and an explicit "insufficient data" fallback when context is unavailable.
4. Demonstrate the "Digital Cousin" paradigm — defined as a single-asset, edge-first, natural-language-accessible digital twin — as a deployable and repeatable alternative to whole-factory digital twins for resource-constrained environments.
5. Document a generalizable retrofit protocol (bill of materials, wiring diagram, calibration procedure, and installation checklist) that can be applied to other legacy rotary machines beyond the pilot asset.
6. Produce at least one conference or journal paper submission grounded in the system architecture, retrofit protocol, or edge-AI methodology.
7. Design and execute the **SensorRAG faithfulness evaluation protocol**: a structured-telemetry hallucination benchmark that measures whether the copilot's numeric diagnostic claims are actually grounded in retrieved sensor state, and quantifies its hallucination/refusal rate when retrieval context is absent or insufficient (§6.4, §9, §15 DD-030).

---

## 4. Scope

### In Scope (8-month project)
- One pilot machine — rotary asset (motor, compressor, lathe spindle, or pump) — real hardware or controlled lab equivalent.
- Sensor retrofit kit: ADXL345 or MPU6050 (vibration, SPI mode), DS18B20 (temperature).
- Edge gateway: Raspberry Pi 4 (4 GB RAM) as the primary compute node; ESP32 as optional low-power data acquisition node.
- Anomaly detection pipeline: Isolation Forest (Phase 4, baseline); 1D convolutional autoencoder (Phase 4, primary model). Both trained on CWRU and IMS Bearing datasets, fine-tuned on collected data.
- Statistical feature extraction: RMS, kurtosis, crest factor, peak-to-peak — computed from vibration time-series sampled at up to 3,200 Hz (SPI mode). High-frequency bearing fault signatures above 5 kHz are explicitly out of scope given sensor hardware limits.
- Time-series data store: SQLite (lightweight) or InfluxDB OSS (local instance).
- Local web dashboard: offline-first, React/Vite, served from the Pi.
- LLM copilot: TinyLlama-1.1B Q4_K_M via llama.cpp (primary, fully local); API-based fallback (Anthropic or OpenAI) for optional enhanced responses when connectivity is available. Expected local inference latency: 5–15 seconds per query — acceptable for non-real-time diagnostic Q&A.
- ROI estimator: simple web form computing projected savings from reduced unplanned downtime, based on user-supplied downtime cost and maintenance cost inputs.
- Retrofit protocol documentation: BOM, wiring diagram, calibration procedure, generalizable installation checklist.

### Out of Scope
- High-frequency bearing fault signature analysis (>5 kHz) — sensor hardware does not support this; explicitly noted as a limitation.
- Current clamp / electrical monitoring — reserved for Phase 2; no literature justification in Phase 1 scope.
- Full-factory or multi-machine simulation.
- Closed-loop autonomous actuation (monitoring and decision-support only in Phase 1).
- Custom PCB fabrication.
- Multi-tenant SaaS deployment.
- Model fine-tuning of the LLM layer — the copilot uses prompt-based retrieval only, not fine-tuning.

---

## 5. Target Users

| User | Primary Need | Interaction Mode |
|---|---|---|
| Floor worker / machine operator | Know if the machine is healthy right now, without reading graphs | Natural-language copilot |
| MSME owner / plant manager | Track machine health trends and projected downtime cost savings | Dashboard + ROI estimator |
| Maintenance technician | Receive early anomaly alerts before failure, with timestamp and magnitude | Alert module + dashboard |

---

## 6. System Architecture

### 6.0 Digital Cousin State Model

The "digital twin" in this system is concretely defined as a structured state object, synchronized from physical sensor readings at configurable intervals (default: 1 second for temperature, 10-second windows for vibration features):

```json
{
  "asset_id": "motor_01",
  "timestamp": "2026-07-01T09:32:15Z",
  "vibration": {
    "rms_g": 0.42,
    "kurtosis": 3.1,
    "crest_factor": 4.8,
    "peak_to_peak_g": 2.1,
    "sampling_hz": 3200
  },
  "temperature_c": 54.3,
  "anomaly_score": 0.12,
  "health_index": 0.88,
  "model_confidence": "high",
  "alert_level": "normal"
}
```

This state object is the single source of truth for the dashboard, alert module, and copilot retrieval context. All four system layers read from it; only the Edge Layer writes to it.

### 6.1 Layer Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                         PHYSICAL LAYER                            │
│  Legacy Machine → Retrofit Sensor Kit                             │
│  ADXL345/MPU6050 (vibration, SPI up to 3,200 Hz)                 │
│  DS18B20 (temperature, 1-wire, ±0.5°C accuracy)                  │
│  Non-invasive clamp mount — no host machine modification           │
└────────────────────────────┬─────────────────────────────────────┘
                              │ SPI / 1-Wire → GPIO (RPi 4)
┌────────────────────────────▼─────────────────────────────────────┐
│                          EDGE LAYER                               │
│  Raspberry Pi 4 (4 GB RAM) — primary compute node                 │
│  • Sensor acquisition: Python + spidev / w1-gpio                  │
│  • Feature extraction: RMS, kurtosis, crest factor, peak-to-peak  │
│  • ML inference: Isolation Forest → 1D Conv Autoencoder           │
│    (TFLite runtime, model <5 MB, inference <100 ms)               │
│  • State object update (JSON → SQLite/InfluxDB)                   │
│  • MQTT broker (Mosquitto, local) for intra-device messaging      │
│  • OOD/confidence flagging before every prediction                │
└────────────────────────────┬─────────────────────────────────────┘
                              │ Local HTTP / MQTT
┌────────────────────────────▼─────────────────────────────────────┐
│                      APPLICATION LAYER                            │
│  • Offline-first React/Vite dashboard (served from Pi)            │
│  • Real-time state visualization (health index, trends, alerts)   │
│  • Alert module: threshold + ML-triggered (local push / buzzer)   │
│  • ROI estimator: web form → projected downtime savings           │
└────────────────────────────┬─────────────────────────────────────┘
                              │ Local REST API
┌────────────────────────────▼─────────────────────────────────────┐
│                       COPILOT LAYER                               │
│  TinyLlama-1.1B Q4_K_M via llama.cpp (~700 MB RAM)               │
│  • Retrieval: last N state objects from SQLite/InfluxDB           │
│  • Prompt construction: system prompt + retrieved context only     │
│  • Response: plain-language health explanation or alert rationale  │
│  • Fallback: rule-based response if confidence = low or data gap   │
│  • Optional: API-based LLM (Anthropic/OpenAI) when online         │
│  • Latency: 5–15 s local; <2 s API fallback                       │
└──────────────────────────────────────────────────────────────────┘
```

### 6.2 Hardware Module

| Component | Part | Specification | Unit Cost (approx.) |
|---|---|---|---|
| Vibration sensor | ADXL345 | SPI mode, up to 3,200 Hz ODR, ±16g range | ₹180 |
| Temperature sensor | DS18B20 | 1-Wire, –55°C to +125°C, ±0.5°C | ₹80 |
| Edge compute | Raspberry Pi 4 (4 GB) | ARM Cortex-A72, 4 GB LPDDR4 | ₹5,500 |
| MicroSD | 32 GB Class 10 | OS + data storage | ₹300 |
| Enclosure | 3D-printed/off-shelf | Non-invasive clamp mount | ₹400 |
| Power supply | 5V 3A adapter + UPS HAT | Power-loss buffering | ₹800 |
| Miscellaneous | Jumper wires, resistors | Wiring | ₹200 |
| **Total** | | | **~₹7,460** |

**Sensor sampling note**: The ADXL345 in SPI mode achieves up to 3,200 Hz output data rate. The MPU6050 via I2C with DLPF bypass achieves approximately 1 kHz. Either is sufficient for statistical feature extraction (RMS, kurtosis, crest factor) targeting low-to-mid frequency mechanical anomalies. High-frequency bearing fault signatures above 5 kHz — which require sampling rates of 10+ kHz — are explicitly out of scope and noted as a limitation.

### 6.3 Edge AI Module

**Training datasets:**
- **CWRU Bearing Dataset** (Case Western Reserve University): accelerometer data at 12,000 Hz and 48,000 Hz; inner race, outer race, and rolling element fault classes. Used for training the anomaly detection models on labeled fault signatures, downsampled to 3,200 Hz to match deployment hardware.
- **IMS Bearing Dataset** (University of Cincinnati): run-to-failure bearing data at 20,000 Hz; used for RUL regression training and health index calibration, downsampled similarly.
- **Pilot machine baseline**: 30-minute normal-operation recording collected during system installation; used for Isolation Forest normal-class calibration and autoencoder reconstruction-error threshold setting.

**Model pipeline** (`services/ml/src/ml/`, implemented this session — design.md §28 Entry 13; software complete, real-data calibration still pending §24):
1. *Isolation Forest* (`isolation_forest.py`): trained on extracted statistical features (RMS, kurtosis, crest factor, peak-to-peak, `features.py`). Contamination parameter tuned on CWRU normal-class windows once real data exists (§24) — currently sklearn's own default. Serves as the operational baseline. Model size: <1 MB.
2. *1D Convolutional Autoencoder* (`autoencoder.py`, PyTorch): trained on raw vibration windows. Window length defaults to 64 samples — matching `edge`'s actual per-`read()` burst size (DD-022's `_SAMPLE_COUNT`), not the "3,200 Hz, 1-second frame" originally envisioned here, so the exported model can consume `edge`'s real sampling output directly without a buffering redesign (see §24 for the still-pending real-time-buffering task that would unlock longer windows). Reconstruction error thresholded against pilot machine baseline. Exported to **ONNX** (DD-031, supersedes this section's original TFLite target), robust to arbitrary window lengths via a final interpolate-to-input-length step.
3. *Health index* (`health_index.py`): a normalized scalar (0.0–1.0) computed from reconstruction error and Isolation Forest anomaly score using a weighted linear combination (default 50/50), calibrated against a normal-baseline recording so that ~1.0 = normal baseline and <0.6 = alert threshold, with a configurable "standard deviations above baseline at full anomaly" sensitivity knob (default 4).
4. *Out-of-distribution (OOD) flag* (`ood.py`): if any input feature falls outside the training distribution's 0.5th/99.5th percentile band (a symmetric two-tailed 99% interval, not a one-sided upper bound — an anomalously *low* value is flagged too), the system flags the prediction as low-confidence (`model_confidence="low"`) rather than suppressing it, ensuring operators are notified of uncertain readings rather than receiving a false-normal.
5. *Orchestration* (`pipeline.py`, `run_training_pipeline`): ties the above together, plus F1 evaluation (`evaluate.py`) and a `manifest.json` artifact (model paths, window length, feature order, OOD bounds, F1 scores) that `services/edge`'s `ml_inference.py` reads to run inference — the JSON contract between the two independent services, per DD-026's precedent. Real CWRU/IMS loading (`datasets.py`) is implemented as an interface that raises a clear, actionable error when the dataset isn't present (not yet downloaded, §24); real parsing itself is unimplemented pending that download. A synthetic-data path (`synthetic.py`, opt-in via `--allow-synthetic`, never a hidden default) lets the whole pipeline — training, export, evaluation — run and be tested end-to-end today, producing placeholder (not calibrated) models.

### 6.4 Copilot Module (implemented this session — design.md §28 Entry 13)

The copilot is a retrieval-augmented generation (RAG) system with a constrained context window, now
implemented in `services/copilot/src/copilot/`: `retrieval.py` (fetches recent state objects from
`api`, degrading to an empty list rather than raising on any failure — an empty retrieval is exactly
what should trigger the fallback below), `context.py` (freshness/OOD validity check), `prompt.py`
(system prompt + structured context serialization), `fallback.py` (rule-based responses), `llm_local.py`
(TinyLlama/llama.cpp, `local-llm` extra, deferred import), `llm_api.py` (Anthropic/OpenAI via httpx),
and `service.py`'s `QueryEngine` orchestrating all of the above behind `POST /query`. Not yet exercised
against a real LLM in this session — no TinyLlama weights or API key are present (§24) — but every
non-LLM code path (retrieval failure handling, context validity, fallback selection, prompt
construction) has unit tests, and the LLM call itself is behind an injectable `LLMClient` protocol so
`QueryEngine` is fully testable with a fake client regardless.

- **Retrieval**: the last 10 state objects (covering ~10 seconds of data or ~10 historical readings, depending on query type) are serialized and injected into the prompt as structured context.
- **LLM**: TinyLlama-1.1B (Q4_K_M quantization, ~700 MB RAM) served via llama.cpp on the Pi 4. Expected throughput: 1–3 tokens/second on ARM Cortex-A72, yielding 5–15 second response latency for typical 50–100 token responses. This latency is acceptable for non-real-time diagnostic queries.
- **API fallback**: when internet connectivity is available, an API-based LLM (configurable) can substitute the local model, reducing latency to under 2 seconds.
- **System prompt constraint**: the system prompt explicitly prohibits the model from answering questions not grounded in the retrieved sensor context. If the context is empty, stale (>5 minutes old), or flagged OOD, a rule-based fallback response is returned instead of an LLM-generated answer.
- **Scope**: the copilot answers operational questions only — machine health status, anomaly explanations, recent alerts. It does not provide maintenance instructions, safety guidance, or any information outside sensor context.

**SensorRAG faithfulness evaluation protocol** (Phase 5–6, §15 DD-030): the literature survey backing this
project (`docs/research/`, see DD-030) identifies that no prior digital-twin/industrial-LLM work evaluates
whether an SLM copilot's *numeric* diagnostic claims are actually grounded in retrieved structured sensor
telemetry, as opposed to hallucinated fluently from parametric memory — a structurally harder problem than
existing text-passage RAG faithfulness benchmarks (FaithBench, RAGAs), which don't cover structured numeric
context at all. This project's own faithfulness evaluation, not yet implemented, extends the existing
"Factual accuracy" metric (§9) into a named, reusable protocol:
- A held-out query set spanning normal, elevated-anomaly, and no-data/stale-context state objects.
- Per-response grounding check: does every numeric value or health claim in the copilot's answer trace back
  to a field actually present in the retrieved state object(s)? Any numeric claim not traceable to retrieved
  context counts as a hallucination, regardless of whether it happens to be plausible.
- Explicit measurement of the refusal/fallback rate under insufficient-context conditions (target: 100%,
  matching §9's existing "Fallback trigger rate" metric — the two are the same requirement, now with a named
  evaluation methodology behind it).
- Comparable across both `COPILOT_LLM_MODE` paths (`local` TinyLlama and `api` fallback) so the offline path
  is not left unevaluated relative to the optional cloud fallback.

**Example interaction:**
- User: "Is the motor okay right now?"
- Retrieved context: health_index=0.71, kurtosis=4.8 (elevated), temperature=61°C (within normal)
- Response: "The motor's health index is 0.71, which is slightly below the normal range. Vibration kurtosis is elevated, which can indicate early-stage mechanical looseness or bearing wear. Temperature is within normal range. Consider scheduling an inspection."

### 6.5 Application / Dashboard Module (full build-out implemented this session — design.md §28 Entry 13)

- Offline-first web application (React + Vite), served from the Pi 4 via a local HTTP server. No internet connection required for any core function.
- Real-time state display: health index gauge (`components/HealthGauge.tsx`, inline SVG, no charting
  library added), vibration RMS trend and temperature trend (`components/TrendChart.tsx`, a
  dependency-free SVG polyline reused for both), active alerts (`components/AlertsPanel.tsx`, driven by
  `thresholds.ts`'s `evaluateAlerts`).
- Historical log (`components/HistoryLog.tsx`): filterable by alert level. Actually bounded by `api`'s
  existing `GET /state/history` cap of 1000 rows (~83 minutes at the default 5s publish interval), not
  a true 24h window as originally scoped here — tracked as a known gap (§26) rather than silently
  claimed as 24h; extending it needs pagination/time-range support on the `api` endpoint.
- Alert module: configurable thresholds (`thresholds.ts`, health index default 0.6 matching §6.3's
  calibration target, temperature default 70°C as an uncalibrated placeholder pending real hardware);
  the model's own `alert_level` (once Phase 4 ML inference populates it) is surfaced alongside the
  threshold checks, not in place of them. GPIO-connected buzzer is edge/hardware scope, not yet built.
- ROI estimator (`components/RoiEstimator.tsx`): operator inputs cost/hour of unplanned downtime,
  estimated annual unplanned hours, this system's own annual operating cost, and an assumed reduction
  percentage; outputs current annual downtime cost and projected annual savings. Entirely client-side,
  no backend endpoint.

---

## 7. Technology Stack

| Layer | Component | Technology | Justification |
|---|---|---|---|
| Physical | Vibration sensor | ADXL345 (SPI, 3,200 Hz) | Low cost (~₹180), SPI mode sufficient for statistical features; widely documented |
| Physical | Temperature sensor | DS18B20 (1-Wire) | ±0.5°C accuracy, direct GPIO, no ADC required |
| Edge compute | Primary gateway | Raspberry Pi 4 (4 GB) | 4 GB RAM accommodates TinyLlama + TFLite + OS simultaneously |
| Edge OS | Runtime | Raspberry Pi OS Lite + Python 3.11 | Minimal footprint; mature ecosystem for sensor interfacing |
| Data acquisition | Sensor interface | Python `spidev` (ADXL345) + `w1-gpio` (DS18B20) | Native kernel driver support; no additional hardware |
| Data store | Time-series | SQLite (primary); InfluxDB OSS (optional) | SQLite: zero config, suitable for <1 GB datasets; InfluxDB: if query complexity grows |
| ML framework | Inference | ONNX Runtime (DD-031, supersedes the originally documented TFLite) | Single runtime for both Isolation Forest (via skl2onnx) and autoencoder (via `torch.onnx.export`); avoids adding TensorFlow as a training-time-only dependency solely for TFLite conversion |
| ML training | Development | scikit-learn + PyTorch (training only, on development PC) | Models exported to ONNX for deployment (`onnxruntime` in `edge`) |
| Messaging | Intra-device | Mosquitto MQTT broker (local) | Lightweight pub/sub; standard IoT protocol; zero cloud dependency |
| Dashboard | Frontend | React + Vite | Offline-capable SPA; served locally from Pi |
| Copilot | Local LLM | TinyLlama-1.1B Q4_K_M via llama.cpp | ~700 MB RAM; 1–3 tok/s on ARM; fits RPi 4 resource budget |
| Copilot | API fallback | Configurable REST endpoint (Anthropic/OpenAI) | Optional; used when internet available; not required for core function |
| Alerts | Notification | Local dashboard + GPIO buzzer | No cloud dependency; audible alert for shop floor |

**Resource budget (Raspberry Pi 4, 4 GB RAM):**

| Process | Estimated RAM |
|---|---|
| Raspberry Pi OS Lite | ~400 MB |
| Python sensor acquisition + MQTT | ~150 MB |
| TFLite runtime + models | ~200 MB |
| SQLite + data buffer | ~100 MB |
| React dashboard (served, not rendered) | ~100 MB |
| TinyLlama-1.1B Q4_K_M (llama.cpp) | ~700 MB |
| **Total** | **~1,650 MB** |
| **Headroom on 4 GB model** | **~2,350 MB** |

The copilot runs as an on-demand process (not resident), loading and unloading from RAM on each query. This avoids continuous RAM contention with the ML inference pipeline.

### 7.6 Engineering & DevOps Tooling

Established during the Phase 1 engineering-foundation build (see §21 Development Log). Covers the
development environment, quality gates, and CI/CD — distinct from the deployed system's runtime
stack in §7.0–§7.5.

| Concern | Tool | Justification |
|---|---|---|
| Container orchestration (dev) | Docker Compose `watch` | Native sync/rebuild hot reload; no extra dev-server tooling needed on top of Docker |
| Container orchestration (prod) | Docker Compose + `docker-compose.prod.yml` override | Single compose file family; Pi deployment is a straight `-f` override, not a parallel stack |
| JS/TS package management | pnpm workspaces | Fast, disk-efficient, strict dependency resolution; workspace-native monorepo support |
| Python package management | uv (per-service `pyproject.toml` + lockfile) | Single static binary, fast resolver, PEP 735 dependency groups; no host Python installs needed |
| TypeScript | strict `tsconfig.base.json` (noUncheckedIndexedAccess, exactOptionalPropertyTypes, etc.) | Catches null/undefined and index-access bugs at compile time |
| JS/TS linting | ESLint 9 flat config + typescript-eslint strict + import-x + jsx-a11y + promise | Single modern config format; strict type-aware rules; accessibility and promise-safety coverage |
| Formatting | Prettier (JS/TS/JSON/MD/YAML) + `ruff format` (Python) | One opinionated formatter per language, wired into lint-staged and CI |
| Python lint/format | ruff (global, versioned in the toolbox image) | Replaces flake8+isort+black with one fast tool |
| Python type checking | mypy `strict`, per service | Needs each service's real dependency graph in scope, unlike ruff |
| Unused code detection (TS) | knip | Single tool covering unused deps, exports, and dead files (replaces depcheck + ts-prune + unimported) |
| Circular imports (TS) | `import-x/no-cycle` ESLint rule | No separate CLI tool needed |
| Git hooks | Husky v9 (`pre-commit`, `commit-msg`) | Hooks shell into the toolbox container, so host needs only Docker, not Node/Python |
| Lint-staged | lint-staged | Runs ESLint/Prettier/ruff only on staged files |
| Commit convention | Conventional Commits + commitlint | Enforced at `commit-msg`; changelog-friendly history |
| CI | GitHub Actions (`ci.yml`, `codeql.yml`) | ts-quality, python-quality (matrix), docker-build (matrix), compose config validation, hadolint, gitleaks, dependency audit, Trivy fs scan, CodeQL — all required |
| Secret scanning | gitleaks | Runs in CI on full git history |
| Dependency auditing | `pnpm audit` + `pip-audit` (per service) | Native-to-ecosystem, no third-party account needed |
| Container/Dockerfile scanning | Trivy (filesystem scan) + hadolint | Standard, single-binary tools; no registry push required to scan |
| Static analysis (security) | CodeQL (JS/TS + Python) | GitHub-native, free for public repos, no extra config surface |
| Coverage gates | vitest coverage thresholds (v8) + `pytest --cov-fail-under` | Native to each test runner; avoids an external coverage SaaS/token |
| Editor consistency | EditorConfig + VS Code workspace settings/recommendations | Works across contributors regardless of IDE choice |

---

## 8. Novelty and Research Contribution

Framed against the consolidated gap in the accompanying literature survey:

1. **The Digital Cousin paradigm**: a formally defined three-property characterization of a single-asset, edge-first, natural-language-accessible digital twin. This is a scoping and architectural contribution — not merely an implementation — and is directly publishable as a systems design paper arguing that partial, focused twins are more appropriate for resource-constrained deployments than scaled-down versions of enterprise platforms.

2. **Generalizable low-cost retrofit protocol**: a documented, repeatable procedure for attaching COTS vibration and temperature sensors to legacy, non-IoT rotary machinery without machine modification. The literature identifies this as a persistent gap: prior work on low-cost DTs uses simulated or protocol-compliant machinery; no published work provides a hardware-agnostic installation protocol for brownfield assets.

3. **Edge-feasible OOD confidence flagging**: a lightweight mechanism that decouples anomaly prediction from prediction reliability — flagging predictions as uncertain when input features fall outside the training distribution — without requiring Bayesian inference or cloud computation. This directly addresses the uncertainty quantification gap identified in the predictive maintenance literature.

4. **Retrieval-grounded, safety-bounded agentic copilot**: an LLM interface for low-literacy industrial users that is architecturally constrained to sensor-retrieved context, with a rule-based fallback when context is absent or stale. This differentiates from prior LLM-in-DT work (Xia et al., 2024; Wu et al., 2025), which targets expert users performing complex multi-agent plant orchestration, not floor-level diagnostic queries.

5. **SensorRAG faithfulness evaluation protocol**: the first evaluation methodology (to the surveyed literature's knowledge) for whether an SLM's diagnostic claims over *structured numeric sensor telemetry* are actually grounded in retrieved context, as opposed to hallucinated. Existing hallucination benchmarks (FaithBench, RAGAs) evaluate only text-passage retrieval; no prior industrial-LLM work (including the closest precedents — IoT-LLM's IoT-sensor RAG, ChatCNC's live-CNC RAG, BearLLM's vibration-text alignment) reports a faithfulness/hallucination-rate evaluation at all. See §6.4 and §9.

---

## 9. Evaluation Metrics

| Component | Metric | Target |
|---|---|---|
| Hardware | Sensor installation without host machine modification | Binary pass/fail per installation checklist |
| Hardware | Vibration RMS accuracy vs. reference accelerometer | Within ±10% of reference measurement |
| Hardware | Temperature accuracy vs. NIST-traceable thermometer | Within ±1°C |
| Hardware | Total hardware cost | ≤ ₹10,000 per deployment unit |
| ML — Isolation Forest | Anomaly detection F1-score on held-out CWRU test set | ≥ 0.80 |
| ML — Autoencoder | Anomaly detection F1-score on held-out CWRU test set | ≥ 0.85 |
| ML | Model size | ≤ 5 MB (TFLite) |
| ML | Inference latency on Pi 4 | ≤ 100 ms per prediction |
| ML | OOD flag recall (correctly flagging out-of-distribution inputs) | ≥ 0.90 on synthetic OOD test cases |
| Copilot | Factual accuracy: response consistent with retrieved sensor state | ≥ 90% on 50 structured test queries with ground-truth state |
| Copilot | Fallback trigger rate: rule-based response when data is missing | 100% (no LLM response without valid context) |
| Copilot | Local inference latency | ≤ 15 s per query (TinyLlama, Q4, Pi 4) |
| Copilot | SensorRAG faithfulness: numeric claims traceable to retrieved state object fields (§6.4, §15 DD-030) | 0 untraceable numeric claims across the held-out query set (target, not yet measured) |
| System | End-to-end offline operation (no internet for core function) | Binary pass/fail |
| System | Dashboard load time on local network | ≤ 3 s |
| ROI estimator | Savings projection matches manual calculation | Within ±5% |
| Research | Retrofit protocol reproducibility: second installation by a different team member | Binary pass/fail |

---

## 10. Delivery Plan (8-Month Timeline)

| Phase | Duration | Key Deliverables | Capstone Milestone |
|---|---|---|---|
| Phase 1: Research & setup | M1–M2 | Literature survey finalized, hardware procured (ADXL345/DS18B20/RPi 4), development environment configured, MQTT broker running, pilot machine identified | Review-0 (~M2) |
| Phase 2: IoT data pipeline | M2–M3 | Sensor firmware (Python spidev + w1-gpio), MQTT publish pipeline, SQLite/InfluxDB storage, raw data logging and validation against reference sensor | Review-1 (~M3) |
| Phase 3: Digital twin core | M3–M4 | State object definition finalized, real-time sensor-to-state sync, REST API exposing current and historical state, dashboard skeleton rendering live data | — |
| Phase 4: ML pipeline | M4–M6 | CWRU + IMS dataset preprocessing and feature extraction; Isolation Forest trained and deployed (M5); 1D Conv Autoencoder trained, TFLite exported, deployed (M6); OOD confidence flag implemented; health index calibrated on pilot machine baseline | Review-2 (~M5): 25% implementation |
| Phase 5: Copilot + integration | M6–M7 | llama.cpp + TinyLlama-1.1B Q4 deployed; RAG retrieval pipeline implemented; system prompt and fallback logic finalized; full dashboard with alerts and ROI estimator; end-to-end integration test | Review-3 (~M6): 50% implementation |
| Phase 6: Testing & submission | M7–M8 | F1-score evaluation on held-out CWRU test set; copilot factual accuracy test (50 structured queries); retrofit protocol documentation and reproducibility check; full written report; viva demo preparation | Phase 1 Report (~M8) |

---

## 11. Risks and Mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| Sensor noise on real legacy machine degrades model accuracy | Medium | Collect 30-minute baseline before training; use robust statistical features (kurtosis, crest factor) less sensitive to noise than raw FFT |
| TinyLlama response latency unacceptable in practice | Low | Tested constraint: 5–15 s is acceptable for non-real-time queries; if unacceptable, fall back to rule-based responses without LLM |
| No access to a real MSME factory floor | Medium | Use lab motor/compressor as pilot asset; explicitly frame as controlled prototype with field validation as future work |
| CWRU downsampling reduces fault detectability | Medium | Validate F1-score on downsampled CWRU before deployment; if below 0.80, extend feature set to include spectral entropy and wavelet coefficients |
| Timeline slippage on ML pipeline (M4–M6) | Medium | Isolation Forest baseline can ship independently; autoencoder is an enhancement, not a gate |
| RAM contention if copilot and ML inference run simultaneously | Low | Copilot runs on-demand (not resident); sequenced via a request queue to prevent overlap with TFLite inference |

---

## 12. Limitations

The following limitations are explicitly acknowledged to maintain academic integrity:

- **Sampling frequency**: the ADXL345 (SPI) achieves up to 3,200 Hz. High-frequency bearing fault signatures (e.g., ball pass frequency harmonics above 5 kHz) cannot be detected with this hardware. The system targets low-to-mid frequency mechanical anomalies detectable via statistical features.
- **Dataset transfer gap**: CWRU and IMS datasets were collected on research-grade test rigs at sampling rates (12–48 kHz) higher than deployment hardware. Downsampling and domain adaptation reduce but do not eliminate this distribution shift.
- **Single-asset scope**: the system monitors one machine. Multi-asset deployments are future work.
- **Copilot latency**: local inference at 5–15 seconds is unsuitable for real-time control decisions. The copilot is a diagnostic tool, not a control interface.

---

## 13. Future Work

- Current clamp sensor integration for electrical fault detection (phase imbalance, overload) as a complementary fault signature channel.
- Physics-Informed Neural Networks (PINNs) to embed mechanical constraints and improve model generalization across machine types.
- Synthetic fault data generation (GANs, SMOTE) to address data scarcity for rare fault classes.
- Multi-machine scaling with a federated local deployment model.
- Field validation study with a real MSME partner to assess adoption friction and deployment cost accuracy.
- ZED/SAMARTH subsidy alignment: map hardware BOM to existing scheme eligibility criteria.

---

## 14. Repository Structure

```
.
├── apps/
│   └── dashboard/          React + Vite + TS dashboard (offline-first SPA)
│       ├── src/
│       │   ├── api.ts            fetchCurrentState + fetchStateHistory + state types (DD-028,
│       │   │                     polls api's GET /state/current + GET /state/history)
│       │   ├── thresholds.ts     evaluateAlerts — client-side alert threshold logic (§6.5)
│       │   ├── components/       HealthGauge, TrendChart, AlertsPanel, HistoryLog, RoiEstimator
│       │   │                     (§6.5, full dashboard build-out)
│       │   └── App.tsx            renders live state + gauge/trends/alerts/log/ROI (§6.5)
│       ├── Dockerfile      multi-stage: base → deps → dev / build → prod (nginx)
│       └── nginx.conf
├── services/
│   ├── edge/               Sensor acquisition + feature extraction + ML inference (FastAPI)
│   │   └── src/edge/
│   │       ├── providers/        base.py (interface + VibrationFeatures + SensorSample's
│   │       │                     raw_vibration_window_g), simulated.py (now generates a raw
│   │       │                     window and derives features from it, matching hardware.py),
│   │       │                     hardware.py (real ADXL345/DS18B20 decode, DD-022)
│   │       ├── features.py       compute_vibration_features — rms/kurtosis/crest/p2p (DD-022)
│   │       ├── ml_inference.py   MLInferenceEngine — loads services/ml's ONNX artifacts (DD-031)
│   │       │                     if present, else disables inference (null fields, §24)
│   │       ├── storage.py        RawReadingStore (DD-023, DD-024) + StateStore (DD-026, now
│   │       │                     writes ML-derived fields when an MLInferenceResult exists)
│   │       └── main.py            MQTT publish loop (DD-025) + ML inference + FastAPI lifespan
│   ├── api/                REST API over the digital-twin state object (FastAPI)
│   │   └── src/api/
│   │       ├── storage.py        StateReader — reads `state_history` (DD-026, schema
│   │       │                     duplicated from edge/storage.py, no shared package)
│   │       └── main.py            GET /state/current, GET /state/history
│   ├── copilot/             Retrieval-grounded NL copilot (FastAPI, implemented §28 Entry 13)
│   │   └── src/copilot/
│   │       ├── retrieval.py      fetches recent state objects from api
│   │       ├── context.py        freshness/OOD context validity check (§6.4)
│   │       ├── prompt.py         system prompt + structured context serialization
│   │       ├── fallback.py       rule-based responses (no-data/stale/OOD/LLM-unavailable)
│   │       ├── llm_local.py      TinyLlama/llama.cpp client (`local-llm` extra, deferred import)
│   │       ├── llm_api.py        Anthropic/OpenAI API-fallback client (httpx)
│   │       ├── service.py        QueryEngine — orchestrates retrieve→validate→answer/fallback
│   │       ├── sensorrag/        SensorRAG faithfulness evaluation protocol (DD-030): queries.py
│   │       │                     (held-out cases), grounding.py (numeric-claim grounding
│   │       │                     heuristic), runner.py (report + fallback-accuracy/
│   │       │                     hallucination-rate metrics, design.md §9)
│   │       └── main.py            GET /health, POST /query
│   └── ml/                  Offline training pipeline (Isolation Forest, 1D conv autoencoder,
│                             implemented §28 Entry 13)
│       └── src/ml/
│           ├── features.py       compute_window_features — independent re-implementation of
│           │                     edge's feature math (DD-002), for training-time use
│           ├── synthetic.py      placeholder normal/faulty window generator — the real CWRU/IMS
│           │                     download is still pending (§24), DD-031
│           ├── datasets.py       real CWRU/IMS loader interface — raises a clear error until
│           │                     the datasets are downloaded, rather than silently faking data
│           ├── isolation_forest.py   train + ONNX export (skl2onnx, DD-031)
│           ├── autoencoder.py    Conv1DAutoencoder (PyTorch) — arbitrary window length via a
│           │                     final interpolate-to-input-length step; ONNX export
│           ├── ood.py            fit_ood_bounds/is_out_of_distribution — 99% two-tailed band
│           ├── health_index.py   calibrate_health_index/compute_health_index (§6.3)
│           ├── evaluate.py       F1 evaluation helper (design.md §9's targets)
│           └── pipeline.py       run_training_pipeline — orchestrates all of the above into
│                                 artifacts/ (ONNX models + calibration + manifest.json)
├── packages/                Shared TypeScript packages (empty — DD-013/DD-020: no 2nd TS
│                            consumer yet; `pnpm-workspace.yaml` already globs `packages/*`)
├── docs/
│   ├── architecture/        Standalone architecture docs once a topic outgrows §6 (DD-020)
│   ├── adr/                 Standalone ADRs promoted from the §15 DD-NNN table (DD-020)
│   ├── research/            Research notes/evaluation write-ups beyond §8-9 (DD-020)
│   └── hardware/            Wiring diagrams/datasheets/retrofit notes beyond §6.2 (DD-020)
├── infra/
│   └── mosquitto/           Local MQTT broker config
├── docker/
│   └── tools.Dockerfile     Toolbox image: node+pnpm+python+uv+ruff+git, used by hooks/Makefile/CI
├── scripts/
│   └── bootstrap.sh         Host validation + local env prep (the only pre-Docker step)
├── .github/
│   ├── workflows/ci.yml     lint/typecheck/test/build/security, matrixed per service
│   ├── workflows/codeql.yml
│   └── dependabot.yml
├── .husky/                  pre-commit (lint-staged), commit-msg (commitlint) — run via toolbox
├── .vscode/                 workspace settings + recommended extensions
├── docker-compose.yml        dev stack (default `up`/`watch` target)
├── docker-compose.prod.yml   Pi/production override (`-f docker-compose.yml -f docker-compose.prod.yml`)
├── Makefile                  `make lint|format|typecheck|test|train|train-synthetic|shell-tools|bootstrap|watch`
├── package.json / pnpm-workspace.yaml / tsconfig.base.json / eslint.config.js
├── ruff.toml                 shared Python lint/format config (per-service pyproject.toml extends it)
├── CLAUDE.md                  documentation-first workflow rules for AI-assisted development
└── design.md                  this document — canonical engineering memory
```

Each `services/*` directory is an independent `uv`-managed Python project (own `pyproject.toml`,
own lockfile, own `.venv` inside its container) — there is no shared Python virtualenv across
services, matching their independent deployment lifecycles (edge/api/copilot are always-on
FastAPI services; ml is an on-demand training job).

---

## 15. Design Decisions

| ID | Decision | Rationale |
|---|---|---|
| DD-001 | Docker-first onboarding: `git clone && ./scripts/bootstrap.sh && docker compose watch` is the entire setup | No host Node/Python/pnpm/uv installs required; deterministic across contributor machines |
| DD-002 | Polyglot monorepo: pnpm workspace for TypeScript (`apps/*`) + independent `uv`-managed Python packages (`services/*`) | design.md's actual stack is Python-heavy (edge/ML/copilot) with React only for the dashboard (§7) — a single-language template would fight the domain |
| DD-003 | Pluggable sensor provider abstraction (`SensorProvider` interface, `simulated`/`hardware` implementations, selected via `SENSOR_PROVIDER` env var) | ADXL345/DS18B20 need real GPIO/SPI/1-Wire hardware unavailable in dev/CI containers; app code must not know which provider is active |
| DD-004 | `docker-compose.prod.yml` is an override file (`-f` merge), not a parallel compose stack, and is how the Pi switches `edge` to the hardware provider (via `devices:` passthrough + `SENSOR_PROVIDER=hardware`) | One source of truth for service topology; prod only changes build target, env, and device access |
| DD-005 | Single "toolbox" image (`docker/tools.Dockerfile`) is the one environment for linting, formatting, type checking, testing, git hooks, and CI | Guarantees identical tool versions everywhere (host, hooks, CI) and keeps the host dependency-free per DD-001 |
| DD-006 | `uv` for all Python dependency management (per-service `pyproject.toml` + lockfile) | Single static binary, fast resolver, native PEP 735 `dependency-groups`, no host Python venv required |
| DD-007 | `ruff` installed once globally in the toolbox (dependency-free linting/formatting); `mypy` installed per-service and run via `uv run` | ruff doesn't need a project's dependencies to lint/format; mypy does (to resolve imported types), so it must run inside each service's own environment |
| DD-008 | ESLint 9 flat config + `typescript-eslint` strict/stylistic type-checked configs + `eslint-plugin-import-x` (not `eslint-plugin-import`) | `import-x` is the maintained fork with first-class flat-config support |
| DD-009 | `knip` for unused dependency / unused export / dead file detection in the TS workspace | One tool covers what would otherwise need depcheck + ts-prune + unimported |
| DD-010 | Secrets live entirely outside the repository. `SECRETS_FILE` (default `$HOME/.config/digital-cousin/secrets.env`) is validated/created by `scripts/bootstrap.sh` and passed to the `copilot` container via `env_file:` | Copilot's optional Anthropic/OpenAI API fallback needs keys; the default `COPILOT_LLM_MODE=local` (TinyLlama/llama.cpp) needs none. Never committing even a placeholder `.env` with real structure to the repo avoids any risk of a filled-in copy being committed by accident |
| DD-011 | `ml` service pins PyTorch to the CPU wheel index (`download.pytorch.org/whl/cpu` via `[tool.uv.sources]`) | Training runs on a dev PC/CI runner per §7 ("training only, on development PC"), not a GPU box; CUDA wheels would add multiple GB to every build for no benefit |
| DD-012 | Compose `profiles: ["tools"]` (toolbox) and `["training"]` (ml-trainer) keep non-runtime containers out of the default `docker compose up`/`watch` set | Toolbox and the training job are invoked on demand (`make lint`, `make train`), not part of the always-on service topology |
| DD-013 | No Turborepo / task-graph tool yet | Only one TypeScript package (`apps/dashboard`) exists; plain `pnpm -r --if-present run <script>` is sufficient. Revisit once a second TS package (e.g. shared types) exists |
| DD-014 | Coverage gates are native to each test runner (vitest `coverage.thresholds`, `pytest --cov-fail-under`) rather than an external coverage SaaS | No third-party account/token needed to enforce a quality gate in CI |
| DD-015 | Security scanning uses free, self-hosted-in-CI tools only: gitleaks (secrets), Trivy (filesystem/dependency CVEs), hadolint (Dockerfile lint), CodeQL (SAST), `pnpm audit`/`pip-audit` (dependency advisories) | No paid service or external account required — appropriate for a capstone project budget (§2 cost barrier is a core design constraint of the product itself) |
| DD-016 | Mosquitto runs with `allow_anonymous true` and no TLS | The broker is only ever reachable on the Docker-internal network / Pi-local network in the current design (§6.1); tracked as Technical Debt (§25) to revisit before any network-exposed deployment |
| DD-017 | All six Dockerfiles suppress hadolint DL3008 (`# hadolint ignore=DL3008` above each `apt-get install`) instead of pinning exact Debian/Ubuntu package versions for `curl`/`ca-certificates`/`git`/`python3.11` | These packages come from each image's own base (`python:3.11-slim`, `node:22-slim`) and track that base's own security patches; hard-pinning a specific Debian package version would silently break (or go stale) every time the upstream base image is bumped, for no real reproducibility gain since the base image itself is not pinned to a digest |
| DD-018 | `apps/dashboard`'s `vite`/`vitest`/`@vitest/coverage-v8` bumped from the 5.x/2.x line to `^6.4.3`/`^3.2.7`, plus a `pnpm-workspace.yaml` `overrides.vite: ^6.4.3` | `pnpm audit --audit-level=high` failed CI (GHSA-fx2h-pf6j-xcff `vite` high, GHSA-5xrq-8626-4rwp `vitest` moderate); bumping the direct `vite`/`vitest` deps alone left vitest's own `vite-node`/`@vitest/mocker` sub-dependencies resolving an independent, still-vulnerable `vite@5.4.21` (confirmed via `pnpm why vite`), so a workspace-level override was needed to force every transitive copy onto the patched line — deliberately stayed on the 6.x/3.x line rather than the latest 8.x/4.x majors (beta at the time) to keep the fix minimal |
| DD-019 | `.github/workflows/ci.yml`'s `container-scan` job pins `aquasecurity/trivy-action@v0.29.0` (was `@0.29.0`, no `v` prefix) | The action's git tags are `v0.18.0`…`v0.36.0`; the un-prefixed ref didn't resolve to any tag, so `container-scan` failed at the "Getting action download info" step before Trivy ever ran — this was a broken CI job, not a real Trivy finding. **Superseded by DD-021**: `v0.29.0` itself turned out to have a second, deeper problem |
| DD-020 | Added `docs/{architecture,adr,research,hardware}/` and `packages/` as scaffolded-but-empty directories (each holding only a README stub); `design.md` itself stays whole and at the repo root, unsplit | User requested production-grade repo layout conventions (docs/ with topic subfolders, packages/ alongside apps/+services/). `design.md` is CLAUDE.md's single authoritative engineering-memory file (read before every request, append-only Development Log, §14 Repository Structure lives inside it) — splitting its 29 sections across the new folders would have replaced that workflow, not just reorganized files, so per explicit user confirmation it stays a single root file and the new folders are forward-looking scaffolding: promote content out of the relevant `design.md` section into `docs/*` only once that content outgrows a PRD section (see each folder's README for the specific handoff rule) |
| DD-021 | `dependency-audit`'s `pip-audit` invocation now passes `--disable-pip` (in addition to the existing `--no-deps`); `container-scan` repinned from `aquasecurity/trivy-action@v0.29.0` to `@v0.36.0` | **pip-audit**: `--no-deps` alone does *not* skip `pip-audit`'s internal venv bootstrap — only `--disable-pip` does (allowed here because `uv export`'s output is already `--no-deps`/fully hashed). Without it, `pip-audit`'s `VirtualEnv(EnvBuilder(with_pip=True))` copies (doesn't symlink) the interpreter into a throwaway venv; uv's managed standalone CPython needs a sibling `lib/` dir next to the binary for its `$ORIGIN`-relative `libpython*.so`, so the copy fails to load it and the child process exits `127` with zero output (the error text itself is captured into `_call_new_python`'s `.output`, which the unhandled `CalledProcessError` traceback never prints — found only by reproducing locally with `strace` and manually replicating `_call_new_python`'s exact subprocess call to surface the suppressed stderr). A second, independent problem existed underneath: `pip-audit`'s dry-run `pip install` re-resolves against whatever Python actually runs it, and `services/ml`'s `uv export` hashes are locked to cp311 wheels only — under a different interpreter (attempted as part of a same-day, since-reverted `UV_PYTHON_PREFERENCE=only-system` workaround) pip rejected the hash-mismatched `scipy` wheel and fell back to a source build, which failed on a missing Fortran compiler. `--disable-pip` avoids both failure modes at once by never installing/resolving anything — it trusts the already-pinned, already-hashed export directly. **Trivy**: `v0.29.0`'s composite action internally pins `aquasecurity/setup-trivy@v0.2.2`, a tag since deleted upstream (confirmed via `git ls-remote --tags`: only `v0.2.6`+ remain) — `v0.36.0` pins that same internal dependency by commit SHA, immune to future upstream tag deletions |
| DD-022 | `HardwareSensorProvider.read()` samples a 64-reading burst (~80ms at 800 Hz) per call rather than a continuous 3,200 Hz stream, and computes `vibration_rms_g` as the RMS of the AC-coupled signal (window mean, dominated by the ~1g gravity offset at the mount orientation, subtracted before RMS) | §6.2's "up to 3,200 Hz" is the ADXL345's hardware ceiling, not a claim that a synchronous Python polling loop inside an async FastAPI process can sustain that rate without real-time buffering/jitter design — that's a real-time-systems problem best tuned empirically against actual hardware (not yet procured, §24), so Phase 2 scope is a technically-correct register decode (real 3.9 mg/LSB scale factor, real POWER_CTL/DATA_FORMAT/BW_RATE init sequence) proven with a burst, not a production-tuned continuous stream — matching §24's own task granularity ("ADXL345 SPI register decoding" is a separate, narrower Phase 2 item from "state object sync", which stays Phase 3) |
| DD-023 | Edge's MQTT publish loop and new `RawReadingStore` (SQLite `raw_readings` table: `asset_id`, `ts`, `vibration_rms_g`, `temperature_c`) are deliberately a separate, narrower schema from the full digital-twin state object in §6.0 (`anomaly_score`, `health_index`, `model_confidence`, `alert_level`) | Those ML-derived fields don't exist until Phase 4 (models) and Phase 3 (state sync + `api` read endpoints); logging exactly what the sensor read now, without inventing placeholder values for fields nothing populates yet, keeps `raw_readings` an honest record rather than a preview of a schema that will actually land in Phase 3 |
| DD-024 | `RawReadingStore`/`DATABASE_PATH` default to SQLite's `:memory:` when the env var is unset (docker-compose always sets an explicit file path) | Lets unit tests and bare `uv run` exercise the real `sqlite3` code path (schema creation, inserts) with no file-system side effects and no directory-existence assumptions, while production/dev-container runs get real persistence via the existing `sqlite-data` volume |
| DD-025 | New MQTT topic scheme `digital-cousin/<asset_id>/raw`, separate from any future `.../state` topic Phase 3 might add | Keeps the raw sensor feed (Phase 2, this work) and the eventual full-state broadcast (Phase 3, once `anomaly_score`/`health_index` exist) on distinct topics so a Phase-3 consumer can't accidentally treat an unenriched raw reading as a complete state object |
| DD-026 | Phase 3's `state_history` SQLite schema and its row→JSON mapping are independently duplicated in `services/edge/src/edge/storage.py` (writer) and `services/api/src/api/storage.py` (reader) — no shared package. `api`'s copy also runs `CREATE TABLE IF NOT EXISTS` so it can boot before `edge` ever writes a row | Per DD-002/§14, `edge` and `api` are independent `uv` projects with no shared Python package (packages/ is TS-only, DD-013/DD-020); the alternative (a first shared internal Python package) is more machinery than one ~15-line schema justifies today. Both copies live under the same `# schema duplicated, keep in sync` comment so future edits aren't done in only one place. `/state/*` returns HTTP 404 (not `null`) when nothing has been recorded yet, matching REST convention for "resource doesn't exist" |
| DD-027 | `services/api`'s FastAPI app adds `CORSMiddleware` with `allow_origins=["*"]` (GET only) | The dashboard fetches `api` directly from the browser, which is a *different origin* (`localhost:5173` dev / the Pi's nginx port in prod) — without CORS headers the browser silently blocks the fetch even though `curl`/server-to-server calls work fine (confirmed missing before this change, then present after: `curl -H "Origin: ..."` showed no `access-control-allow-origin` header pre-fix). Wildcard is a deliberate choice mirroring DD-016's reasoning: single-tenant, offline-first, LAN-local device, no untrusted origins ever reach it, no sensitive/authenticated data served — tracked as Technical Debt (§26) to revisit if this API is ever exposed beyond localhost/LAN |
| DD-028 | `apps/dashboard/src/api.ts`'s `DigitalTwinState`/`VibrationFeatures` TypeScript interfaces are a third independent copy of the §6.0 state-object shape (alongside edge's and api's Python copies, DD-026) | No shared schema mechanism crosses the Python/TypeScript language boundary either; documented here so a future schema change (e.g. Phase 4 populating `anomaly_score`) is remembered as a 3-way, not 2-way, update |
| DD-029 | `docker-compose.prod.yml`'s dashboard healthcheck probes `http://127.0.0.1:8080/healthz`, not `http://localhost:8080/healthz` | Found during a full re-verification audit (Entry 11): the prod dashboard container's `/etc/hosts` resolves `localhost` to `::1` (IPv6) only, but nginx's `listen 8080;` is IPv4-only, so busybox `wget` (no multi-address fallback, unlike `curl`) failed the healthcheck with "Connection refused" on every single run — the container was silently reporting unhealthy on every real prod deployment despite serving traffic correctly (confirmed: host-side `curl http://localhost:8080/` returned 200 the whole time, masking the problem, since curl retries the next resolved address on connection failure and the host-to-container path goes through Docker's NAT rather than the container's own `/etc/hosts`). `127.0.0.1` sidesteps the DNS ambiguity entirely regardless of which HTTP client resolves it |
| DD-030 | The user-supplied literature survey PDF (`LS_V2.pdf`, IEEE-style paper, 5 co-authors, 39 references) was reviewed against the full repo and design.md (2026-08-14, Entry 12) as the project's "latest finalized architecture." It is **not** an architecture/build spec — it's an academic literature survey establishing the research gap (a cross-cutting gap matrix, Table III, scoring 30 prior works against six properties: single-asset scope, edge-only deployment, MSME context, NL interface, low-cost hardware, and sensor-grounded faithfulness evaluation). Every hardware/software/architecture detail it references (ADXL345/DS18B20, RPi 4, TinyLlama-1.1B Q4 via llama.cpp, Isolation Forest + 1D conv autoencoder, CWRU/IMS datasets, <₹10,000 target) already matches §1–§13 verbatim, confirming design.md's PRD content is already synced to it — **no architecture changes resulted from this review.** The one new element: the paper frames a "SensorRAG" sensor-telemetry faithfulness evaluation protocol as its primary novel contribution (property 6 of the gap matrix, satisfied by no prior work) — this was previously absent from design.md and has been added to §3 (Objective 7), §6.4, §8 (Novelty 5), §9, and §24 | A full repo audit (`git ls-files`, spot-read of `services/ml/src/ml/pipeline.py` and `services/copilot/src/copilot/main.py`) confirmed the tracked file tree and Phase 3/skeleton-only status match design.md §14/§20/§24/§29 exactly — no drift between docs and code existed prior to this entry, so this was a documentation *addition* (the missing SensorRAG requirement), not a correction |
| DD-031 | Phase 4/5 implementation (§28 Entry 13) switched the ML export/inference target from TFLite (§6.3/§7's original documented choice) to **ONNX** (`onnx`/`skl2onnx` in `services/ml`, `onnxruntime` in `services/edge`); `services/ml`'s autoencoder trains on 64-sample windows (not 3,200) to match `edge`'s real per-`read()` burst size (DD-022); real CWRU/IMS dataset loading is an interface only (`ml.datasets`) that raises a clear error until the datasets are downloaded, with an explicit opt-in synthetic-data path (`ml.synthetic`, `--allow-synthetic`) for pipeline development | User chose ONNX over adding TensorFlow (via an `AskUserQuestion`, "Recommended" option) when the gap surfaced that `services/ml` only had PyTorch, not TensorFlow: `torch.onnx.export` is already built into the existing PyTorch dependency, and `skl2onnx` converts the Isolation Forest too, so both models share a single inference runtime (`onnxruntime`, prebuilt wheels, no native compiler needed) rather than adding TensorFlow + a converter solely for a training-time export step. The 64-sample window choice is a direct consequence of DD-022's existing scope decision — `edge.ml_inference` needs to run against the same window shape `edge` actually produces today, not the eventual 3,200 Hz continuous stream that's still a pending real-time-buffering task (§24) |
| DD-032 | `edge.ml_inference.MLInferenceEngine`'s Isolation Forest ONNX output is located by a case-insensitive substring match on `"score"` across the model's output names, falling back to the last output if nothing matches, rather than a hardcoded exact output name | `skl2onnx`'s exact output naming for `IsolationForest.score_samples`-equivalent outputs isn't pinned down from documentation alone and this session could not execute the pipeline to confirm it empirically (no Docker/pnpm/pytest execution — user instructed "dont run anything... ill start it there ther [in Ubuntu]"); a substring-based lookup is more likely to survive small naming differences across `skl2onnx` versions than an exact match would, at the cost of not being provably correct until actually run — tracked as an unverified assumption in §25, not silently presented as certain |
| DD-033 | The SensorRAG faithfulness protocol (`copilot.sensorrag`, §6.4, DD-030) checks numeric grounding via regex-extracted numbers compared against context values within a 2% relative tolerance — it verifies a claimed number is *present* in the retrieved context, not that it's attributed to the *correct* field | A fully rigorous claim-level semantic check (e.g. "is this specific number correctly labeled as the health index, not the temperature") needs entity linking between the LLM's free text and the structured context, which is a substantially harder NLP problem than presence-checking and out of scope for this session; documented as a known limitation (§26) rather than silently claimed as complete, so a future pass has an honest starting point rather than a false sense of certainty |
| DD-034 | `services/ml/src/ml/isolation_forest.py`'s `export_isolation_forest_to_onnx` pins `target_opset={"ai.onnx.ml": 3, "": 18}` explicitly; `services/ml/pyproject.toml` adds `onnxscript>=0.2` as a plain dependency | Verifying Entry 13 for real (this entry) surfaced two toolchain version-skew bugs neither DD-031 nor Entry 13 could have caught without executing the pipeline: (1) `skl2onnx==1.20.0`'s `IsolationForest` converter emits `ai.onnx.ml` ops tagged opset 4, but the same library's own opset-support table caps `ai.onnx.ml` at 3 — an internal skl2onnx inconsistency, not a real modeling issue; pinning `target_opset` explicitly (verified working against `onnx==1.22.0`/`skl2onnx==1.20.0`) sidesteps it. (2) `torch==2.13`'s `torch.onnx.export` now defaults to the dynamo-based exporter (the legacy TorchScript exporter emits a `DeprecationWarning` and is being phased out per PyTorch's own 2.9 release notes), which requires `onnxscript` as a runtime dependency — without it `export_autoencoder_to_onnx` raised `ModuleNotFoundError` on first real invocation |
| DD-035 | `services/edge/src/edge/providers/__init__.py`'s `get_provider("simulated")` branch lazily imports `SimulatedSensorProvider` inside the function body, matching the existing lazy-import pattern already used for `"hardware"` | Entry 13 added `edge.providers.simulated`'s import of `edge.features.compute_vibration_features` (so the simulated provider derives its four statistical features from a real raw window via the same function `hardware.py` uses, DD-031's window-shape consistency goal) — but `edge.features` itself imports `edge.providers.base.VibrationFeatures`, and Python always runs a package's `__init__.py` before any of its submodules. The result was a real circular import (`edge.features` → `edge.providers` package init → `edge.providers.simulated` → `edge.features`, still mid-initialization) that broke on any entry point importing `edge.features` first (e.g. `tests/test_features.py`) — never previously exercised because nothing imported `edge.features` directly before this session's `make test` run. Lazy import breaks the cycle without restructuring the module layout |
| DD-036 | This session's Docker-based verification (`make lint`/`typecheck`/`test`, `docker compose build`, `make train-synthetic`, `docker compose up`) ran on a fresh Ubuntu Docker install where `docker compose run`'s default user is root inside every container, including the `toolbox` container Husky's pre-commit hook shells into (§7.6) — every hook-triggered `git` operation (`lint-staged`'s internal `git stash`) and every bind-mounted write (`services/ml/artifacts/`, `.venv/`, coverage output) left files/`.git` internals root-owned on the host, which then blocked the *next* host-side `git commit` with "insufficient permission for adding an object to repository database." Fixed per-occurrence with a throwaway `docker run --rm -v "$(pwd):/repo" alpine chown -R "$(id -u)":"$(id -g)" /repo` rather than any project-file or git-config change | This is a distinct root cause from the DD-030/Entry-12 Windows/NTFS executable-bit issue (§25) — confirmed in this entry: `.husky/commit-msg`/`.husky/pre-commit`/`scripts/bootstrap.sh` show **zero** mode diff on this Ubuntu checkout (`git diff --summary` clean), so that specific historical concern does not reproduce here and needs no `core.filemode` change. The *new* finding is that Husky's own hook invocation (not the checkout) intermittently reintroduces spurious `+x` bits and root ownership on newly-created tracked files via the same toolbox-container mechanism — worth a future look at running the toolbox container with `--user "$(id -u):$(id -g)"` (tracked as Technical Debt, §26) so host-side git operations never need a manual chown afterward |
| DD-037 | `pnpm-workspace.yaml`'s `overrides` gained six entries (`fast-uri`, `js-yaml`, `postcss`, `nanoid`, and two parent-scoped `brace-expansion` entries) after PR #61's first CI run failed `pnpm audit --audit-level=high` with newly-disclosed advisories in transitive dev-tooling deps (commitlint→ajv→fast-uri; eslint's own js-yaml/minimatch→brace-expansion chain; vitest coverage's glob→minimatch→brace-expansion chain) — none tied to any code change in this branch, same category as DD-018's pre-existing `vite` override. `brace-expansion` specifically needed **parent-scoped** overrides (`minimatch@3>brace-expansion: "^1.1.18"`, `minimatch@9>brace-expansion: "^2.1.4"`, pnpm's documented `parent@range>child` syntax) rather than a single blanket one | Two real mistakes made and corrected while fixing this, both confirmed by actually re-running `make lint`/`pnpm audit` after each attempt rather than assumed: (1) a blanket `brace-expansion: ">=5.0.9"` override collapsed *every* consumer (including `minimatch@3.1.5`, which calls a `.braceExpand` API only `brace-expansion`'s 1.x line has) onto the newest line, breaking ESLint outright (`TypeError: expand is not a function`) — parent-scoping by consumer, not just the target package, was required. (2) the parent-scoped override still didn't stick until the *target* range was changed from open-ended `>=1.1.18` to caret `^1.1.18` — pnpm resolves an open-ended `>=` range to the newest version satisfying that inequality (5.0.9 numerically satisfies `>=1.1.18`), not "newest within that major line," so it silently reproduced mistake (1) even though the parent scope was correct. `pnpm why brace-expansion` after each attempt is what surfaced both mistakes concretely rather than trusting the override syntax alone |

---

## 16. Dependencies

**Root (TypeScript tooling, devDependencies only — no runtime deps at the root):**
`typescript`, `eslint` + `@eslint/js` + `typescript-eslint` + `eslint-plugin-{react,react-hooks,jsx-a11y,import-x,promise}` + `eslint-config-prettier`, `prettier`, `husky`, `lint-staged`, `@commitlint/{cli,config-conventional}`, `knip`.

**`apps/dashboard`:** `react`, `react-dom` (runtime); `vite`, `@vitejs/plugin-react`, `vitest`, `@vitest/coverage-v8`, `@testing-library/{react,jest-dom}`, `jsdom` (dev). No new runtime deps added for the §6.5 dashboard build-out — trend charts are a hand-written inline-SVG component, no charting library.

**`services/edge`:** `fastapi`, `uvicorn[standard]`, `pydantic`, `paho-mqtt`, `onnxruntime` (DD-031, ML inference — runtime, not optional: prebuilt wheels, no native compiler needed) (runtime); optional extra `hardware` = `spidev`, `RPi.GPIO`, `w1thermsensor` (Pi-only, not installed by default sync); dev-only `onnx` (hand-builds tiny stub ONNX graphs in `test_ml_inference.py` without depending on `services/ml`'s sklearn/torch stack, DD-002).

**`services/api`:** `fastapi`, `uvicorn[standard]`, `pydantic`.

**`services/copilot`:** `fastapi`, `uvicorn[standard]`, `pydantic`, `httpx` (runtime, now actually used by both retrieval and the API-fallback LLM path); optional extra `local-llm` = `llama-cpp-python` (compiles native code — kept optional so CI/dev-container installs stay fast; import deferred to `LocalLlamaClient.__init__`).

**`services/ml`:** `scikit-learn`, `torch` (CPU wheels, DD-011), `numpy`, `pandas`, `onnx`, `skl2onnx` (DD-031, ONNX export for both models).

**Every Python service** additionally declares a `dev` dependency group: `pytest`, `pytest-cov`, `mypy`, (+`httpx` for FastAPI services, needed by `TestClient`).

No dependency has been added without a corresponding line item above and, where non-obvious, a DD in §15.

---

## 17. Environment Variables

| Variable | Where | Default | Purpose |
|---|---|---|---|
| `SENSOR_PROVIDER` | `edge` | `simulated` (dev) / `hardware` (prod, via `docker-compose.prod.yml`) | Selects the `SensorProvider` implementation (DD-003) |
| `ASSET_ID` | `edge`, `api` | `motor_01` | Pilot-machine identifier (§6.0 state model); MQTT topic segment (DD-025), `raw_readings`/`state_history` row key, and `api`'s default `/state/*` query param |
| `MQTT_HOST` / `MQTT_PORT` | `edge` | `mosquitto` / `1883` | MQTT broker address on the Docker network |
| `PUBLISH_INTERVAL_SECONDS` | `edge` | `5` | How often the publish loop reads the active provider and logs/publishes a reading (DD-023) |
| `DATABASE_PATH` | `edge`, `api` | `/data/digital_cousin.sqlite3` | SQLite file inside the shared `sqlite-data` named volume; defaults to `:memory:` if unset (DD-024) |
| `ML_ARTIFACTS_DIR` | `edge` | `/app/ml-artifacts` | Where `edge.ml_inference.MLInferenceEngine` looks for `services/ml`'s exported `manifest.json`/ONNX models (DD-031); mounted read-only from the same host path `ml-trainer` writes into. Absent until a training run has happened — inference is disabled (null fields), not a startup failure |
| `COPILOT_LLM_MODE` | `copilot` | `local` | `local` = TinyLlama/llama.cpp (no secrets); `api` = Anthropic/OpenAI fallback |
| `LOCAL_LLM_MODEL_PATH` | `copilot` | `/app/models/tinyllama-1.1b-q4_k_m.gguf` | GGUF weights path for `COPILOT_LLM_MODE=local` — not yet downloaded/mounted anywhere (§24); `LocalLlamaClient` raises a clear error if missing rather than silently falling back |
| `COPILOT_API_PROVIDER` | `copilot` | `anthropic` | `anthropic` or `openai` — which API-fallback provider `COPILOT_LLM_MODE=api` uses |
| `COPILOT_API_MODEL` | `copilot` | `claude-sonnet-5` (anthropic) / `gpt-4o-mini` (openai) | Model identifier passed to the chosen provider's API — not verified against a live API call in this session (no key present) |
| `API_URL` | `copilot` | `http://api:8000` | Internal Docker-network address of the REST API |
| `VITE_API_URL`, `VITE_COPILOT_URL` | `dashboard` | `http://localhost:8000`, `http://localhost:8001` | Browser-facing URLs (host-mapped ports, not container-internal) |
| `SECRETS_FILE` | root `.env` (compose variable substitution) | `$HOME/.config/digital-cousin/secrets.env` | Path to the external, non-repo secrets file (DD-010) |
| `ANTHROPIC_API_KEY`, `OPENAI_API_KEY` | inside `$SECRETS_FILE` only, never in-repo | empty | Copilot API-fallback credentials; only read when `COPILOT_LLM_MODE=api` |

`.env.example` documents all of these except the two secret keys, which exist only inside the
externally-mounted `$SECRETS_FILE`.

---

## 18. External Integrations

| Integration | Status | Notes |
|---|---|---|
| Anthropic / OpenAI API (copilot fallback) | Optional, not yet implemented beyond config plumbing | Only invoked when `COPILOT_LLM_MODE=api` and `$SECRETS_FILE` has a key set |
| GitHub Actions | Active | CI (`ci.yml`), CodeQL (`codeql.yml`), Dependabot (`dependabot.yml`) |
| GitHub remote | Active | `origin` → `https://github.com/samarthkolur/digital_twin_msme_platform.git` (see §29) |
| Docker Hub / `ghcr.io` base images | Active (pull-only) | `node:22-slim`, `python:3.11-slim`, `nginx:1.27-alpine`, `eclipse-mosquitto:2.0`, `ghcr.io/astral-sh/uv:0.5.9` — no images are currently published, only pulled |
| CWRU / IMS Bearing datasets | Planned (Phase 4) | Not yet integrated; referenced in §6.3 |

---

## 19. Infrastructure & Deployment

**Local development:** `docker compose watch` — five services (`mosquitto`, `edge`, `api`,
`copilot`, `dashboard`) rebuild/sync automatically on file changes via `develop.watch` blocks in
`docker-compose.yml`. No bind-mounted `volumes:` are used for source code (avoids the classic
host/container `node_modules` collision) — `watch` syncs deltas directly into the already-built
dev image.

**Production / Raspberry Pi:** `docker compose -f docker-compose.yml -f docker-compose.prod.yml up
-d`. The override file (DD-004):
- switches every service to its `prod` Dockerfile target (slim runtime, non-root user, no dev
  server),
- removes `develop.watch` (irrelevant outside local dev),
- sets `SENSOR_PROVIDER=hardware` and passes through `/dev/spidev0.0`, `/dev/gpiomem`, and
  `/sys/bus/w1` for real sensor access,
- applies memory limits per service sized to the Pi 4's 4 GB budget (§7 resource table).

**Persistence:** two named volumes — `sqlite-data` (state object store, shared by `edge`/`api`) and
`mosquitto-data` (broker persistence).

**Health checks:** every service exposes `/health` (FastAPI services) or `/healthz` (dashboard
nginx); Compose `healthcheck:` blocks gate `depends_on: condition: service_healthy` (e.g. `edge`
waits for `mosquitto`).

**No CI-driven image publishing yet** — `ci.yml`'s `docker-build` job builds every target to prove
it builds, but does not push. Publishing to a registry for actual Pi deployment is a deliberate
follow-up (§26 Future Improvements) once there's a real pilot machine to deploy to.

---

## 20. Domain-Specific Components

- **State object** (§6.0): the single source of truth synchronized by the edge layer; `api` reads
  it, `dashboard` and `copilot` consume it via `api`. Implemented end-to-end including the
  ML-derived fields (`anomaly_score`/`health_index`/`model_confidence`/`alert_level`) once
  `MLInferenceEngine` has artifacts to load (§28 Entry 13) — they stay `null` otherwise, unchanged
  from Phase 3's behavior.
- **`SensorProvider` abstraction** (DD-003, `services/edge/src/edge/providers/`): `base.py` defines
  the interface (`read() -> SensorSample`, now including `raw_vibration_window_g` for ML
  inference), `simulated.py` generates a raw window and derives features from it (matching
  `hardware.py`'s approach rather than randomizing features independently), `hardware.py` has a
  real ADXL345 register decode (DD-022) untested against real silicon (§24).
- **`MLInferenceEngine`** (`services/edge/src/edge/ml_inference.py`, §6.3, DD-031): loads
  `services/ml`'s exported ONNX models + calibration + manifest if present; computes
  anomaly_score/health_index/model_confidence/alert_level per reading. Degrades gracefully (all
  fields stay `null`) when no artifacts exist yet — the default state until `make train-synthetic`
  or a real training run happens (§24). The Isolation Forest ONNX output-name lookup is a
  documented, unverified assumption (DD-032) — this session had no way to execute the pipeline to
  confirm it.
- **Copilot retrieval/prompt-construction/fallback logic** (§6.4): implemented —
  `services/copilot/src/copilot/{retrieval,context,prompt,fallback,llm_local,llm_api,service}.py`,
  orchestrated by `QueryEngine` behind `POST /query`. Not yet exercised against a real LLM (no
  TinyLlama weights or API key present, §24); the rule-based fallback and all non-LLM logic are
  unit-tested with an injectable fake `LLMClient`.
- **SensorRAG faithfulness evaluation** (`services/copilot/src/copilot/sensorrag/`, DD-030,
  DD-033): a held-out query set (`queries.py`) spanning answerable and fallback-expected cases, a
  numeric-grounding heuristic (`grounding.py`, presence-based, not full semantic attribution — see
  DD-033), and a runner (`runner.py`) reporting fallback accuracy and hallucination rate (design.md
  §9). Runnable today against a fake/injected LLM client (proven by its own tests); running it
  against the real local/API LLM is blocked on the same missing weights/key as the copilot itself.
- **ML training pipeline** (§6.3, DD-031): implemented in `services/ml/src/ml/` — feature
  extraction, Isolation Forest, 1D conv autoencoder (PyTorch), OOD bounds, health-index
  calibration, F1 evaluation, and ONNX export, orchestrated by `pipeline.run_training_pipeline`.
  Runs end-to-end against synthetic placeholder data (`--allow-synthetic`); real CWRU/IMS parsing
  is an explicit `NotImplementedError` until those datasets are downloaded (§24) — `ml.datasets`
  raises a clear, actionable error rather than silently training on fake data by default.

---

## 21. Current Phase

**Phase 4/5 software implementation (M4–M7)** — per the delivery plan (§10). All of Phase 4's ML
pipeline and Phase 5's copilot/dashboard/SensorRAG software is now both written (§28 Entry 13) **and
verified running end-to-end in this Ubuntu Docker environment** (§28 Entry 14): `make lint`/
`typecheck`/`test` all pass, every service image builds, `make train-synthetic` produces real ONNX
artifacts, and a live `docker compose up` stack shows `edge` populating `anomaly_score`/
`health_index`/`model_confidence`/`alert_level` from those artifacts, the dashboard rendering them
in a real browser, and the copilot's `POST /query` retrieving live context and returning a correct
rule-based fallback. What still gates calling any phase *complete* is unchanged: real CWRU/IMS
datasets, real TinyLlama weights or an API key, and real ADXL345/DS18B20/pilot-machine hardware are
all still missing (§24) — this entry verifies the software against synthetic/simulated data, not
against reality.

## 22. Current Milestone

Phase 4 (ML pipeline) and Phase 5 (copilot, full dashboard) are software-complete **and verified**
as of this entry (§28 Entry 14): `make lint`, `make typecheck`, and `make test` all pass across
`apps/dashboard` and `services/{edge,api,copilot,ml}`; `docker compose build` builds all six images
(including the new `ml-trainer` profile image); `make train-synthetic` produces real ONNX artifacts
end-to-end; a live `docker compose up` stack shows `edge` loading those artifacts and populating the
previously-`null` ML fields; the dashboard was clicked through in a real browser (health gauge,
trend charts, alerts panel, historical log with filter, ROI estimator all confirmed working); and
the copilot's `POST /query` was exercised live, correctly retrieving 10 recent state objects and
falling back to a rule-based response (no LLM weights/API key configured yet, §24). Six real bugs
surfaced only by actually running the code (not discoverable by review alone) were found and fixed
— see §28 Entry 14 for the full list. See §25 for what remains genuinely unverified (real hardware,
real datasets, a real LLM call), and §28 Entry 14 for exactly what was run and what it found.

## 23. Completed Milestones

- **Engineering foundation established** (logical time 2026-07-11): Docker-first dev environment
  (`docker compose watch`), polyglot pnpm+uv monorepo, strict TS + ESLint flat config + Prettier,
  ruff + mypy strict per Python service, Husky/lint-staged/commitlint, GitHub Actions CI
  (lint/typecheck/test/build/security matrixed across 4 Python services + dashboard), CodeQL,
  Dependabot, `scripts/bootstrap.sh` onboarding, VS Code workspace config, and skeleton services
  (`edge`, `api`, `copilot`, `ml`, `dashboard`) each with a working health check and passing tests.
- **Phase 2 IoT data pipeline (software)** (logical time 2026-07-11): real ADXL345 register
  decoding + DS18B20 read in `HardwareSensorProvider` (DD-022); `RawReadingStore` SQLite
  persistence (DD-023, DD-024); an MQTT publish loop wired into `edge`'s FastAPI lifespan
  (DD-025); `ASSET_ID`/`PUBLISH_INTERVAL_SECONDS` config. Verified live end-to-end against the real
  Mosquitto broker and a persistent SQLite file, not just against mocks (see Entry 8).
- **Phase 3 state object sync + `api` read endpoints** (this work, logical time 2026-07-11):
  extended the sensor-provider interface with full vibration features (`rms_g`/`kurtosis`/
  `crest_factor`/`peak_to_peak_g`/`sampling_hz`, DD-022/§6.0) via a shared
  `compute_vibration_features` function; added `StateStore`'s `state_history` table (DD-026,
  ML-derived fields `null` until Phase 4 per DD-023's principle) and a `digital-cousin/<asset_id>/
  state` MQTT topic (DD-025) alongside the existing raw topic; implemented `api`'s `GET
  /state/current` and `GET /state/history` reading the same table via a duplicated (DD-026),
  schema-synced `StateReader`. Verified live: real HTTP requests against a running `api` container
  returning real `edge`-written rows, a 404 for an asset that never reported, and a real MQTT
  subscription to the new state topic.
- **Dashboard skeleton rendering live state** (this work, logical time 2026-07-11): `apps/dashboard`
  now polls `api`'s `GET /state/current` every 5s and renders real vibration/temperature data,
  with distinct loading/no-data/error/ready states, instead of the static placeholder. Added
  `CORSMiddleware` to `api` (DD-027) — the dashboard/api cross-origin fetch was silently blocked by
  the browser without it, caught by checking response headers with `curl -H "Origin: ..."` before
  assuming the integration worked. Verified live in an actual browser (headless Chrome against the
  running `docker compose` stack), not just via unit tests with a mocked `fetch`.
- **Phase 4 ML pipeline + Phase 5 copilot/dashboard/SensorRAG software** (written logical time
  2026-08-14, §28 Entry 13; **verified running end-to-end logical time 2026-08-15, §28 Entry 14**):
  Isolation Forest + 1D conv autoencoder training with ONNX export (DD-031), OOD bounds, health-index
  calibration, an `edge.ml_inference` module wiring trained models into the state object, a full
  copilot (retrieval/context/prompt/fallback/local-LLM/API-LLM/orchestration), the SensorRAG
  faithfulness harness (DD-030, DD-033), and the full dashboard build-out (gauge/trends/alerts/
  history log/ROI estimator). Confirmed via `make lint`/`typecheck`/`test`, `docker compose build`,
  a real `make train-synthetic` run, a live `docker compose up` stack, and a real-browser
  click-through — not just unit tests against fakes. Still blocked on real hardware/datasets/model
  weights (§24), which this entry did not and could not address.

## 24. Pending Tasks

- [x] Procure Raspberry Pi 4 (§6.2 BOM) — acquired as of this entry
- [ ] Procure remaining sensor hardware: ADXL345/MPU6050, DS18B20 (§6.2 BOM) — still blocking
      `HardwareSensorProvider` validation below
- [ ] Identify and gain access to the pilot machine (real MSME asset or lab equivalent, §11 risk)
- [ ] Validate `HardwareSensorProvider` against real hardware and a reference sensor (§10 Phase 2;
      blocked on sensor procurement above) — the register decode (DD-022) is written to the ADXL345
      datasheet but has only been exercised against a mocked SPI bus, never a real device
- [ ] Now that a real Pi is available: verify the prod Compose overlay (`docker-compose.prod.yml`)
      actually builds/runs on real ARM hardware (Cortex-A72) — this has only been exercised via
      `docker-build` CI so far, never on physical Pi silicon; sensor passthrough (`/dev/spidev0.0`
      etc.) will still fail without the sensors, but the rest of the stack can be validated now
- [ ] Tune the vibration sampling loop's real-time behavior (buffering, jitter, sample count/rate)
      once real hardware is available — DD-022 deliberately scoped Phase 2 to a correct but modest
      64-sample burst rather than a continuous 3,200 Hz stream, which needs empirical tuning
- [x] Build out the *full* dashboard (health gauge, historical trend charts, alert module, ROI
      estimator) — §6.5, implemented §28 Entry 13, **verified §28 Entry 14**: `make lint`/`typecheck`/
      `test` pass and a real-browser click-through confirmed every component renders and computes
      correctly against the live stack.
- [ ] Download/preprocess CWRU + IMS datasets into `services/ml` — still the actual blocker on real
      (non-synthetic) model training; `ml.datasets` raises a clear error until this is done, and
      `ml.pipeline`'s real-CWRU code path is an explicit `NotImplementedError` pending it (DD-031)
- [x] Implement Isolation Forest + 1D conv autoencoder training + ONNX export in `services/ml`, and
      have `edge` populate `anomaly_score`/`health_index`/`model_confidence`/`alert_level` via
      `edge.ml_inference` — §28 Entry 13 (DD-031), **verified §28 Entry 14**: `make train-synthetic`
      produces real ONNX artifacts, `edge` loads them, and DD-032's Isolation-Forest-ONNX-output-name
      lookup was confirmed correct against the real `skl2onnx`-exported model (`"scores"` output,
      matched by the `"score"` substring hint).
- [x] Run `make train-synthetic` and confirm `edge` actually loads the resulting artifacts and
      populates the state object end-to-end — §28 Entry 14; confirmed live via `GET /state/current`
      and the dashboard.
- [ ] Download TinyLlama-1.1B Q4_K_M GGUF weights (design.md §7) to exercise `COPILOT_LLM_MODE=local`
      for real, or obtain an Anthropic/OpenAI API key in `$SECRETS_FILE` to exercise
      `COPILOT_LLM_MODE=api` — the copilot's non-LLM logic is unit-tested and its retrieval/fallback
      path is now verified live end-to-end (§28 Entry 14), but no real LLM call has ever been made
      through `LocalLlamaClient`/`ApiLlmClient`
- [x] Implement copilot retrieval + prompt construction + rule-based fallback — §28 Entry 13,
      **verified §28 Entry 14**: a live `POST /query` against the running stack correctly retrieved
      10 recent state objects and returned the rule-based fallback response (no LLM configured).
- [x] Build the SensorRAG faithfulness evaluation protocol (§6.4, §9, DD-030, DD-033) — held-out
      query set, numeric-grounding heuristic, fallback-accuracy/hallucination-rate reporting, all
      proven against injected fake LLM clients in tests (§28 Entry 13, unit tests re-confirmed
      passing §28 Entry 14). **Still not run against a real LLM** (blocked on the TinyLlama-weights/
      API-key task above) — the numbers it would report today are only meaningful against fakes, not
      a real faithfulness measurement yet.
- [x] Run the full local/containerized quality gates against everything written in Entry 13
      (`make lint`, `make typecheck`, `make test`, `docker compose build`, `docker compose watch`) —
      §28 Entry 14. Found and fixed six real bugs (ESLint/ruff/mypy findings, a circular import, two
      ONNX toolchain version-skew issues, and one test-assertion bug) — see Entry 14 for the list.
- [x] Verify `apps/dashboard`'s local toolchain issue from Entry 13 (`tsc` `EPERM` errors, Node
      version mismatch) doesn't reproduce in Ubuntu — confirmed Windows-sandbox-specific; `make
      typecheck`/`make test` both pass cleanly in this Ubuntu Docker environment (§28 Entry 14).
- [ ] Add a multi-arch (`linux/arm64`) image publish workflow once ready to deploy to a real Pi (§26)
- [ ] Housekeeping: remove or relocate the untracked `digital_twin_msme_platform.git/` bare-repo
      directory at the project root (not part of the tracked project, purpose unclear — still not
      touched pending user confirmation, per Entry 12/14)
- [x] The `.husky/commit-msg`/`.husky/pre-commit`/`scripts/bootstrap.sh` executable-bit diffs from
      Entry 12 do **not** reproduce on this Ubuntu checkout (§28 Entry 14, DD-036) — confirmed via a
      clean `git diff --summary` on all three files; no `core.filemode` change needed after all. A
      *different* exec-bit issue was found instead (Husky's toolbox-container hook runs as root and
      can taint newly-created tracked files) — see the new Technical Debt item (§26) for the
      long-term fix (run the toolbox container as the host UID/GID).
- [ ] Open the PR for `feature/dashboard-live-state` (or merge it) so CI actually runs against it —
      still not done; every commit on this branch, including Entry 13/14's, has only ever been
      validated locally, never on GitHub Actions (§29).

## 25. Known Issues

- Mosquitto broker has `allow_anonymous true` and no TLS (DD-016) — acceptable only while the
  broker is unreachable outside the Docker network / Pi-local network.
- `HardwareSensorProvider.read()` is fully implemented (DD-022) but has only ever run against a
  mocked SPI bus in tests — never real ADXL345/DS18B20 hardware (procurement still pending, §24).
- No `uv.lock` / `pnpm-lock.yaml` committed as of this entry — generated and committed as part of
  validating this foundation (see §28 Development Log for the exact commands run).
- An untracked `digital_twin_msme_platform.git/` bare-repository directory exists at the project root
  (found during the 2026-08-14 audit, §28 Entry 12) — not part of the tracked project; likely a stray
  clone/backup artifact. Not deleted without user confirmation; see §24 Pending Tasks.
- `.husky/commit-msg`, `.husky/pre-commit`, `scripts/bootstrap.sh`'s executable-bit diffs from Entry
  12 (found on a Windows/NTFS checkout) are **resolved as of Entry 14** — confirmed non-reproducing
  on this Ubuntu checkout (clean `git diff --summary` on all three files); no `core.filemode` change
  was needed. See DD-036 for a related but distinct issue found this entry: Husky's own toolbox-
  container hook execution (not the checkout) can reintroduce spurious `+x` bits and root ownership
  on newly-created tracked files, worked around per-occurrence rather than fixed at the source
  (tracked as Technical Debt, §26).
- `docker-compose.yml`'s `copilot` service's dangling `deploy/secrets.env.local` fallback path
  (found in the 2026-08-14 audit) is **fixed** as of Entry 13 — now falls back to
  `./.secrets.env.local` (gitignored, a real relative path) instead of a nonexistent `deploy/`
  directory.
- **Entry 13's software is now verified end-to-end (Entry 14)** — `make lint`/`typecheck`/`test`,
  `docker compose build`, a real `make train-synthetic` run, a live `docker compose up` stack, and a
  real-browser dashboard click-through all pass; DD-032's Isolation-Forest-ONNX output-name lookup
  is confirmed correct against a real `skl2onnx` export. What's still genuinely unverified is
  strictly the pieces this entry could not exercise without real hardware/datasets/model weights:
  - No real LLM call has been made through `LocalLlamaClient`/`ApiLlmClient` — `POST /query` was
    exercised live, but only exercised the retrieval + rule-based fallback path (no TinyLlama
    weights or Anthropic/OpenAI API key configured, §24).
  - The SensorRAG faithfulness harness has only been run against injected fake LLM clients in
    tests, never a real LLM — the fallback/hallucination-rate numbers it would report today aren't
    a real faithfulness measurement yet.
  - `HardwareSensorProvider` is still only exercised against a mocked SPI bus, never real ADXL345/
    DS18B20 silicon (hardware procurement still pending, §24).
  - The real (non-synthetic) CWRU/IMS training path (`ml.pipeline` without `--allow-synthetic`) is
    still an explicit `NotImplementedError` — only the synthetic-data path has actually run.

## 26. Technical Debt

- The Makefile's `lint` target doesn't run `format:check` or `knip`, both of which are required
  gates in the same CI job (`.github/workflows/ci.yml`'s TypeScript job runs format:check → lint →
  typecheck → test → knip in sequence) — found in Entry 15 when PR #61's first CI run failed on
  `format:check` despite a clean local `make lint`. Add both to a combined local target so this
  local/CI gap doesn't recur.
- Mosquitto authentication/TLS deferred until the broker is ever exposed beyond localhost/LAN.
- `api`'s CORS policy allows all origins (DD-027) — same localhost/LAN-only reasoning as the
  Mosquitto item above; revisit together if this API is ever exposed beyond localhost/LAN.
- No CI image-publishing workflow yet (builds are verify-only); needed before real Pi deployment.
- `docker-compose.prod.yml` device passthrough (`/dev/spidev0.0`, `/dev/gpiomem`) is hard-coded to
  the default SPI bus/device — revisit if the retrofit protocol (§11) ends up needing configurable
  bus addressing across different pilot machines.
- Coverage thresholds (60% dashboard, 70% Python services) are placeholders sized for the current
  skeleton; raise as real feature code lands.
- The dashboard's historical log/trend charts (§6.5) are bounded by `api`'s `GET /state/history`
  1000-row cap, not the originally-scoped 24h window — needs pagination or a time-range query
  parameter on that endpoint to actually reach 24h at realistic publish intervals.
- SensorRAG's numeric-grounding check (DD-033) verifies a claimed number is present in the retrieved
  context, not that it's attributed to the *correct* field — a response could quote a real context
  number but apply it to the wrong claim and still pass. Full claim-level semantic grounding needs
  entity linking, out of scope for this pass.
- The `toolbox` container (and any `docker compose run`) runs as root by default, including when
  Husky's pre-commit hook shells into it (§7.6) — every hook-triggered `git`/file-write operation
  leaves files and `.git` internals root-owned on the host, which then blocks the next host-side
  `git` command until manually `chown`'d back (DD-036, found and worked around repeatedly in Entry
  14). Fix at the source: run toolbox/compose invocations with `--user "$(id -u):$(id -g)"` (or bake
  a matching non-root user into `docker/tools.Dockerfile`) so this stops recurring.

## 27. Future Improvements

- Add a `docker-publish.yml` (manual dispatch) workflow for multi-arch (`linux/amd64`+`linux/arm64`)
  builds pushed to GHCR, once there's a pilot machine to deploy to.
- Consider Turborepo once a second TypeScript package exists (DD-013).
- Consider InfluxDB OSS if SQLite query complexity grows, per §7's original stack note.
- Add mosquitto auth (username/password or client certs) before any non-localhost exposure.
- Add an end-to-end test harness (e.g. Playwright) once the dashboard has real UI beyond the
  current placeholder.

---

## 28. Development Log

### Entry 1 — Phase 1, M1–M2 (logical project time: 2026-07-11)

**Task completed:** Established the production engineering foundation (Docker-first dev
environment, polyglot pnpm+uv monorepo, quality gates, CI/CD, bootstrap tooling) per the
foundation-only scope agreed with the user — no application features implemented.

**Files created:** `.editorconfig`, `.gitignore`, `.gitattributes`, `.dockerignore`,
`.env.example`, `package.json`, `pnpm-workspace.yaml`, `tsconfig.base.json`, `eslint.config.js`,
`.prettierrc.json`, `.prettierignore`, `.lintstagedrc.json`, `commitlint.config.js`, `knip.json`,
`Makefile`, `ruff.toml`, `docker-compose.yml`, `docker-compose.prod.yml`,
`docker/tools.Dockerfile`, `.husky/{pre-commit,commit-msg}`, `.vscode/{settings,extensions}.json`,
`.github/workflows/{ci,codeql}.yml`, `.github/dependabot.yml`, `.github/PULL_REQUEST_TEMPLATE.md`,
`README.md`, `scripts/bootstrap.sh`, `infra/mosquitto/mosquitto.conf`,
`apps/dashboard/**` (Vite+React+TS scaffold, Dockerfile, nginx.conf, sample test),
`services/{edge,api,copilot,ml}/**` (pyproject.toml, `src/` package, `tests/`, Dockerfile). Full
tree in §14.

**Files modified:** `design.md` (this document — §7.6, §14–§29 added).

**Files deleted:** none.

**Reason for change:** User requested a production-grade engineering foundation
("`git clone && ./scripts/bootstrap.sh && docker compose watch`, no host installs beyond Docker")
per CLAUDE.md's documentation-first workflow. Before implementing, flagged and resolved a real
mismatch between the requested Node/TS-centric tooling (pnpm, strict TS, ESLint flat config,
Docker Compose watch) and the project's actual mostly-Python stack (§7) via three clarifying
questions — resolved as: polyglot monorepo, pluggable hardware/simulated sensor abstraction, and
minimal-skeleton service code (see DD-002, DD-003 and this entry's scope).

**Architectural decisions:** See §15 DD-001 through DD-016.

**Remaining work:** See §24 Pending Tasks. Immediately next: run `pnpm install` / `uv sync` per
service to generate and commit lockfiles, then validate `docker compose build`, `docker compose
watch`, lint/typecheck/test, and the git hooks end-to-end (tracked as this entry's validation pass
— results appended to this log once complete).

**Known issues:** See §25.

**Recommended next task:** Complete the validation pass (lockfiles + `docker compose build` +
quality gates), then move to Phase 1's remaining deliverables — hardware procurement and pilot
machine identification (§24) — before starting Phase 2 (IoT data pipeline) implementation.

### Entry 2 — Phase 1, M1–M2 (logical project time: 2026-07-11, same day)

**Task completed:** Full validation pass of the engineering foundation from Entry 1 — lockfile
generation, quality gates, and an actual end-to-end run of `docker compose watch` (not just static
review). Found and fixed two real bugs that static review missed.

**Files created:** `pnpm-lock.yaml`, `services/{edge,api,copilot,ml}/uv.lock` (generated, then
committed for deterministic installs per DD-001).

**Files modified:**
- `pnpm-workspace.yaml` — added `allowBuilds: {esbuild: true, unrs-resolver: true}` (pnpm 11 blocks
  postinstall scripts by default; both are legitimate: esbuild is Vite's bundler, unrs-resolver is
  eslint-plugin-import-x's resolver).
- `package.json`, `apps/dashboard/package.json` — added `"type": "module"` to silence a Node ESM
  warning on `eslint.config.js`/`commitlint.config.js`.
- `.prettierignore` — added `CLAUDE.md` (hand-maintained instructions file, not ours to reformat).
- `apps/dashboard/vite.config.ts` — coverage `exclude` now spreads `coverageConfigDefaults.exclude`
  instead of replacing it (was silently un-excluding config/type-declaration files from the "all
  files" coverage scan); added `src/main.tsx` (untestable bootstrap entrypoint) to the exclude list
  after the first `pnpm run test` run correctly failed the coverage gate on it.
- `knip.json` — added `ignoreDependencies` for `@commitlint/cli`/`lint-staged` (used only via
  `.husky/*` hooks, which knip's static analysis doesn't trace) and `ignoreBinaries: ["ruff"]` (an
  external Python binary, not an npm package); removed a redundant explicit `entry` that knip's
  Vite plugin already infers.
- **`apps/dashboard/Dockerfile`** (real bug): `tsconfig.base.json` was only `COPY`'d in the `build`
  stage, not `deps` (inherited by `dev`) — the `dev` target crashed on boot with
  `failed to resolve "extends": "../../tsconfig.base.json"` the moment Vite tried to transform any
  file. Moved the `COPY` up to `deps` so both `dev` and `build` get it. Caught by actually booting
  `docker compose watch` and hitting the dashboard, not by `docker compose build` succeeding (the
  image built fine — the failure was only at container *runtime*).
- **`docker-compose.prod.yml`** (real bug): `dashboard.ports` in the override only added `8080:8080`
  under Compose's default merge-by-append behavior, so the prod container ended up with both the
  stale dev mapping (`5173:5173`, nothing listens on it in the `prod` nginx image) and the real one.
  Fixed with the `ports: !override` YAML tag so the override *replaces* rather than merges. Caught
  by inspecting `docker compose -f ... -f docker-compose.prod.yml ps` output, not by `config
  --quiet` (which validates syntax, not the merged semantics).
- **`docker-compose.yml`** (real bug): `docker compose run --rm --no-deps toolbox pnpm exec
  lint-staged` failed non-interactively with `[ERR_PNPM_ABORTED_REMOVE_MODULES_DIR_NO_TTY]` — pnpm
  wanted to confirm a `node_modules` recreation and had no TTY to ask in (`docker compose run`
  without `-it`). Added `environment: CI: "true"` to the `toolbox` service, which is pnpm's own
  documented fix for this exact error. This is the mechanism the Husky hooks (`.husky/pre-commit`,
  `.husky/commit-msg`) depend on, so this bug would have made every commit hang or fail.

**Files deleted:** none.

**Reason for change:** CLAUDE.md's validation checklist requires proving `docker compose watch`,
hot reload, and git hooks actually work — not just that files parse or images build. Static
correctness (Dockerfile syntax, Compose YAML validity) does not imply runtime correctness; two of
the three bugs above (`tsconfig.base.json`, the ports merge) had 100% clean `docker compose build`
and `docker compose config --quiet` output and would only surface when a developer actually ran
`docker compose watch` or deployed to prod.

**Architectural decisions:** No new DDs — all fixes are corrections of Entry 1's implementation
against its own stated design, not new decisions.

**What was actually verified, end to end, in this session (not just "should work"):**
- `pnpm install` → lockfile generated, Husky `prepare` hook ran successfully.
- `pnpm run format:check`, `lint`, `typecheck`, `test` (with coverage thresholds), `knip` — all
  green on the real toolchain (pnpm 11.11.0, Node 24 host / Node 22 containers, ESLint 9.39.4,
  TypeScript 5.9.3, Vitest 2.1.9, knip 5.88.1).
- Each of `services/{edge,api,copilot,ml}`: `uv sync --group dev`, `mypy .` (strict, 0 errors),
  `pytest` (coverage ≥70% gate met in every service), `ruff check` + `ruff format --check` — all
  green. `services/ml`'s `torch==2.13.0+cpu` confirmed resolving from the CPU wheel index (DD-011),
  not a multi-GB CUDA build.
- `docker compose build` for all four app/service `dev` targets and all four `prod` targets, plus
  `docker/tools.Dockerfile` — all succeed.
- `docker compose config --quiet` for both the base file and the `-f docker-compose.yml -f
  docker-compose.prod.yml` merge (including the `!reset`/`!override` YAML tags).
- `docker compose up -d`: all five dev services (`mosquitto`, `edge`, `api`, `copilot`, `dashboard`)
  reach `healthy`; `edge`'s `depends_on: mosquitto: condition: service_healthy` correctly gated its
  start until the broker was healthy; hit `/health` on `api`/`copilot` and `/` on the dashboard.
- `docker compose watch`: edited `apps/dashboard/src/App.tsx` and `services/api/src/api/main.py`
  while the stack was running under `watch` and confirmed both changes propagated live (dashboard:
  Vite HMR via `develop.watch` sync; api: `uvicorn --reload` picked up the synced file) without any
  manual rebuild — this is the literal `docker compose watch` requirement from the task, verified
  live rather than assumed from the compose file's `develop.watch` blocks.
- Prod overlay (`docker-compose.prod.yml`) brought up for `dashboard`/`api`/`copilot`/`mosquitto`
  (excluding `edge`, which needs real `/dev/spidev0.0` + `/dev/gpiomem` device access on a real Pi —
  not available in this dev environment, so DD-003's provider abstraction remains unverified against
  real hardware, only against the compose device-passthrough wiring itself) — all reached `healthy`,
  including the nginx-served dashboard on its production port 8080.
- Husky wiring: confirmed `core.hooksPath` points at `.husky/_` and its dispatch shims exist for
  every git hook Husky manages. Ran the *underlying* commands the hooks invoke
  (`docker compose run --rm --no-deps toolbox pnpm exec lint-staged`/`commitlint`) directly rather
  than through a real `git commit`, to validate the mechanism without creating a commit the user
  didn't ask for. `commitlint` correctly accepted a valid Conventional Commit message and rejected
  an invalid one with the expected `subject-empty`/`type-empty` errors.

**Remaining work:** Same as Entry 1 §24, plus: `hadolint` was checked only via CI config, not run
locally against the Dockerfiles in this session (deferred, not blocking — CI's `dockerfile-lint`
job covers it on the first push). Recommend running `make lint`/`make typecheck`/`make test` (the
containerized path via the toolbox) at least once before relying on it, in addition to the host-run
validation done here, since the two Dockerfile/Compose bugs above prove build success does not
guarantee runtime success.

**Known issues:** See §25 — none newly introduced; the two bugs found here are already fixed, not
outstanding.

**Recommended next task:** Unchanged from Entry 1 — hardware procurement and pilot machine
identification (§24), then Phase 2.

### Entry 3 — Phase 1, M1–M2 (logical project time: 2026-07-11, same day)

**Task completed:** Fixed the CI `dockerfile-lint` (hadolint) job failure surfaced on the first
GitHub Actions run of the branch pushed in Entry 1/2. The matrix job for `services/edge/Dockerfile`
failed (`failure-threshold: warning` in `.github/workflows/ci.yml`, so any warning fails the job);
the other five matrix jobs showed as skipped/cancelled in the run, not actually passing, since
GitHub Actions matrix jobs cancel siblings on a first failure by default (`fail-fast: true`). This
is exactly the gap Entry 2 flagged as deferred/unverified ("hadolint was checked only via CI config,
not run locally").

**Files modified:** `services/edge/Dockerfile`, `services/api/Dockerfile`,
`services/copilot/Dockerfile`, `apps/dashboard/Dockerfile`, `docker/tools.Dockerfile` — added
`# hadolint ignore=DL3008` above each `apt-get install` line (DL3008: "Pin versions in apt get
install"). `services/ml/Dockerfile` has no `apt-get install` and needed no change.

**Files created/deleted:** none.

**Reason for change:** See DD-017. Verified the fix by running `docker run --rm -i hadolint/hadolint
< <file>` against all six Dockerfiles locally (hadolint was not installed as a host binary) — all
six now produce zero output (no warnings or errors), matching what `failure-threshold: warning`
requires to pass in CI.

**Architectural decisions:** DD-017 (§15).

**Remaining work:** Same as Entry 2 — hardware procurement and pilot machine identification (§24).
Recommend re-running the full `dockerfile-lint` matrix in CI (push or re-run the workflow) to
confirm all six jobs go green together, since this session validated locally via `docker run
hadolint/hadolint`, not by observing a fresh Actions run.

**Known issues:** None newly introduced.

**Recommended next task:** Push/re-run CI to confirm the full `dockerfile-lint` matrix passes, then
proceed to hardware procurement and pilot machine identification (§24), then Phase 2.

### Entry 4 — Phase 1, M1–M2 (logical project time: 2026-07-11, same day)

**Task completed:** Fixed the two CI failures that surfaced on the next Actions run after Entry 3
(confirmed via the CI UI that the full `dockerfile-lint` matrix now passes, closing Entry 3's
Remaining work): `Dependency audit` (`pnpm audit --audit-level=high`) and `Trivy filesystem scan`
(`container-scan` job), both of which were failing `CI status`'s aggregate gate.

**Files modified:**
- `apps/dashboard/package.json` — `vite` `^5.4.11` → `^6.4.3`, `vitest` `^2.1.5` → `^3.2.7`,
  `@vitest/coverage-v8` `^2.1.5` → `^3.2.7`.
- `pnpm-workspace.yaml` — added `overrides.vite: ^6.4.3` (see DD-018 for why the direct bump alone
  was insufficient).
- `pnpm-lock.yaml` — regenerated via `docker compose run --rm --no-deps toolbox pnpm install
  --no-frozen-lockfile` (the toolbox container owns `node_modules` as root per DD-005's tooling
  model, so the lockfile must be regenerated inside it, not from the host).
- `.github/workflows/ci.yml` — `container-scan` step `uses: aquasecurity/trivy-action@0.29.0` →
  `@v0.29.0`.

**Files created/deleted:** none.

**Reason for change:** See DD-018 (dependency audit: `vite` GHSA-fx2h-pf6j-xcff high,`vitest`
GHSA-5xrq-8626-4rwp moderate, both fixed upstream) and DD-019 (Trivy: broken action ref, not a real
scan finding — the job failed before Trivy executed).

**Architectural decisions:** DD-018, DD-019 (§15).

**What was actually verified, end to end, in this session:**
- `pnpm why vite` showed two resolved copies (`5.4.21` via `vitest`'s internal `vite-node`/
  `@vitest/mocker`, `6.4.3` direct) before the override; exactly one (`6.4.3`) after — the override
  was necessary, not just the direct version bump.
- `pnpm audit --audit-level=high` (containerized toolbox): "No known vulnerabilities found" after
  the override, versus 4 vulnerabilities (1 high, 3 moderate) before it.
- `pnpm run typecheck`, `pnpm run lint`, `pnpm run test` (containerized toolbox) all green on the
  bumped `vite@6.4.3`/`vitest@3.2.7` — dashboard test suite still 100% coverage, no ESLint or `tsc`
  regressions from the major-version bumps.
- `docker compose build dashboard` succeeds — the `dev`/`prod` image stages still build cleanly
  against the new lockfile.
- Confirmed `aquasecurity/trivy-action`'s real git tags (`v0.18.0`…`v0.36.0`, all `v`-prefixed) via
  `git ls-remote --tags`, and that `v0.29.0`'s `action.yaml` still accepts every input this workflow
  passes (`scan-type`, `scan-ref`, `severity`, `exit-code`, `skip-dirs`) — the fix is a pure ref
  correction, not an inputs/behavior change.
- Not verified in this session: an actual Trivy filesystem scan run (no local `trivy` binary
  available; the fix was validated by confirming the action ref resolves and its inputs are
  unchanged at that tag, not by executing a scan).

**Remaining work:** Same as Entry 3 — hardware procurement and pilot machine identification (§24).
Recommend one more CI run to confirm `Dependency audit`, `Trivy filesystem scan`, and `CI status`
all go green together, since Trivy itself was not executed locally.

**Known issues:** None newly introduced.

**Recommended next task:** Push/re-run CI to confirm the full pipeline is green, then proceed to
hardware procurement and pilot machine identification (§24), then Phase 2.

### Entry 5 — Phase 1, M1–M2 (logical project time: 2026-07-11, same day)

**Task completed:** Repository reorganization to production-grade layout conventions, per user
request. Audited the full tracked file tree first (`git ls-files`) and found it already conformed:
source code was already under `apps/`/`services/`, repo-level config was already at root, and no
stray documentation existed outside `design.md` (no loose research notes, hardware datasheets, or
ADR-shaped writeups anywhere in the repo). The only real gap was that `docs/` and `packages/`
(the latter already referenced by `pnpm-workspace.yaml`'s `packages/*` glob per DD-013) didn't
exist yet. Asked the user how far to take `design.md` specifically (leave whole at root / move
whole / split its sections across the new `docs/` subfolders) since CLAUDE.md makes it the single
authoritative, append-only engineering-memory file, not ordinary documentation — user chose to
leave it whole and at root.

**Files created:** `docs/architecture/README.md`, `docs/adr/README.md`, `docs/research/README.md`,
`docs/hardware/README.md`, `packages/README.md` — each a short stub naming the folder's purpose,
the `design.md` section it currently supersedes-from (until content actually outgrows that
section), and the promotion rule for when to add real files there.

**Files modified:** `README.md` (Repository layout section lists the new folders), `design.md`
(§14 Repository Structure updated to match; this entry and DD-020 added).

**Files deleted/moved:** none — this was additive scaffolding, not a file migration, since nothing
in the existing tree was out of place.

**Reason for change:** See DD-020.

**Architectural decisions:** DD-020 (§15).

**Remaining work:** Same as Entry 4. Additionally: `docs/adr/`, `docs/research/`, `docs/hardware/`,
and `packages/` are intentionally empty scaffolding — no content was extracted from `design.md`.
Populate them opportunistically per each folder's README (e.g. move DD-020 itself to a full ADR
file if its rationale ever needs more than the one-line table entry).

**Known issues:** None newly introduced.

**Recommended next task:** Push/re-run CI to confirm the full pipeline is green (unchanged from
Entry 4), then hardware procurement and pilot machine identification (§24), then Phase 2.

### Entry 6 — Phase 1, M1–M2 (logical project time: 2026-07-11, same day)

**Task completed:** Investigated and fixed the failing `Dependency audit` GitHub Actions job
(`run_id=29141265728`, `job_id=86514811281`). Pulled the job logs and confirmed `pnpm audit` was
already clean; the failure occurred only in the Python audit stage when `pip-audit` attempted to
create a temporary virtual environment and failed inside `ensurepip` (non-zero exit `127`).

**Files created:** none.

**Files modified:** `.github/workflows/ci.yml` (dependency-audit step now exports requirements with
`--no-emit-project` and runs `uvx pip-audit --no-deps -r /tmp/reqs.txt` for each service).

**Files deleted/moved:** none.

**Reason for change:** `uv export --format requirements-txt` can include `-e .` (the local project),
which is not a published package artifact and causes `pip-audit` install/hash validation paths to
fail in CI. Exporting with `--no-emit-project` removes that local editable line, and `--no-deps`
keeps `pip-audit` from performing unnecessary dependency resolution/virtualenv bootstrap against an
already fully resolved lockfile export.

**Architectural decisions:** none new; aligns with DD-015's dependency-auditing approach while
making the CI invocation deterministic on hosted runners.

**Remaining work:** Re-run CI to confirm the `Dependency audit` job is green end-to-end on GitHub
Actions.

**Known issues:** None newly introduced.

**Recommended next task:** Re-run the `CI` workflow and verify all required checks pass, then
continue with §24 Pending Tasks.

### Entry 7 — Phase 1, M1–M2 (logical project time: 2026-07-11, same day)

**Task completed:** Entry 6's fix did not actually resolve the `Dependency audit` failure — the user
reported "same error persists" with a fresh screenshot showing the identical `ensurepip` exit-127
traceback on the commit containing Entry 6's change. Entry 6's diagnosis (a `-e .` editable-install
line from `uv export`, fixed by adding `--no-emit-project`/`--no-deps`) was incomplete: `--no-deps`
does not skip `pip-audit`'s internal venv bootstrap (only `--disable-pip` does — confirmed by
reading `pip_audit/_dependency_source/requirement.py` directly), so the same `ensurepip` failure
was always going to persist regardless of `--no-emit-project`. Root-caused for real this time by
reproducing locally (`uv`/`uvx` 0.5.9 on the host, no CI needed): `strace -f` showed the venv's
`python3.11` process `execve`-succeeding then immediately `exit_group(127)` with zero output;
manually replicating `venv.EnvBuilder(with_pip=True).create()` in isolation (bypassing
`check_output`'s captured-but-unprinted `.output`) surfaced the real error: `error while loading
shared libraries: .../lib/libpython3.11.so.1.0: cannot open shared object file`. Confirmed via `ls`
that the venv's `bin/python3.11` was a real copied file (not a symlink) missing its own `lib/`
sibling — `EnvBuilder(with_pip=True)` defaults `symlinks=False`, and uv's managed CPython needs
`$ORIGIN`-relative access to that sibling dir. A first attempted fix (`UV_PYTHON_PREFERENCE=
only-system` to sidestep uv's relocatable build entirely) traded this bug for a second one: the
runner's system Python has no `python3.11`, so `uv export` itself failed with "No interpreter found
for Python ==3.11.*" when the env var scope leaked onto it; narrowing the scope to just the `uvx
pip-audit` call fixed that, but then exposed a *third* issue — `services/ml`'s `uv export` hashes
are locked to cp311 wheels only, so auditing under the system's cp312 Python made pip reject the
hash-mismatched `scipy` wheel and fall back to a source build, which failed on a missing Fortran
compiler (`gfortran`/`ifx`/etc. all absent). Abandoned that approach entirely once
`pip_audit/_dependency_source/requirement.py` revealed `--disable-pip` as the actually-intended
escape hatch for pre-resolved, fully-hashed input — it skips venv creation altogether, fixing all
three problems at once. Separately, also caught that DD-019's `container-scan` fix (Entry 4) only
addressed the missing `v` prefix on `aquasecurity/trivy-action@v0.29.0` — that specific release
still failed with "Unable to resolve action `aquasecurity/setup-trivy@v0.2.2`", a *second*, deeper
bug: `v0.29.0`'s own composite action pins its internal `setup-trivy` dependency to a tag that's
since been deleted upstream. Repinned to `v0.36.0`, which pins that same internal dependency by
commit SHA instead of a mutable tag.

**Files modified:** `.github/workflows/ci.yml` — `dependency-audit`'s `pip-audit` step now runs
`uvx pip-audit --no-deps --disable-pip -r /tmp/reqs.txt` (added `--disable-pip`); `container-scan`
repinned `aquasecurity/trivy-action@v0.29.0` → `@v0.36.0`.

**Files created/deleted:** none.

**Reason for change:** See DD-021 (supersedes DD-019's trivy fix and corrects Entry 6's incomplete
`pip-audit` diagnosis).

**Architectural decisions:** DD-021 (§15).

**What was actually verified, end to end, in this session:**
- Reproduced the exact CI failure locally (same `uv`/`uvx` version, 0.5.9) without needing a CI run,
  via `strace -f -e trace=execve,exit_group` and by manually invoking
  `venv.EnvBuilder(with_pip=True).create()` in isolation to surface the suppressed shared-library
  error.
- Confirmed all four services (`api`, `copilot`, `edge`, `ml`) pass `uv export ... | uvx pip-audit
  --no-deps --disable-pip -r ...` with exit code 0, in seconds rather than minutes (no venv/pip
  bootstrap at all) — `ml`'s `torch==2.13.0+cpu` is correctly skipped with a "not found on PyPI"
  notice (expected: local-version identifiers from the CPU wheel index, DD-011, aren't on PyPI) and
  does not fail the job.
- Confirmed `aquasecurity/setup-trivy`'s real tags (`v0.2.6`, `v0.3.0`, `v0.3.1` — `v0.2.2` is gone)
  via `git ls-remote --tags`, and that `trivy-action@v0.36.0`'s `action.yaml` pins that dependency by
  commit SHA and still accepts every input this workflow passes (`scan-type`, `scan-ref`,
  `severity`, `exit-code`, `skip-dirs`).
- Validated `.github/workflows/ci.yml`'s full YAML syntax via `yaml.safe_load` after editing.
- Not verified in this session: an actual Trivy scan run, or the `dependency-audit` job on the real
  GitHub Actions runner image specifically (as opposed to this local reproduction) — recommend one
  more CI run to close this out for real this time.

**Remaining work:** Push/re-run CI to confirm `Dependency audit`, `Trivy filesystem scan`, and `CI
status` all go green together — this is now the third attempt, so treat "green in the Actions UI"
as the actual completion signal, not local reproduction alone. Then hardware procurement and pilot
machine identification (§24), then Phase 2.

**Known issues:** None newly introduced. Note for future debugging in this repo: `pip-audit`
failures that show a bare `CalledProcessError` with no subprocess output are almost certainly
swallowing real diagnostic text in `.output`/`.stderr` — reproduce locally and catch the exception
directly rather than trusting the traceback shown in CI logs.

**Recommended next task:** Confirm the CI run is fully green, then hardware procurement and pilot
machine identification (§24), then Phase 2.

### Entry 8 — Phase 2, M2–M3 (logical project time: 2026-07-11, same day)

**Task completed:** Started Phase 2 (IoT data pipeline, §10) — implemented the sensor-firmware and
MQTT/SQLite parts of `services/edge` that don't require physical hardware in hand. User asked to
"start Phase 1"; clarified via a question that they meant the next coding phase (Phase 2 per
design.md's own numbering, since Phase 1 per §21-24 was already engineering-foundation-complete
with only physical procurement left, which isn't a code task).

**Files created:** `services/edge/src/edge/storage.py` (`RawReadingStore`), `services/edge/tests/
test_hardware_provider.py`, `services/edge/tests/test_storage.py`, `services/edge/tests/
test_publish_loop.py`.

**Files modified:**
- `services/edge/src/edge/providers/hardware.py` — replaced the `NotImplementedError` stub with a
  real ADXL345 SPI register decoder (DATA_FORMAT/BW_RATE/POWER_CTL init, 3.9 mg/LSB full-res scale,
  DD-022) and a real DS18B20 read via `w1thermsensor`.
- `services/edge/src/edge/main.py` — added `read_and_publish_once`/`publish_loop`, wired into the
  FastAPI lifespan alongside a `paho-mqtt` client (`connect_async`+`loop_start`, so a
  not-yet-reachable or absent broker never crashes startup — verified by the fact unit tests pass
  with zero broker running) and a `RawReadingStore`. New module-level config: `ASSET_ID`,
  `MQTT_TOPIC`, `PUBLISH_INTERVAL_SECONDS`.
- `docker-compose.yml` — `edge.environment` gained `ASSET_ID` and `PUBLISH_INTERVAL_SECONDS`.
- `.env.example` — documented `ASSET_ID`.

**Files deleted:** none.

**Reason for change:** See DD-022 (register decode + sampling scope), DD-023 (raw vs. full state
schema), DD-024 (`:memory:` test default), DD-025 (MQTT topic scheme).

**Architectural decisions:** DD-022 through DD-025 (§15).

**What was actually verified, end to end, in this session:**
- `uvx ruff@0.8.0 check`/`format --check`, `uv run mypy .` (strict, 0 errors), `uv run pytest` — all
  green; 8 tests, 96.58% coverage (gate is 70%). Caught and fixed one real mypy error along the way:
  `paho.mqtt.client.CallbackAPIVersion` is an implicit re-export under `--strict`'s
  `--no-implicit-reexport`, fixed by importing it from its actual home, `paho.mqtt.enums`.
- `HardwareSensorProvider` tested against a hand-built fake `spidev`/`w1thermsensor` (injected via
  `sys.modules`, since the real `hardware` extra is Pi-only and not installed here): asserted the
  exact three register writes (`DATA_FORMAT`, `BW_RATE`, `POWER_CTL`) and hand-verified the RMS math
  against a deterministic alternating two-value sample sequence (expected `0.0195`, matched).
- `docker compose build edge` succeeds; brought up `mosquitto`+`edge` for real via `docker compose
  up -d`, both reached `healthy`. Subscribed to `digital-cousin/motor_01/raw` from inside the
  mosquitto container and captured a real published message. Queried `/data/digital_cousin.sqlite3`
  from inside the running edge container directly and confirmed 9 rows had accumulated at the
  expected 5-second cadence (`PUBLISH_INTERVAL_SECONDS`). Checked `docker compose stop`'s logs and
  confirmed a clean lifespan shutdown (task cancellation, no hang, no traceback) rather than an
  assumed-clean teardown.
- Not verified in this session (blocked on hardware, tracked in §24): anything against a real
  ADXL345/DS18B20 — `HardwareSensorProvider` is only proven against a mocked SPI bus.

**Remaining work:** See §24 — hardware procurement/pilot machine identification (unblocks real-
hardware validation of this session's work), then the rest of Phase 2/3 (state object sync, `api`
read endpoints).

**Known issues:** None newly introduced.

**Recommended next task:** Hardware procurement and pilot machine identification (§24) to unblock
validating `HardwareSensorProvider` for real; in parallel, Phase 3's state-object sync and `api`
read endpoints can proceed against the `simulated` provider.

### Entry 9 — Phase 3, M3–M4 (logical project time: 2026-07-11, same day)

**Task completed:** Phase 3's state object sync and `api` read endpoints (§10), continuing directly
from Entry 8 since Phase 2's hardware-validation items remain blocked on procurement. Also: created
branch `feature/phase-3-state-sync-api` for this work rather than committing to `main` directly, per
user instruction to always branch for new feature work going forward.

**Files created:** `services/edge/src/edge/features.py` (`compute_vibration_features`),
`services/edge/tests/test_features.py`, `services/api/src/api/storage.py` (`StateReader`),
`services/api/tests/test_state.py`.

**Files modified:**
- `services/edge/src/edge/providers/base.py` — added `VibrationFeatures`; `SensorSample.
  vibration_rms_g` (flat) replaced with `SensorSample.vibration: VibrationFeatures` (nested).
- `services/edge/src/edge/providers/simulated.py` — generates all four vibration features,
  `peak_to_peak_g` derived from `crest_factor`/`rms_g` for internal consistency rather than
  independently randomized.
- `services/edge/src/edge/providers/hardware.py` — `read()` now calls
  `compute_vibration_features` on its 64-sample burst instead of inlining an RMS-only calculation;
  extracted `_SAMPLING_HZ = 800` as a named constant.
- `services/edge/src/edge/storage.py` — added `StateStore` (`state_history` table, DD-026) and
  `state_row_to_dict`, alongside the unchanged Phase 2 `RawReadingStore`.
- `services/edge/src/edge/main.py` — `read_and_publish_once`/`publish_loop` now take both stores;
  each cycle logs to `state_history` in addition to `raw_readings`, and publishes to a new
  `digital-cousin/<asset_id>/state` MQTT topic (full state object) alongside the existing
  `.../raw` topic (unchanged raw payload, DD-025).
- `services/api/src/api/main.py` — replaced the bare health-only app with a FastAPI lifespan
  managing a `StateReader`, plus `GET /state/current` (404 if nothing recorded) and `GET
  /state/history?limit=N` (default 100, capped at 1000).
- `docker-compose.yml` — `api.environment` gained `ASSET_ID` (matching `edge`'s existing default).
- `services/edge/tests/test_hardware_provider.py`, `test_publish_loop.py`, `test_storage.py` —
  updated for the nested `vibration` accessor and the dual-store/dual-topic publish flow.

**Files deleted:** none.

**Reason for change:** See DD-026 (state_history schema duplication + `api`'s idempotent
`CREATE TABLE IF NOT EXISTS` for start-order independence) and DD-022 (feature math now shared via
`edge.features` instead of inlined in `hardware.py`).

**Architectural decisions:** DD-026 (§15).

**What was actually verified, end to end, in this session:**
- `uvx ruff@0.8.0 check`/`format --check`, `uv run mypy .` (strict, 0 errors) for both `edge` and
  `api`. `uv run pytest`: edge 14 tests / 97.45% coverage, api 5 tests / 100% coverage (gate 70%
  both).
- `compute_vibration_features` cross-checked against a hand-computed 4-sample window (rms, kurtosis
  = 7/3, crest_factor = sqrt(3), peak-to-peak all matched exactly) — decoupled from the ADXL345/SPI
  mocking so the math itself has an independent, easy-to-verify test.
- `docker compose build edge api` succeeded; brought up `mosquitto`+`edge`+`api` for real via
  `docker compose up -d`, all three reached `healthy`.
- Hit the running `api` container's real HTTP endpoints: `GET /state/current` returned a real
  `edge`-written reading (200, correct `vibration` sub-object, `anomaly_score`/`health_index`/etc.
  all `null` as designed); `GET /state/history?limit=3` returned 3 rows, most-recent-first, values
  matching what was independently queried straight out of `/data/digital_cousin.sqlite3` inside the
  edge container; `GET /state/current?asset_id=nonexistent_machine` returned a real 404.
- Subscribed to `digital-cousin/motor_01/state` from inside the mosquitto container and captured a
  real published full state object (not just the raw topic from Entry 8).
- Checked `docker compose stop`/`logs` for both services and confirmed clean lifespan shutdown (no
  hangs, no tracebacks) rather than assuming it from Entry 8's edge-only precedent.

**Remaining work:** See §24. Hardware procurement/pilot machine identification still gates real
`HardwareSensorProvider` validation. Next unblocked software work: the dashboard skeleton (Phase
3/5, still a placeholder) rendering live data from the two new `api` endpoints, or starting Phase 4
(CWRU/IMS dataset work in `services/ml`) — both are independent of the hardware-blocked items.

**Known issues:** None newly introduced.

**Recommended next task:** Either wire the dashboard to `api`'s new `/state/*` endpoints (closes
out Phase 3's last software deliverable), or start Phase 4 dataset work in `services/ml` — both
unblocked; hardware procurement/pilot machine identification (§24) remains the standing blocker for
everything hardware-specific.

### Entry 10 — Phase 3, M3–M4 (logical project time: 2026-07-11, same day)

**Task completed:** Wired the dashboard to `api`'s new `/state/*` endpoints, closing out Phase 3's
last remaining deliverable (§10: "dashboard skeleton rendering live data"). Continuing the branch-
per-feature workflow from Entry 9: PR #32 (Phase 3 backend) had been merged to `main` by the user in
the interim, so this work started from a fresh `feature/dashboard-live-state` branch off the
updated `main`, deleting the now-merged `feature/phase-3-state-sync-api` branch first.

**Files created:** `apps/dashboard/src/api.ts` (`fetchCurrentState`, `DigitalTwinState`/
`VibrationFeatures` types, DD-028), `apps/dashboard/src/api.test.ts`.

**Files modified:**
- `apps/dashboard/src/App.tsx` — replaced the static placeholder with a polling component (5s
  interval, matching `PUBLISH_INTERVAL_SECONDS`'s default) with four explicit states (loading/
  no-data/error/ready), rendering the real vibration/temperature fields and an honest note that
  anomaly detection isn't available yet when `health_index` is `null`.
- `apps/dashboard/src/App.test.tsx` — updated for the new polling/rendering behavior (mocks
  `./api`'s `fetchCurrentState`, preserving the real `NoStateError` via `importOriginal`).
- `apps/dashboard/src/vite-env.d.ts` — typed `ImportMetaEnv.VITE_API_URL`.
- `services/api/src/api/main.py` — added `CORSMiddleware` (`allow_origins=["*"]`, GET only,
  DD-027) — **a real bug caught before it shipped**, not a preemptive addition: the dashboard/api
  fetch is cross-origin (`localhost:5173` → `localhost:8000`), and `curl -H "Origin: ..."` against
  the running `api` container showed no `access-control-allow-origin` header before this change,
  which would have silently broken in any real browser despite every `curl`-based check up to this
  point succeeding.

**Files deleted:** none. (Local branch `feature/phase-3-state-sync-api` deleted after confirming
`git merge-base --is-ancestor` showed it fully merged into `main`.)

**Reason for change:** See DD-027 (CORS), DD-028 (third schema-duplication location).

**Architectural decisions:** DD-027, DD-028 (§15).

**What was actually verified, end to end, in this session:**
- `pnpm run lint`/`typecheck`/`test` (containerized toolbox) all green — caught and fixed two real
  ESLint errors along the way (`@typescript-eslint/no-empty-function` on a deliberately-never-
  resolving test Promise, fixed with a targeted disable comment; `@typescript-eslint/
  restrict-template-expressions` on a numeric template literal, fixed with `String(...)`). 7 tests,
  100%/88.88%/100%/100% coverage (gate 60%).
- `docker compose build dashboard`, then brought up `mosquitto`+`edge`+`api`+`dashboard` for real.
- **Caught the missing-CORS bug before declaring success**: `curl -i -H "Origin: http://
  localhost:5173" http://localhost:8000/state/current` showed no CORS header pre-fix (would pass in
  any non-browser check, silently fail in a real browser) — added `CORSMiddleware`, rebuilt/
  redeployed `api`, re-ran the same `curl` and confirmed `access-control-allow-origin: *` present.
- **Verified in an actual browser, not just curl or unit tests**: `google-chrome --headless=new
  --virtual-time-budget=8000 --dump-dom http://localhost:5173/` against the live stack — the
  dumped DOM showed the real rendered state (`motor_01`, real vibration/temperature values, the
  "anomaly detection isn't available yet" message), proving the cross-origin fetch actually
  succeeds end-to-end in a real browser engine, which a mocked-fetch unit test or a `curl` check
  alone cannot prove.
- Checked both `dashboard` and `api` container logs for errors post-verification — clean.

**Remaining work:** See §24. Hardware procurement/pilot machine identification remains the standing
blocker for real-hardware validation. Phase 3 is now fully done; next phases are independent of
each other and of the hardware blocker: Phase 4 (CWRU/IMS dataset work + Isolation Forest/
autoencoder training in `services/ml`), Phase 5's full dashboard (gauges/trends/alerts/ROI) and
copilot retrieval.

**Known issues:** None newly introduced.

**Recommended next task:** Start Phase 4 (`services/ml` dataset preprocessing) — it's the next
sequential phase per §10 and is fully unblocked (no hardware dependency, `simulated` provider
already produces plausible vibration data for pipeline development).

### Entry 11 — Phase 3, M3–M4 (logical project time: 2026-07-11, same day)

**Task completed:** Full re-verification audit of everything built through Phase 3, at the user's
explicit request ("check everything properly is everything until phase 3 done perfectly"). Not a
new feature — re-ran every quality gate and every runtime check across the whole repo, including
combinations not previously exercised together (all 5 services at once; the prod Compose overlay
rebuilt for real rather than reusing a stale dev-target image). Found and fixed one real,
previously-undetected bug.

**Files modified:** `docker-compose.prod.yml` (dashboard healthcheck `localhost` → `127.0.0.1`,
DD-029).

**Files created/deleted:** none.

**Reason for change:** See DD-029.

**Architectural decisions:** DD-029 (§15).

**What was actually checked, and what it found:**
- **Local quality gates, containerized (matching CI's exact invocation), for every service, not
  just the ones touched this session:** `make lint`, `make format-check`, `make typecheck`, `make
  test`, `make knip` — all green. Along the way, discovered and fixed an unrelated *environmental*
  problem (not a code bug): earlier sessions had run `uv sync`/`mypy`/`pytest` directly on the host
  for speed, leaving host-created `.venv` directories that the containerized toolbox then failed to
  replace (`Directory not empty`). Removed them (confirmed gitignored first) and reran `make
  typecheck` clean from a fresh container-created venv — this is what a contributor following
  DD-001 ("Docker-first, no host installs") would actually experience, so it needed to work via the
  toolbox specifically, not just via host `uv run`.
- **Every Docker image and target CI builds** (`apps/dashboard` dev+prod, `services/{edge,api,
  copilot}` prod, `services/ml`, `docker/tools.Dockerfile`) — all 7 build clean via plain `docker
  build`, independent of `docker compose build`'s caching.
- **hadolint** against all six Dockerfiles directly (`docker run --rm -i hadolint/hadolint`) — zero
  output on all six, independent of CI.
- **Security scans, run locally rather than trusted from a prior CI green:** `gitleaks detect` (18
  commits, no leaks), `pip-audit --disable-pip` for all four Python services (clean; `torch`
  correctly skipped as before), `pnpm audit --audit-level=high` (clean), and a real `trivy fs` scan
  of the whole repo (0 vulnerabilities, 0 secrets across all five lockfiles) — this was the first
  time Trivy was actually run in this project rather than only relied upon via CI.
- **`docker compose config` validation** for both the base file and the `-f ... -f
  docker-compose.prod.yml` merge.
- **All five services running simultaneously for the first time** (previous sessions had only
  tested subsets: edge+mosquitto, edge+api+mosquitto, edge+api+dashboard+mosquitto) — `copilot` had
  never been part of a live multi-service check before. All five reached `healthy`; hit every
  `/health` endpoint (correcting an initial mistake of curling the same host-mapped port twice
  under the mislabeled belief one of them was `edge`'s — `edge` has no host-mapped port by design,
  confirmed its actual health via `docker exec`), confirmed `copilot`'s `API_URL` wiring reaches
  `api` over the Docker network, and re-confirmed `/state/current`/`/state/history` and the
  dashboard's live render (headless Chrome) all still work with the full stack up, not just pairs.
  All five containers' logs checked for errors/warnings — clean.
- **The prod Compose overlay, rebuilt for real this time**: an initial `docker compose -f ... -f
  docker-compose.prod.yml up -d` (without `--build`) silently reused the cached *dev*-target image
  (`vite --host 0.0.0.0` on port 5173), not the prod nginx image — a testing-methodology mistake
  caught by noticing the running command didn't match what `target: prod` should produce. Re-ran
  with `--build`, which surfaced DD-029's real bug: the prod dashboard's healthcheck was failing
  every single time (`FailingStreak` accumulating, `wget: Connection refused`) even though the
  container was serving traffic correctly on the host side. Diagnosed via `getent hosts localhost`
  (returned only `::1`), `wget http://127.0.0.1:8080` (succeeded) vs. `wget http://localhost:8080`
  (failed) run directly inside the container, and inspection of the nginx config (`listen 8080;`,
  IPv4-only). Fixed, rebuilt, and confirmed all four prod-overlay services (dashboard included)
  reach `healthy` and `curl http://localhost:8080/healthz` still returns `ok`.
- **Confirmed CI is actually green on GitHub, not just assumed from local checks:** `gh run list`
  showed the `CI`/`CodeQL` workflows completed `success` on both the `feature/phase-3-state-sync-
  api` PR and on `main` after its merge. Explicitly noted: `feature/dashboard-live-state` (this
  session's other branch, not touched further here) has no open PR yet, so CI has never run against
  it — only local checks (all green, see Entry 10) have validated that work so far.

**Remaining work:** See §24 — unchanged; this entry found and fixed one bug but didn't add new
scope. Recommend opening a PR for `feature/dashboard-live-state` so CI validates it for real,
matching the standard this audit just re-confirmed for everything merged so far.

**Known issues:** DD-029's bug is fixed as of this entry, not outstanding. No issues discovered by
this audit remain open.

**Recommended next task:** Open the PR for `feature/dashboard-live-state` (or merge it) so CI
covers it; then Phase 4 (`services/ml` dataset work), unchanged from Entry 10's recommendation.

### Entry 12 — Phase 3, M3–M4 (logical project time: 2026-08-14)

**Task completed:** User supplied a literature survey PDF (`LS_V2.pdf`) describing it as "the latest
finalized architecture and build" and asked for a full repo audit against it, with changes documented
in a new `to_do.md` and updates to `design.md`/`CLAUDE.md`. Extracted the PDF's actual text (10 pages,
pypdf) rather than trusting the filename/framing, and determined it is an academic literature-survey
paper (IEEE-style, 5 authors, 30 surveyed works + 2 benchmarking sources, a six-property research-gap
matrix) — not a new architecture or build specification. Cross-checked every hardware/software detail
it references against §1–§13 of this document and found all of it already present (same PRD v2.0
content design.md already carries). Then independently audited the actual repository: `git ls-files`
full tree diffed against §14, `git status`/`git diff` for uncommitted changes, and — after the user
asked for confirmation this was a full pass and not just a directory-listing check — **every one of
the ~75 tracked files was read in full** (all Python/TS source and tests across `edge`/`api`/
`copilot`/`ml`/`dashboard`, every Dockerfile, both compose files, both GitHub Actions workflows, the
Makefile, `bootstrap.sh`, every root/tooling config file, all four `docs/*/README.md` stubs, and
`packages/README.md`) against design.md's own claims (§14, §20, §24, §29). Found no drift — the repo
matches the documentation exactly (Phase 3 complete, ML/copilot still skeletons, hardware validation
still blocked on procurement per §24) — plus one additional minor finding only visible at full-content
read depth: `docker-compose.yml`'s `copilot.env_file` fallback path `./deploy/secrets.env.local`
doesn't correspond to any real directory (§25).

**Files created:** `to_do.md` (chronological action-item list synthesizing §24 Pending Tasks with the
newly identified SensorRAG evaluation work, for at-a-glance tracking without reading the full §24
prose).

**Files modified:** `design.md` (§3 Objective 7, §6.4 SensorRAG protocol subsection, §8 Novelty 5, §9
faithfulness metric row, §24 two new pending items, §25 two new known issues, DD-030, this entry,
§29), `CLAUDE.md` (added a pointer to `to_do.md` as design.md's companion action-item list).

**Files deleted:** none. (Untracked `digital_twin_msme_platform.git/` and the three executable-bit-only
diffs found during the audit were left untouched — flagged in §24/§25 for user confirmation, not
acted on unilaterally since their origin/purpose is unclear.)

**Reason for change:** See DD-030. The audit found zero architecture drift between the repo and
design.md, and zero new build requirements from the PDF beyond confirming the existing architecture —
the only real gap was a missing requirement (SensorRAG faithfulness evaluation) that the PDF itself
identifies as the project's primary novel research contribution, which had no corresponding entry
anywhere in design.md's objectives, copilot design, evaluation metrics, or pending tasks.

**Architectural decisions:** DD-030 (§15). No architecture changed — only a previously-undocumented
evaluation requirement was added.

**What was actually verified in this session:** PDF text extracted and read in full (not summarized
from the filename/user framing); full `git ls-files` tree diffed against §14 line-by-line; `git status`
and `git diff` run to catch any uncommitted drift design.md might not reflect (found the stray
`digital_twin_msme_platform.git/` directory and the three mode-only diffs this way). Initially only
spot-read two "skeleton-only" files as a sample; the user then explicitly asked whether this was a
full-codebase pass or just a doc/tree check — it was the latter, so every one of the ~75 tracked files
was subsequently read in full (not just listed): `services/edge/src/edge/{main,features,storage}.py`
+ `providers/{base,simulated,hardware}.py` + all 5 test files; `services/api/src/api/{main,storage}.py`
+ both test files; `services/copilot/src/copilot/main.py` + its test + `pyproject.toml`; `services/ml/
src/ml/pipeline.py` + its test + `pyproject.toml`; `apps/dashboard/src/{App,api,main}.{ts,tsx}` +
`setupTests.ts` + `vite-env.d.ts` + both test files + `vite.config.ts` + `tsconfig.json` + `index.html`;
all 6 Dockerfiles; both compose files; both GitHub Actions workflows; `Makefile`, `scripts/
bootstrap.sh`, `infra/mosquitto/mosquitto.conf`, `.env.example`; every root tooling config
(`package.json`, `pnpm-workspace.yaml`, `tsconfig.base.json`, `eslint.config.js`, `ruff.toml`,
`knip.json`, `.lintstagedrc.json`, `commitlint.config.js`, both Husky hook scripts, `.prettierrc.json`,
`.prettierignore`, `.gitignore`, `.gitattributes`, `.dockerignore`, `.editorconfig`, `.vscode/*.json`,
`.github/dependabot.yml`, `.github/PULL_REQUEST_TEMPLATE.md`); `README.md`; all four `docs/*/README.md`
stubs and `packages/README.md`; and every service's `__init__.py`. This full-content pass (not just the
tree-level check) is what surfaced the `deploy/secrets.env.local` dangling-path finding above — the
tree/prose-level check alone would have missed it.

**Remaining work:** Unchanged from Entry 11/§24, plus the two new items this entry added: build the
SensorRAG faithfulness evaluation protocol (depends on Phase 5 copilot retrieval existing first), and
resolve the two housekeeping findings (stray bare-repo directory, executable-bit diffs) with the user.

**Known issues:** See §25 — two new items added this entry (stray directory, executable-bit diffs),
neither newly *introduced* by this session, both newly *discovered*.

**Recommended next task:** Unchanged from Entry 11 — open the PR for `feature/dashboard-live-state`,
then Phase 4 (`services/ml` dataset work). The SensorRAG evaluation work and housekeeping items are
independent of that critical path and can be picked up whenever convenient.

### Entry 13 — Phase 4/5 software implementation (logical project time: 2026-08-14, same day)

**Task completed:** User asked to "apply all the changes to follow the new plan and blueprint" — i.e.
implement `to_do.md`'s roadmap from Entry 12, not just plan it. Scoped via two `AskUserQuestion`
prompts first: which pieces to build (user: all of them, in priority order) and how to resolve the
TFLite-vs-available-tooling gap flagged in Entry 12's audit (user: pick the Recommended option,
ONNX — DD-031). Implemented in priority order: (1) housekeeping, (2) the full dashboard build-out
(§6.5), (3) the ML training pipeline (§6.3, DD-031), (4) wiring `edge` to consume the ML pipeline's
ONNX artifacts, (5) the copilot (§6.4), (6) the SensorRAG faithfulness harness (§6.4, §9, DD-030,
DD-033). Partway through, the user clarified twice: don't push/commit yet without being asked (later
explicitly requested, not yet acted on — see Remaining work), and — critically — **don't run, install,
or test anything**, since they'd set up the real runtime environment in Ubuntu and would verify there
themselves. That instruction, plus this session's own environment lacking a reachable Docker daemon
and having a broken local Node toolchain (`node_modules` `EPERM` stat errors, host Node v20 vs. the
project's required ≥22), means **everything below was written and reasoned through carefully but never
executed even once** — see §22/§25 for the explicit list of what that leaves unverified.

**Files created:**
- Housekeeping: none (edits only).
- Dashboard (§6.5): `apps/dashboard/src/thresholds.ts` (+`.test.ts`),
  `apps/dashboard/src/components/{HealthGauge,TrendChart,AlertsPanel,HistoryLog,RoiEstimator}.tsx`
  (each +`.test.tsx`).
- ML pipeline (§6.3, DD-031): `services/ml/src/ml/{features,synthetic,datasets,isolation_forest,
  autoencoder,ood,health_index,evaluate}.py` (each with a matching `tests/test_*.py`).
- Edge ML wiring: `services/edge/src/edge/ml_inference.py` (+`tests/test_ml_inference.py`, which
  hand-builds tiny stub ONNX graphs via the `onnx` library rather than depending on `services/ml`'s
  sklearn/torch stack, keeping the two services independent per DD-002).
- Copilot (§6.4): `services/copilot/src/copilot/{retrieval,context,prompt,fallback,llm_local,llm_api,
  service}.py` (each with a matching test file) and `services/copilot/tests/test_main.py`.
- SensorRAG (DD-030, DD-033): `services/copilot/src/copilot/sensorrag/{__init__,queries,grounding,
  runner}.py` (+`tests/test_sensorrag_{grounding,runner}.py`).

**Files modified:**
- `docker-compose.yml` — fixed the dangling `deploy/secrets.env.local` fallback (→
  `./.secrets.env.local`); added `ML_ARTIFACTS_DIR` env var + a read-only bind mount of
  `./services/ml/artifacts` into `edge` (the same host path `ml-trainer` already writes into).
- `.gitignore` — added `.secrets.env.local`.
- `Makefile` — added `train-synthetic` (runs `ml.pipeline --allow-synthetic`; plain `make train`
  stays mapped to the real, currently-blocked CWRU path, per `ml.datasets`' "fail loudly by default"
  design intent).
- `apps/dashboard/src/{api,App}.ts(x)` (+ their `.test` files) — added `fetchStateHistory`; `App.tsx`
  now polls both current state and history and renders all five new dashboard components.
- `services/edge/src/edge/providers/base.py` — `SensorSample` gained `raw_vibration_window_g`
  (the raw magnitude window `vibration` was computed from, needed by the autoencoder).
- `services/edge/src/edge/providers/simulated.py` — now generates a raw window and derives its four
  features from it via the real `compute_vibration_features` (matching `hardware.py`'s approach),
  instead of randomizing `rms_g`/`kurtosis`/`crest_factor` independently and deriving
  `peak_to_peak_g` from `crest_factor` as an approximation.
- `services/edge/src/edge/providers/hardware.py` — populates the new `raw_vibration_window_g` field.
- `services/edge/src/edge/storage.py` — `StateStore.insert` gained an optional `ml_result` parameter,
  writing `anomaly_score`/`health_index`/`model_confidence`/`alert_level` when present (unchanged
  `NULL` behavior when absent, DD-023's principle preserved).
- `services/edge/src/edge/main.py` — loads an `MLInferenceEngine` at startup (or disables inference
  gracefully if no artifacts exist yet); `read_and_publish_once`/`publish_loop` run inference per
  reading, with the same log-and-continue failure handling as a sensor read failure.
- `services/edge/pyproject.toml`, `services/ml/pyproject.toml` — added `onnxruntime` (edge, runtime)
  and `onnx` (edge, dev-only, DD-032's test stub graphs) / `onnx`+`skl2onnx` (ml) + matching mypy
  `ignore_missing_imports` overrides.
- `services/edge/tests/test_storage.py` — updated `SensorSample(...)` construction sites for the new
  required field.
- `services/copilot/src/copilot/main.py` — added `POST /query` (lifespan-managed `QueryEngine`).
- `services/ml/src/ml/pipeline.py` (+`tests/test_pipeline.py`) — replaced the version-string stub
  with the real `run_training_pipeline` orchestrator (bumped `pipeline_version()` to `"0.2.0"`).
- `design.md` — this entry, plus §3/§6.3/§6.4/§6.5/§7/§14/§15 (DD-031–DD-033)/§16/§17/§20/§21/§22/
  §23/§24/§25/§26, updated throughout to describe what's now implemented vs. still blocked.
- `to_do.md` — housekeeping items checked off (see below).

**Files deleted:** none.

**Reason for change:** See DD-031 (ONNX over TFLite — user's explicit pick from the `AskUserQuestion`
prompt), DD-032 (Isolation Forest ONNX output-name lookup — an unverified assumption, documented as
such rather than presented as certain, since this session could not execute the pipeline to confirm
it), DD-033 (SensorRAG's grounding check is presence-based, not full semantic attribution — a
deliberate, documented scope limit, not an oversight).

**Architectural decisions:** DD-031, DD-032, DD-033 (§15).

**What was actually attempted for verification, and why it stopped where it did:**
- Housekeeping: `chmod 755` and `git update-index --chmod=+x` were both tried on the three
  executable-bit-diffed files — neither actually fixed the underlying issue (see §25); reverted to
  the original unstaged state rather than leaving a half-fix, since forcing the index without the
  worktree agreeing would have been misleading, not a real fix.
- Attempted `npx tsc --version`/`node --version`/`pnpm --version`/`docker info` on the host to see
  what could be verified directly: host Node is v20.17.0 (pnpm 11 needs ≥22.13), the local
  `node_modules` throws `EPERM` on `fs.realpathSync` when `tsc` tries to resolve `typescript` (a
  broken/inaccessible install, not attributable to anything done this session), and `docker info`
  fails (`DOCKER_NOT_REACHABLE`) — none of the three obvious "just check it compiles" paths worked.
- Installed `pytest`/`mypy`/`ruff`/`onnx`/`onnxruntime`/`skl2onnx` into the host's Python 3.12 (which
  already had `numpy`/`scikit-learn`/`torch`/`fastapi`/`httpx` present) specifically to actually run
  the new Python code — this was in progress (one `pip install` had completed) when the user's
  explicit "dont run anything" instruction arrived; no test suite was ever executed as a result, and
  every Python module written after that point was reasoned through by hand instead, not run.
- No attempt was made to verify the TypeScript dashboard code by any other means (no alternate
  Node install, no online playground, no manual AST-level review beyond careful reading) once the
  local toolchain was confirmed broken and before the "don't run anything" instruction made the
  point moot regardless.

**Remaining work:** See the rewritten §24 — in priority order: run the full quality gates
(`make lint`/`make typecheck`/`make test`, `docker compose build`, `docker compose watch`) against
everything in this entry, since none of it has executed even once; run `make train-synthetic` to
confirm the ML pipeline actually produces valid ONNX artifacts and that `edge` loads them correctly
end-to-end; then the still-unchanged hardware/dataset/model-weight blockers from Entry 12. The user
also asked this session to commit and push (Conventional Commits style matching `git log`, no
Claude co-author line) — not yet done as of this entry; recommend doing so only after at least
`make lint`/`make typecheck` pass in Ubuntu, given how much of this has never been executed.

**Known issues:** See §25 — this entire entry's code is unverified; specific unverified assumptions
listed there (DD-032's ONNX output-name lookup, the autoencoder's never-run forward pass, `sensorrag`/
`llm_local`/`llm_api` never imported by a running process, the dashboard never type-checked/rendered).

**Recommended next task:** In the user's Ubuntu environment: `make lint && make typecheck && make
test` first (cheapest, fastest signal), then `docker compose build` and `make train-synthetic`, then
`docker compose watch` for a live end-to-end check including the dashboard in an actual browser. Fix
whatever those surface before considering any of §6.3/§6.4/§6.5's Entry 13 work "done" rather than
"written."

---

### Entry 14 — Phase 4/5 verification (logical project time: 2026-08-15)

**Task completed:** Executed to_do.md §0's verification checklist against Entry 13's previously-unrun
software — `make lint`/`make typecheck`/`make test`, `docker compose build` (all six images,
including the `training`-profile `ml-trainer`), `make train-synthetic`, a live `docker compose up`
stack, a real-browser dashboard click-through, DD-032's ONNX output-name lookup, and a live
`POST /query` against the copilot — and committed the (now-passing) result to git.

**Files created:** None (pure verification + bugfix pass on Entry 13's files; docs updates below).

**Files modified (bugfixes found only by actually running the code — not visible from review alone):**
- `apps/dashboard/src/components/HealthGauge.tsx` — `viewBox` template literal used the bare numeric
  constant `SIZE` directly; `@typescript-eslint/restrict-template-expressions` flagged the numeric
  literal type, fixed by wrapping in `String(...)` (matching the file's own existing convention two
  lines below for the `transform` attribute).
- `apps/dashboard/src/components/RoiEstimator.tsx` — `onSubmit={(event) => event.preventDefault()}`
  is a void-returning arrow shorthand, forbidden by `@typescript-eslint/no-confusing-void-expression`;
  wrapped in braces.
- `apps/dashboard/src/components/RoiEstimator.test.tsx` — the "starts at zero" test used
  `screen.getByText("₹0.00")`, ambiguous because *both* the downtime-cost and savings `<dd>` render
  `₹0.00` at the default inputs; fixed to `getAllByText(...)` asserting length 2. A real test bug,
  not a component bug — `vitest run` failed before this fix.
- `services/copilot/tests/test_main.py`, `services/edge/src/edge/ml_inference.py`,
  `services/edge/tests/test_ml_inference.py`, `services/ml/src/ml/autoencoder.py` — ruff `E501`
  (line too long) and one `I001` (unsorted imports, `services/ml/src/ml/isolation_forest.py`,
  auto-fixed via `ruff check --fix`).
- `services/edge/src/edge/ml_inference.py` — two mypy `no-any-return` errors: `_output_name_containing`
  returned `output.name`/`outputs[-1].name` directly, both typed `Any` by onnxruntime's stubs;
  fixed with an explicit `str` variable annotation and an explicit `str(...)` call respectively.
- `services/ml/src/ml/ood.py`, `services/ml/src/ml/isolation_forest.py` — mypy `no-any-return`:
  `np.any(...)`/`model.score_samples(...)` both returned `Any` per numpy/sklearn's stubs; fixed with
  explicit `NDArray[...]`-annotated intermediate variables.
- `services/ml/src/ml/autoencoder.py` — mypy `no-any-return` on `forward`'s `decoded` (annotated);
  mypy `no-untyped-call` on `loss.backward()` (torch's stub doesn't type it — `# type: ignore
  [no-untyped-call]`, matching the existing `# type: ignore[...]` convention already used elsewhere
  in `services/edge/tests/`); mypy `arg-type` on `torch.onnx.export`'s second positional argument,
  which expects a `tuple[Any, ...]` not a bare `Tensor` — wrapped `dummy_input` in a 1-tuple.
- `services/edge/src/edge/providers/__init__.py` — the circular-import fix, DD-035.
- `services/ml/src/ml/isolation_forest.py` — the `target_opset` pin, DD-034.
- `services/ml/pyproject.toml`, `services/ml/uv.lock`, `services/edge/uv.lock` — `onnxscript`
  dependency addition (DD-034) and lockfile regeneration from the `uv sync` runs this entry actually
  executed (Entry 13 never ran `uv sync`, so these lockfiles were stale relative to their own
  `pyproject.toml`'s already-declared `onnxruntime`/`onnx` entries).
- `docker-compose.yml`, `CLAUDE.md`, `Makefile`, and every file Entry 13 touched — spurious
  `100644→100755` mode-only diffs (Windows/NTFS artifact predating this entry, distinct from
  DD-036's new toolbox-container finding) reset to `100644` before staging; zero content change.
- `design.md`, `to_do.md` — this entry, plus §15 (DD-034–DD-036), §21/§22/§23/§24/§25/§26/§29.

**Files deleted:** None. (The untracked `digital_twin_msme_platform.git/` directory remains
untouched, still pending user confirmation per Entry 12 — not part of this entry's scope.)

**Reason for change:** The user asked to verify Entry 13's work, run all tests, and push — this
entry is exactly that verification pass, executed for real (working Docker daemon, working Node
toolchain) after Entry 13 had to skip it entirely.

**Architectural decisions:** DD-034 (ONNX toolchain version-skew fixes), DD-035 (edge circular-import
fix), DD-036 (Docker-toolbox-runs-as-root ownership artifact, distinct from the Entry-12 Windows
exec-bit issue which turned out **not** to reproduce here).

**What was actually run, in order, and what it found:**
1. `docker compose build toolbox` — built clean.
2. `make lint` — failed twice (2 TS errors, then 5 Python ruff errors across 4 files); fixed both
   rounds, then passed clean.
3. `make typecheck` — failed (7 mypy errors across `edge`/`ml`, TS clean throughout); fixed all 7,
   then passed clean (5/22/15/19 source files across the four Python services, TS `tsc --noEmit`
   clean).
4. `make test` — failed three ways: 1 dashboard test assertion bug (RoiEstimator), 2 ML export
   failures (skl2onnx opset mismatch, missing onnxscript), and 1 edge collection error (the
   circular import). Fixed all four; re-run showed all 8 dashboard test files / 33 tests and all
   four Python services' suites passing with coverage above each service's configured floor
   (dashboard 98.66%, api 100%, copilot 73.88%, edge 95.34%, ml 95.92%).
5. `docker compose build` (default profile) + `docker compose --profile training build ml-trainer` —
   all six images built clean.
6. `make train-synthetic` — produced `services/ml/artifacts/{isolation_forest.onnx,
   autoencoder.onnx (+.onnx.data), manifest.json, health_index_calibration.json}`; reported
   `isolation_forest_f1=0.787`, `autoencoder_f1=0.995` against synthetic data (not §9's real-data
   target — expected, `used_synthetic_data: true` in the manifest makes that explicit).
7. `docker compose up -d` — host port 8000 collided with an unrelated local project's container
   (`mybill-api-1`, unrelated to this repo); resolved with a local-only, uncommitted compose override
   remapping `api`'s host port to 18000 and pointing the dashboard's `VITE_API_URL` at it — a test-
   environment workaround only, no committed file changed, `docker-compose.yml` itself still
   publishes `8000:8000` for real deployments. All 5 containers reported healthy.
8. `GET /state/current` — confirmed `anomaly_score`/`health_index`/`model_confidence`/`alert_level`
   all populated (not `null`): e.g. `anomaly_score: -0.046`, `health_index: 1.0`,
   `model_confidence: "high"`, `alert_level: "normal"`.
9. DD-032 check: `docker exec`'d into the running `edge` container and inspected the real
   `isolation_forest.onnx`'s output names directly via `onnxruntime` — `["label", "scores"]`. The
   `"score"` substring hint correctly matches `"scores"` over `"label"`; the lookup is confirmed
   correct, not just plausible.
10. Dashboard click-through in the Browser pane at `http://localhost:5173` — health gauge rendered
    (SVG, correct color banding), both trend charts rendered as SVG polylines with live-updating
    "last N readings" counts, alerts panel showed "No active alerts" (correctly, all synthetic
    readings were in-range), historical log populated live and showed the alert-level filter
    dropdown with all four options, and the ROI estimator computed `₹100000.00`/`₹30000.00` from
    `1000×100` cost/hours and the default 30% reduction — matched hand-calculation exactly.
11. `POST /query` against the live `copilot` container — `{"answer": "...check the dashboard
    directly...", "used_fallback": true, "context_size": 10}`: confirmed live retrieval (10 recent
    state objects fetched from `api`) and correct fallback behavior (no LLM configured, §24).
12. `docker compose down`, throwaway-container ownership fixes (DD-036), then committed.

**Remaining work:** See the rewritten §24 — in priority order: download CWRU/IMS datasets, download
TinyLlama weights or configure an API key, procure remaining sensor hardware, and open the PR for
`feature/dashboard-live-state` so CI actually runs against all of this (still only validated
locally, per §29).

**Known issues:** See §25 (updated) — the only genuinely-unverified items left are the ones that
need real hardware, real datasets, or a real LLM; everything software-only that could be exercised
in this environment now has been.

**Recommended next task:** Open the PR for `feature/dashboard-live-state` (§24) so this entry's
commits actually run through GitHub Actions CI, not just local verification — that's the one
verification layer this entry couldn't reach from a local Docker environment.

---

### Entry 15 — CI verification (logical project time: 2026-08-15, same day)

**Task completed:** Opened PR #61 for `feature/dashboard-live-state` (per Entry 14's recommended
next task) and fixed everything its first CI run caught that local verification hadn't: a
`prettier --check` failure on `to_do.md` and a `pnpm audit --audit-level=high` failure (DD-037).

**Files modified:**
- `to_do.md` — a stray 2-space continuation-line indent (inconsistent with the file's own 6-space
  convention elsewhere) that `prettier --write` needed two passes to fully normalize.
- `pnpm-workspace.yaml`, `pnpm-lock.yaml` — six new `overrides` entries (DD-037) for CVEs disclosed
  in transitive dev-tooling dependencies since this branch's `pnpm-lock.yaml` was last regenerated
  (2026-07-11) — unrelated to any code in this branch, same category as DD-018's existing `vite`
  override.
- `apps/dashboard/src/thresholds.ts` — dropped `export` from `DashboardAlert` (knip: unused outside
  its own module — `AlertsPanel.tsx` consumes `evaluateAlerts`'s return type by inference, never
  imports the type by name). Genuinely dead surface area, not a false positive.

**Files created/deleted:** None.

**Reason for change:** CI is a real verification layer local Docker execution can't fully replicate
— specifically, `pnpm audit` queries a live advisory database, so a lockfile that was clean when
last regenerated can start failing the same check weeks later with zero code change, and CI runs
`knip`/`format:check` in the same job as lint/typecheck/test where this session's local `make lint`
target does not (§7.6's Makefile only wires up `lint`, not `format-check`/`knip`, into the primary
gate command run in Entry 14 — a gap worth closing, see §26).

**Architectural decisions:** DD-037 (pnpm audit override fixes, including two real mistakes made and
corrected in the process — see the DD itself for the exact failure modes and how each was confirmed).

**Remaining work:** Confirm PR #61's CI run is fully green after this entry's push (not yet
confirmed as of writing — this entry fixed the two known failures locally but hasn't re-run them
through GitHub Actions yet). See §24.

**Known issues:** Local `make lint`/`make test` do not run `format:check` or `knip`, both of which
are required CI gates in the same `ci.yml` job — worth adding both to the Makefile's `lint` target
(or a new combined target) so this gap doesn't recur. Tracked as Technical Debt (§26).

**Recommended next task:** Verify PR #61 is green on GitHub Actions; if so, merge or continue
iterating per §24's remaining priorities (CWRU/IMS datasets, TinyLlama weights, hardware
procurement).

---

## 29. Current Repository State

- **Branch:** `feature/dashboard-live-state`, pushed to `origin` but **no PR opened yet** — CI has
  not run against this branch's commit (Entry 10); everything on it is validated locally only, per
  Entry 11's audit. `main` tracks `origin/main` and is confirmed CI-green (Entry 11).
  `feature/phase-3-state-sync-api` (PR #32) was merged and deleted before this branch was created.
- **Remote:** `https://github.com/samarthkolur/digital_twin_msme_platform.git`.
- **Commit history:** single "first commit" (CLAUDE.md, design.md, initial `.gitattributes`/
  `.gitignore`) predates this entry; this engineering-foundation work is the first substantial
  change on top of it.
- **Toolchain versions pinned:** Node `>=22` in containers (`packageManager: pnpm@11.11.0` via
  corepack; host validation used Node 24, which is forward-compatible), Python `3.11` (matching the
  Raspberry Pi OS Lite target in §7), `uv` `0.5.9`, `ruff` `0.8.0`.
- **Lockfiles committed:** `pnpm-lock.yaml` and `services/{edge,api,copilot,ml}/uv.lock`, generated
  and verified during Entry 2's validation pass — `docker compose build`/`bootstrap.sh` use these
  with `--frozen-lockfile`/`uv sync`, not floating resolution.
- **`edge`, `api`, and `dashboard` now have real application logic** (Entry 8 Phase 2, Entries 9-10
  Phase 3, DD-022 through DD-028): real ADXL345/DS18B20 sensor decoding + full vibration feature
  extraction, an MQTT publish loop (raw + state topics), SQLite `raw_readings`/`state_history`
  persistence, `api`'s `GET /state/current`/`GET /state/history` (with CORS enabled, DD-027), and a
  dashboard that polls and renders that live state — all verified live (real Mosquitto broker, real
  HTTP requests, a real headless-Chrome render). Still not implemented: ML training and copilot
  retrieval logic (Phase 4/5, §24); `anomaly_score`/`health_index`/`model_confidence`/`alert_level`
  stay `null` until then. `copilot` and `ml` still only expose their foundation-phase skeletons.
  Phase 3 (§10) is now fully complete.
- **Engineering foundation is runtime-verified, not just statically reviewed** (Entry 2): `docker
  compose watch` hot reload, health-gated startup ordering, the prod Compose overlay, and the Husky
  → toolbox → lint-staged/commitlint hook chain were all exercised live, and two real bugs surfaced
  only by doing so (see Entry 2) — both fixed before this entry.
- **All six Dockerfiles pass hadolint** (Entry 3, DD-017): verified locally via `docker run --rm -i
  hadolint/hadolint < <file>` for `apps/dashboard`, `services/{edge,api,copilot,ml}`, and
  `docker/tools.Dockerfile` — zero output on all six, and confirmed green on the actual
  `dockerfile-lint` CI matrix in the run following Entry 3 (closing that entry's Remaining work).
- **Dashboard on `vite@6.4.3`/`vitest@3.2.7`** (Entry 4, DD-018), with a `pnpm-workspace.yaml`
  `overrides.vite` pin so vitest's internal `vite-node`/`@vitest/mocker` can't drag in the older,
  vulnerable `vite@5.4.21` transitively — `pnpm audit --audit-level=high` clean as of this entry.
- **Dependency-audit `pip-audit` step fixed for real** (Entry 7, DD-021, supersedes Entry 6):
  `--disable-pip` skips `pip-audit`'s internal venv bootstrap entirely, avoiding the `ensurepip`
  exit-127 failure (uv's managed CPython's `$ORIGIN`-relative shared lib breaks when
  `EnvBuilder(with_pip=True)` copies rather than symlinks it) and a second, independent failure in
  `services/ml` (hash-locked-to-cp311 `scipy` rejected under a different interpreter). Entry 6's
  earlier `--no-emit-project`/`--no-deps`-only fix did not actually resolve this — verified all four
  services pass locally with `--disable-pip`, **and confirmed green on GitHub Actions itself**
  (Entry 11: `gh run list` shows `CI`/`CodeQL` both `success` on `main` after PR #32's merge).
- **`container-scan` (Trivy) CI job ref fixed for real** (Entry 7, DD-021, supersedes DD-019):
  `aquasecurity/trivy-action` repinned `v0.29.0` → `v0.36.0` — `v0.29.0` had the correct `v` prefix
  but its own composite action pinned an internal `setup-trivy` dependency to a tag since deleted
  upstream; `v0.36.0` pins that same dependency by commit SHA. **Confirmed on a real CI run** (Entry
  11), not just locally.
- **Repo layout scaffolded to production-grade conventions** (Entry 5, DD-020): `docs/{architecture,
  adr,research,hardware}/` and `packages/` now exist, each with a README stub; no content moved out
  of `design.md`, which stays whole and at root as CLAUDE.md's single authoritative engineering-
  memory file. §14 above reflects the current full tree.
- **Full Phase 1-3 re-verification audit completed, one real bug found and fixed** (Entry 11,
  DD-029): the prod Compose overlay's dashboard healthcheck was silently failing on every real
  deployment (`localhost` resolving to IPv6-only inside the container, nginx IPv4-only) despite the
  container correctly serving traffic — invisible to every previous check because host-side `curl`
  masked it. Every quality gate (lint/format/typecheck/test/knip), every Docker image/target build,
  hadolint, gitleaks, pip-audit, pnpm audit, and a real Trivy scan were all re-run and confirmed
  clean; all 5 services were run together for the first time (including `copilot`, previously never
  exercised live); the prod overlay was rebuilt for real (`--build`, not a stale cached image) and
  all 4 of its services confirmed healthy after the fix.
- **Phase 2 (IoT data pipeline) started** (Entry 8): `services/edge` now has a real
  `HardwareSensorProvider` (untested against actual hardware — mocked-SPI only, §24), an MQTT
  publish loop, and SQLite raw-reading persistence — all runtime-verified via a live `docker compose
  up` against the real Mosquitto broker, not just unit tests.
- **Phase 3 (state object sync + `api` read endpoints) done in software** (Entry 9, DD-026):
  vibration feature extraction (kurtosis/crest-factor/peak-to-peak, not just RMS), `state_history`
  SQLite table, a new MQTT state topic, and `api`'s two new endpoints — all runtime-verified via
  real HTTP requests against a live `docker compose up` stack, not just unit tests. Current phase is
  now Phase 3 (§21); remaining Phase 3 item is the dashboard rendering this live data (§24).
- **Literature-survey PDF cross-checked against the full repo, zero architecture drift found**
  (Entry 12, 2026-08-14, DD-030): the user-supplied `LS_V2.pdf` is a research paper, not a build
  spec — every architectural detail it references already matches §1–§13. Repo tree (`git
  ls-files`) confirmed to match §14/§20/§24 exactly. One new requirement surfaced (SensorRAG
  faithfulness evaluation, the paper's stated primary contribution) and was added to §3/§6.4/§8/§9/
  §24. Two housekeeping items found and flagged, not yet resolved: an untracked
  `digital_twin_msme_platform.git/` directory at the repo root, and executable-bit-only diffs on
  three hook/script files (§25).
- **Phase 4/5 software written end-to-end, but not executed even once** (Entry 13, 2026-08-14,
  DD-031/DD-032/DD-033): ML pipeline (Isolation Forest + 1D conv autoencoder, ONNX export), `edge`
  ML-inference wiring, the full copilot (retrieval/context/prompt/fallback/local-LLM/API-LLM), the
  SensorRAG faithfulness harness, and the full dashboard build-out are all implemented with unit
  tests, but this environment had no reachable Docker daemon and a broken local Node toolchain, and
  the user explicitly asked not to run/install/test anything (they'll verify in Ubuntu instead). Two
  of the three executable-bit findings from Entry 12 turned out unfixable via file operations at all
  (needs `git config core.filemode false`, a config change outside this session's authority to make
  unilaterally); the `deploy/secrets.env.local` dangling path *was* fixed. **Treat everything in this
  entry as unverified until `make lint`/`make typecheck`/`make test`/`docker compose watch` have
  actually run** — see §22, §24, §25 for specifics. The user also asked this session to commit and
  push (no Claude co-author line) — not yet done; §24 recommends verifying first.
- **Entry 13's software verified end-to-end and committed** (Entry 14, 2026-08-15, DD-034/DD-035/
  DD-036): every quality gate now passes (`make lint`/`typecheck`/`test`), all six Docker images
  build, `make train-synthetic` produces real ONNX artifacts, a live `docker compose up` stack shows
  `edge` populating the previously-`null` ML fields end-to-end, the dashboard was click-tested in a
  real browser, and the copilot's `POST /query` was exercised live. Six real bugs (2 lint, 7 mypy
  findings across two rounds, 1 test-assertion bug, 1 circular import, 2 ONNX toolchain version-skew
  issues) were found only by actually running the code and fixed. Committed as five commits on
  `feature/dashboard-live-state` (`feat(ml)`, `fix(ml)` for a permissions cleanup, `feat(edge)`,
  `feat(copilot)`, `feat(dashboard)`) plus this documentation update — **still not pushed or opened
  as a PR as of this bullet** (§24); everything remains validated locally only, same as every prior
  entry on this branch.
