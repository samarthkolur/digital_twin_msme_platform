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

**Model pipeline:**
1. *Isolation Forest* (Phase 4, M4–M5): trained on extracted statistical features (RMS, kurtosis, crest factor, peak-to-peak). Contamination parameter tuned on CWRU normal-class windows. Serves as the operational baseline from M5 onward. Model size: <1 MB.
2. *1D Convolutional Autoencoder* (Phase 4, M5–M6): trained on raw vibration windows (3,200 Hz, 1-second frames) from CWRU and IMS. Reconstruction error thresholded against pilot machine baseline. Converted to TFLite; target model size: <5 MB; target inference latency: <100 ms on Pi 4.
3. *Health index*: a normalized scalar (0.0–1.0) computed from reconstruction error and Isolation Forest anomaly score using a weighted linear combination, calibrated so that 1.0 = normal baseline and <0.6 = alert threshold.
4. *Out-of-distribution (OOD) flag*: if input features fall outside the 99th percentile of the training distribution, the system flags the prediction as low-confidence rather than suppressing it, ensuring operators are notified of uncertain readings rather than receiving a false-normal.

### 6.4 Copilot Module

The copilot is a retrieval-augmented generation (RAG) system with a constrained context window:

- **Retrieval**: the last 10 state objects (covering ~10 seconds of data or ~10 historical readings, depending on query type) are serialized and injected into the prompt as structured context.
- **LLM**: TinyLlama-1.1B (Q4_K_M quantization, ~700 MB RAM) served via llama.cpp on the Pi 4. Expected throughput: 1–3 tokens/second on ARM Cortex-A72, yielding 5–15 second response latency for typical 50–100 token responses. This latency is acceptable for non-real-time diagnostic queries.
- **API fallback**: when internet connectivity is available, an API-based LLM (configurable) can substitute the local model, reducing latency to under 2 seconds.
- **System prompt constraint**: the system prompt explicitly prohibits the model from answering questions not grounded in the retrieved sensor context. If the context is empty, stale (>5 minutes old), or flagged OOD, a rule-based fallback response is returned instead of an LLM-generated answer.
- **Scope**: the copilot answers operational questions only — machine health status, anomaly explanations, recent alerts. It does not provide maintenance instructions, safety guidance, or any information outside sensor context.

**Example interaction:**
- User: "Is the motor okay right now?"
- Retrieved context: health_index=0.71, kurtosis=4.8 (elevated), temperature=61°C (within normal)
- Response: "The motor's health index is 0.71, which is slightly below the normal range. Vibration kurtosis is elevated, which can indicate early-stage mechanical looseness or bearing wear. Temperature is within normal range. Consider scheduling an inspection."

### 6.5 Application / Dashboard Module

- Offline-first web application (React + Vite), served from the Pi 4 via a local HTTP server. No internet connection required for any core function.
- Real-time state display: health index gauge, vibration RMS trend (rolling 1-hour window), temperature trend, active alerts.
- Historical log: last 24 hours of state objects, filterable by alert level.
- Alert module: configurable thresholds (health index, temperature); alerts delivered via local dashboard notification and an optional GPIO-connected buzzer for shop-floor audibility.
- ROI estimator: operator inputs average cost per hour of unplanned downtime and average planned maintenance cost; the module outputs projected annual savings assuming a configurable reduction in unplanned downtime events.

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
| ML framework | Inference | TensorFlow Lite (TFLite) | Optimized for ARM; supports both Isolation Forest (via Python sklearn, <1 MB) and autoencoder (TFLite, <5 MB) |
| ML training | Development | scikit-learn + PyTorch (training only, on development PC) | Models exported to TFLite/ONNX for deployment |
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
│       ├── Dockerfile      multi-stage: base → deps → dev / build → prod (nginx)
│       └── nginx.conf
├── services/
│   ├── edge/               Sensor acquisition + feature extraction (FastAPI)
│   │   └── src/edge/providers/   base.py (interface), simulated.py, hardware.py
│   ├── api/                REST API over the digital-twin state object (FastAPI)
│   ├── copilot/             Retrieval-grounded NL copilot (FastAPI)
│   └── ml/                  Offline training pipeline (Isolation Forest, 1D conv autoencoder)
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
├── Makefile                  `make lint|format|typecheck|test|train|shell-tools|bootstrap|watch`
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

---

## 16. Dependencies

**Root (TypeScript tooling, devDependencies only — no runtime deps at the root):**
`typescript`, `eslint` + `@eslint/js` + `typescript-eslint` + `eslint-plugin-{react,react-hooks,jsx-a11y,import-x,promise}` + `eslint-config-prettier`, `prettier`, `husky`, `lint-staged`, `@commitlint/{cli,config-conventional}`, `knip`.

**`apps/dashboard`:** `react`, `react-dom` (runtime); `vite`, `@vitejs/plugin-react`, `vitest`, `@vitest/coverage-v8`, `@testing-library/{react,jest-dom}`, `jsdom` (dev).

**`services/edge`:** `fastapi`, `uvicorn[standard]`, `pydantic`, `paho-mqtt` (runtime); optional extra `hardware` = `spidev`, `RPi.GPIO`, `w1thermsensor` (Pi-only, not installed by default sync).

**`services/api`:** `fastapi`, `uvicorn[standard]`, `pydantic`.

**`services/copilot`:** `fastapi`, `uvicorn[standard]`, `pydantic`, `httpx` (runtime, for the API-fallback path); optional extra `local-llm` = `llama-cpp-python` (compiles native code — kept optional so CI/dev-container installs stay fast).

**`services/ml`:** `scikit-learn`, `torch` (CPU wheels, DD-011), `numpy`, `pandas`.

**Every Python service** additionally declares a `dev` dependency group: `pytest`, `pytest-cov`, `mypy`, (+`httpx` for FastAPI services, needed by `TestClient`).

No dependency has been added without a corresponding line item above and, where non-obvious, a DD in §15.

---

## 17. Environment Variables

| Variable | Where | Default | Purpose |
|---|---|---|---|
| `SENSOR_PROVIDER` | `edge` | `simulated` (dev) / `hardware` (prod, via `docker-compose.prod.yml`) | Selects the `SensorProvider` implementation (DD-003) |
| `MQTT_HOST` / `MQTT_PORT` | `edge` | `mosquitto` / `1883` | MQTT broker address on the Docker network |
| `DATABASE_PATH` | `edge`, `api` | `/data/digital_cousin.sqlite3` | SQLite file inside the shared `sqlite-data` named volume |
| `COPILOT_LLM_MODE` | `copilot` | `local` | `local` = TinyLlama/llama.cpp (no secrets); `api` = Anthropic/OpenAI fallback |
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
  it, `dashboard` and `copilot` consume it via `api`. Not yet implemented beyond the schema
  definition in §6.0 — Phase 3 work.
- **`SensorProvider` abstraction** (DD-003, `services/edge/src/edge/providers/`): `base.py` defines
  the interface (`read() -> SensorSample`), `simulated.py` generates plausible dev data,
  `hardware.py` lazily imports `spidev`/`w1thermsensor` and currently raises `NotImplementedError`
  on `read()` pending Phase 2 register-decoding work — the provider-selection plumbing is done, the
  ADXL345 wire protocol is not.
- **Copilot retrieval/prompt-construction logic** (§6.4): not yet implemented — `services/copilot`
  currently only exposes `/health`.
- **ML training pipeline** (§6.3): `services/ml` has the package/dependency/CI skeleton only;
  Isolation Forest and autoencoder implementations are Phase 4 work.

---

## 21. Current Phase

**Phase 1: Research & setup (M1–M2)** — per the delivery plan (§10). This engineering-foundation
build is the "development environment configured" deliverable of Phase 1.

## 22. Current Milestone

Development environment configured (Phase 1 deliverable). Outstanding within this milestone:
hardware procurement and pilot machine identification (tracked in §24 Pending Tasks) are the only
Phase 1 items not addressed by this engineering-foundation work.

## 23. Completed Milestones

- **Engineering foundation established** (this work, logical time 2026-07-11): Docker-first dev
  environment (`docker compose watch`), polyglot pnpm+uv monorepo, strict TS + ESLint flat config +
  Prettier, ruff + mypy strict per Python service, Husky/lint-staged/commitlint, GitHub Actions CI
  (lint/typecheck/test/build/security matrixed across 4 Python services + dashboard), CodeQL,
  Dependabot, `scripts/bootstrap.sh` onboarding, VS Code workspace config, and skeleton services
  (`edge`, `api`, `copilot`, `ml`, `dashboard`) each with a working health check and passing tests.

## 24. Pending Tasks

- [ ] Procure hardware: ADXL345/MPU6050, DS18B20, Raspberry Pi 4 (§6.2 BOM)
- [ ] Identify and gain access to the pilot machine (real MSME asset or lab equivalent, §11 risk)
- [ ] Implement ADXL345 SPI register decoding in `HardwareSensorProvider.read()` (Phase 2)
- [ ] Implement the state object sync loop (edge → SQLite) and the `api` read endpoints (Phase 3)
- [ ] Download/preprocess CWRU + IMS datasets into `services/ml` (Phase 4)
- [ ] Implement Isolation Forest + 1D conv autoencoder training in `services/ml/src/ml/pipeline.py` (Phase 4)
- [ ] Implement copilot retrieval + prompt construction + rule-based fallback (Phase 5)
- [ ] Build out the real dashboard (health gauge, trends, alerts, ROI estimator) (Phase 3/5)
- [ ] Add a multi-arch (`linux/arm64`) image publish workflow once ready to deploy to a real Pi (§26)
- [ ] Generate and commit `pnpm-lock.yaml` and each service's `uv.lock` (first `bootstrap.sh` / `uv sync` run)

## 25. Known Issues

- Mosquitto broker has `allow_anonymous true` and no TLS (DD-016) — acceptable only while the
  broker is unreachable outside the Docker network / Pi-local network.
- `HardwareSensorProvider.read()` raises `NotImplementedError` — the hardware path is not yet
  functional (by design, this phase is tooling-only; see §24).
- No `uv.lock` / `pnpm-lock.yaml` committed as of this entry — generated and committed as part of
  validating this foundation (see §28 Development Log for the exact commands run).

## 26. Technical Debt

- Mosquitto authentication/TLS deferred until the broker is ever exposed beyond localhost/LAN.
- No CI image-publishing workflow yet (builds are verify-only); needed before real Pi deployment.
- `docker-compose.prod.yml` device passthrough (`/dev/spidev0.0`, `/dev/gpiomem`) is hard-coded to
  the default SPI bus/device — revisit if the retrofit protocol (§11) ends up needing configurable
  bus addressing across different pilot machines.
- Coverage thresholds (60% dashboard, 70% Python services) are placeholders sized for the current
  skeleton; raise as real feature code lands.

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

---

## 29. Current Repository State

- **Branch:** `main`, tracking `origin/main`.
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
- **No application features implemented** — every service exposes a working `/health` endpoint and
  passing tests, but the state object sync, sensor register decoding, ML training, and copilot
  retrieval logic are all still Pending Tasks (§24), by design (this was a foundation-only task).
- **Engineering foundation is runtime-verified, not just statically reviewed** (Entry 2): `docker
  compose watch` hot reload, health-gated startup ordering, the prod Compose overlay, and the Husky
  → toolbox → lint-staged/commitlint hook chain were all exercised live, and two real bugs surfaced
  only by doing so (see Entry 2) — both fixed before this entry.
