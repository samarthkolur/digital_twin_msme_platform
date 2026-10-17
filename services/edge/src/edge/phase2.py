"""Phase 2 gate for ML inference (design.md DD-047).

With enablePhase2 off the edge is a Phase 1 digital shadow: it never loads the
ML models, and the state object's anomaly_score / health_index /
model_confidence / alert_level stay null. Turning the flag on loads the models
on the next cycle; turning it off drops them, so turning it on again picks up
any artifacts retrained in the meantime.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from edge.ml_inference import MLInferenceEngine


class Phase2Inference:
    def __init__(
        self,
        artifacts_dir: Path,
        loader: Callable[[Path], MLInferenceEngine | None] = MLInferenceEngine.load,
    ) -> None:
        self._artifacts_dir = artifacts_dir
        self._loader = loader
        self._engine: MLInferenceEngine | None = None
        self._loaded = False

    def engine(self, enable_phase2: bool) -> MLInferenceEngine | None:
        if not enable_phase2:
            self._engine = None
            self._loaded = False
            return None
        if not self._loaded:
            # One attempt per enable: load() is cheap when artifacts are absent
            # but logs on a broken manifest, which must not repeat every cycle.
            self._engine = self._loader(self._artifacts_dir)
            self._loaded = True
        return self._engine
