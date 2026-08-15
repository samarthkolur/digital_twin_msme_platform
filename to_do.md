# To-Do — Digital Cousin

Chronological action-item companion to [design.md](design.md). This file is a quick-scan checklist;
`design.md` §24 (Pending Tasks), §28 (Development Log), and §15 (Design Decisions) hold the full
rationale for every item here. Update both files together — this file should never contain
information that isn't also traceable back to a design.md section.

**History:** Entry 12 (2026-08-14) audited a user-supplied literature-survey PDF against the repo —
zero architecture drift found, one new requirement surfaced (SensorRAG faithfulness evaluation).
Entry 13 (same day) then implemented that entire roadmap: full dashboard build-out, ML training
pipeline with ONNX export (DD-031), `edge` ML-inference wiring, the full copilot, and the SensorRAG
harness, but none of it had been run, linted, type-checked, or tested. Entry 14 (2026-08-15) verified
all of it end-to-end in a working Ubuntu Docker environment — `make lint`/`typecheck`/`test`,
`docker compose build`, `make train-synthetic`, a live `docker compose up` stack, a real-browser
dashboard click-through, and a live copilot `POST /query`. Six real bugs were found (only visible by
actually running the code) and fixed: 2 ESLint errors, 7 mypy findings, 1 flaky test assertion, 1
circular import, and 2 ONNX toolchain version-skew issues (DD-034, DD-035). Section 0 below is now
closed out; committed as five commits on `feature/dashboard-live-state` (not yet pushed/opened as a
PR — see §1).

---

## 0. Verify Entry 13's work — done, Entry 14 (2026-08-15)

- [x] `make lint && make typecheck && make test` — found and fixed 2 ESLint errors (HealthGauge
      template literal, RoiEstimator void-arrow), 7 mypy errors (edge/ml `no-any-return`/
      `no-untyped-call`/`arg-type`), 5 ruff line-length/import-sort errors, and 1 flaky vitest
      assertion (RoiEstimator's "starts at zero" test was ambiguous over two `₹0.00` elements). All
      green after fixes: dashboard 33/33 tests, api 5/5, copilot 33/33, edge 17/17, ml 28/28.
- [x] `docker compose build` — all six images (`dashboard`, `api`, `copilot`, `edge`, `mosquitto`,
      `ml-trainer`) build clean.
- [x] `make train-synthetic` — produced real `services/ml/artifacts/{isolation_forest.onnx,
    autoencoder.onnx(+.onnx.data), health_index_calibration.json, manifest.json}`. Needed two
      fixes first (design.md DD-034): skl2onnx's `target_opset` pinned explicitly (its own default
      emitted an opset it also claims not to support), and `onnxscript` added as a dependency
      (torch's now-default dynamo ONNX exporter requires it).
- [x] `docker compose up` — confirmed `edge` loads the artifacts and `/state/current` populates
      `anomaly_score`/`health_index`/`model_confidence`/`alert_level` (previously always `null`).
      Also found and fixed a real circular import (`edge.features` ↔ `edge.providers`, design.md
      DD-035) that broke `pytest` collection entirely before this could even be tested.
- [x] Dashboard click-through in a real browser — health gauge, both trend charts, alerts panel,
      historical log with the alert-level filter, and the ROI estimator (`1000×100` cost/hours,
      30% reduction → `₹100000.00`/`₹30000.00`, hand-verified) all confirmed working live.
- [x] DD-032 re-check — inspected the real exported ONNX model's output names directly
      (`["label", "scores"]`); the `"score"` substring hint correctly matches `"scores"`. Confirmed
      correct, not just plausible.
- [x] `POST /query` on the copilot — live call returned `{"used_fallback": true, "context_size":
    10}`: retrieval correctly pulled 10 recent state objects from `api`, and fallback correctly
      triggered since no LLM weights/API key are configured yet (§4 below covers that).
- [x] Committed (Conventional Commits, no Claude co-author, matching `git log` style) as
      `feat(ml)`, `fix(ml)` (file-permission cleanup), `feat(edge)`, `feat(copilot)`,
      `feat(dashboard)` — see design.md §28 Entry 14 for full detail. **Not yet pushed** — see §1.

## 1. Housekeeping

- [ ] **Push `feature/dashboard-live-state` and open its PR** (or merge it) so CI actually runs
      against it — per design.md §29, this branch (including Entry 13/14's new commits) has only
      ever been validated locally, never on GitHub Actions.
- [ ] **Resolve the untracked `digital_twin_msme_platform.git/` directory** at the project root. It's
      a bare git repo (`HEAD`/`objects`/`refs`/`packed-refs`), untracked, purpose unclear — looks like
      a stray clone or backup. Still not touched, pending user confirmation. (design.md §24, §25)
- [x] **Executable-bit diffs on `.husky/commit-msg`, `.husky/pre-commit`, `scripts/bootstrap.sh`**:
      confirmed in Entry 14 that these do **not** reproduce on Ubuntu (clean `git diff --summary` on
      all three) — the Windows/NTFS-specific issue from Entry 12 is closed, no `core.filemode`
      change needed. A _different_ exec-bit issue was found instead: the `toolbox` container (and
      Husky's pre-commit hook, which shells into it) runs as root by default, which can leave newly
      created tracked files `+x` and root-owned on the host (design.md DD-036) — worked around
      per-occurrence this session with a throwaway `chown`; the real fix (run the container as the
      host UID/GID) is tracked as Technical Debt (design.md §26), not yet applied.

## 2. Phase 2 close-out — hardware procurement & validation (blocking real-hardware work)

- [x] Procure Raspberry Pi 4 — done.
- [ ] Procure remaining sensor hardware: ADXL345 (or MPU6050) + DS18B20 (design.md §6.2 BOM).
- [ ] Identify and gain access to the pilot machine (real MSME asset, or a lab motor/compressor as a
      controlled-prototype substitute per design.md §11 risk mitigation).
- [ ] Validate `HardwareSensorProvider` (`services/edge/src/edge/providers/hardware.py`) against real
      ADXL345/DS18B20 hardware and a reference sensor — the register decode (DD-022) is implemented and
      unit-tested against a mocked SPI bus only, never real silicon.
- [ ] Verify `docker-compose.prod.yml` actually builds/runs on the real Pi 4 (Cortex-A72) — so far only
      exercised via `docker-build` CI, never on physical hardware.
- [ ] Tune the vibration sampling loop's real-time behavior (buffering, jitter, sample count/rate) once
      real hardware is available — DD-022 deliberately scoped Phase 2 to a correct-but-modest 64-sample
      burst rather than a continuous 3,200 Hz stream; this needs empirical tuning against real silicon.
      (This also gates ever moving `services/ml`'s window length past 64 samples, DD-031.)

## 3. Phase 4 — ML pipeline (`services/ml`) — code written (Entry 13) and verified (Entry 14); next:

- [ ] Download and preprocess the CWRU and IMS Bearing datasets into `services/ml/data/` —
      `ml.datasets` already raises a clear error pointing here until this is done; `ml.pipeline`'s
      real-data code path is an explicit `NotImplementedError` pending it.
- [ ] Once real data exists: re-run the pipeline against it instead of `--allow-synthetic`, and check
      the reported F1 scores against design.md §9's real targets (Isolation Forest ≥0.80, autoencoder
      ≥0.85) — the synthetic-data numbers (0.787 / 0.995) confirmed the pipeline runs end-to-end but
      are not that metric.
- [ ] Re-calibrate `health_index` (`ml.health_index`) against the pilot machine's real 30-minute
      baseline recording once hardware/pilot machine access exists (design.md §6.3), not synthetic data.

## 4. Phase 5 — copilot (`services/copilot`) — code written (Entry 13), retrieval/fallback path verified live (Entry 14); next:

- [ ] Download TinyLlama-1.1B Q4_K_M GGUF weights (design.md §7) to `LOCAL_LLM_MODEL_PATH` and confirm
      `COPILOT_LLM_MODE=local` actually generates a response via `llama-cpp-python` (`local-llm` extra
      — `uv sync --extra local-llm`, which compiles native code, so expect a slower first build).
- [ ] Or: put an `ANTHROPIC_API_KEY`/`OPENAI_API_KEY` in `$SECRETS_FILE` (DD-010) and confirm
      `COPILOT_LLM_MODE=api` works against a live API call.
- [ ] Run the SensorRAG evaluation (`python -m copilot.sensorrag.runner`, or `run_sensorrag_evaluation`
      programmatically) against whichever real LLM path is set up, and record the actual fallback
      accuracy / hallucination rate — the numbers the harness reports today are only against fake/
      injected LLM clients in tests, not a real faithfulness measurement.
- [ ] Revisit DD-033's grounding-check limitation (presence-based, not full semantic attribution) once
      real SensorRAG runs are happening — decide whether it's good enough or needs claim-level linking.

## 5. Phase 6 — testing & submission

- [ ] Copilot factual-accuracy test: 50 structured queries with ground-truth state (target ≥90%,
      design.md §9) — run alongside the SensorRAG protocol above, not as a separate effort.
- [ ] Retrofit protocol documentation: BOM, wiring diagram, calibration procedure, generalizable
      installation checklist (design.md §6, §11).
- [ ] Retrofit protocol reproducibility check: second installation by a different team member
      (design.md §9).
- [ ] Full written report + viva demo preparation.

## 6. Deferred / not yet scheduled

- [ ] Add a multi-arch (`linux/arm64`) image-publish workflow (GHCR) once ready to deploy to the real
      Pi (design.md §26, §27).
- [ ] Add mosquitto auth (username/password or client certs) before any non-localhost exposure
      (design.md §16 DD-016, §26).
- [ ] Consider Turborepo once a second TypeScript package exists (design.md §15 DD-013).
- [ ] Consider InfluxDB OSS if SQLite query complexity grows (design.md §27).
- [ ] Add an end-to-end test harness (e.g. Playwright) now that the dashboard has real UI (design.md §27).
- [ ] Give `api`'s `GET /state/history` pagination or a time-range parameter so the dashboard's
      historical log can actually reach the originally-scoped 24h window instead of the current
      1000-row cap (~83 minutes at the default publish interval) — design.md §26.
- [ ] Run the `toolbox`/compose containers as the host UID/GID (design.md §26, DD-036) so hook-
      triggered git/file operations stop leaving root-owned files behind.

---

_Out of scope for this project (design.md §4) — do not add to this list: high-frequency (>5 kHz)
bearing fault analysis, current-clamp/electrical monitoring, full-factory/multi-machine simulation,
closed-loop autonomous actuation, custom PCB fabrication, multi-tenant SaaS, LLM fine-tuning._
