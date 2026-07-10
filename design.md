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
