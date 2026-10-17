#!/usr/bin/env python3
"""Generate the paper's result figures from the real CWRU/IMS data and the
exported ONNX artefacts.

Run from anywhere:
    uv run --with matplotlib --with seaborn --with onnxruntime \
        python services/ml/scripts/make_paper_figures.py

Outputs (docs/research/figures/):
    fig_rul_calibration.{pdf,png}            predicted vs true life fraction + residuals
    fig_cwru_feature_separability.{pdf,png}  per-feature class distributions
    figure_data_summary.json                 the numbers each figure reports
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import onnxruntime as ort
import seaborn as sns
from sklearn.metrics import mean_absolute_error, r2_score

ML = Path(__file__).resolve().parent.parent
REPO = ML.parent.parent
OUT = REPO / "docs/research/figures"
sys.path.insert(0, str(ML / "src"))

from ml.cwru_loader import load_cwru_windows  # noqa: E402
from ml.features import compute_window_features, features_to_array  # noqa: E402
from ml.ims_loader import load_ims_rul_windows  # noqa: E402

MANIFEST = json.loads((ML / "artifacts/manifest.json").read_text())
WINDOW_LENGTH = MANIFEST["window_length"]

# IEEE two-column: a single column is 3.5 in, full width 7.16 in.
COLUMN_IN, FULL_IN = 3.5, 7.16

sns.set_theme(style="ticks", context="paper", font_scale=0.95)
sns.set_palette("colorblind")
plt.rcParams.update(
    {
        "font.family": "serif",
        "font.serif": ["DejaVu Serif"],
        "mathtext.fontset": "dejavuserif",
        "axes.grid": True,
        "grid.alpha": 0.3,
        "grid.linewidth": 0.5,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "figure.autolayout": False,
    }
)
C_NORMAL, C_FAULTY = sns.color_palette("colorblind")[0], sns.color_palette("colorblind")[3]


def window_features(windows: np.ndarray) -> np.ndarray:
    return features_to_array([compute_window_features(w) for w in windows])


def save(fig: plt.Figure, stem: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for ext in ("pdf", "png"):
        fig.savefig(OUT / f"{stem}.{ext}")
    plt.close(fig)
    print(f"  wrote {stem}.pdf / .png")


def figure_rul_calibration() -> dict[str, Any]:
    """Predicted vs true life fraction on the held-out IMS split, plus residuals."""
    print("[1/2] IMS run-to-failure, held-out split by file ...")
    _, _, windows, truth = load_ims_rul_windows(ML / "data/ims", WINDOW_LENGTH)
    features = window_features(windows).astype(np.float32)

    session = ort.InferenceSession(str(ML / "artifacts/rul.onnx"))
    raw = session.run(None, {session.get_inputs()[0].name: features})[0].ravel()
    # The exported Ridge graph carries no clamp, but both consumers of it apply
    # one (ml.rul.predict_rul and edge.ml_inference), because the state object
    # defines this field as a fraction in [0, 1]. Scoring the raw graph would not
    # describe deployed behaviour: R2 = -0.086 raw against 0.187 clipped, since a
    # linear model extrapolates on out-of-distribution inputs.
    pred = np.clip(raw, 0.0, 1.0)
    outside = int(((raw < 0.0) | (raw > 1.0)).sum())

    mae = float(mean_absolute_error(truth, pred))
    r2 = float(r2_score(truth, pred))
    print(f"      {len(truth)} windows | MAE={mae:.4f} R2={r2:.4f}")

    fig, (ax, axr) = plt.subplots(
        2,
        1,
        figsize=(COLUMN_IN, 3.9),
        sharex=True,
        gridspec_kw={"height_ratios": [2.4, 1], "hspace": 0.12},
    )

    ax.scatter(
        truth,
        pred,
        s=11,
        color=C_NORMAL,
        alpha=0.4,
        edgecolor="none",
        label="held-out window",
        rasterized=True,
    )
    # The split is by file, so each distinct target is one snapshot: summarise it.
    levels = np.unique(truth)
    med = np.array([np.median(pred[truth == t]) for t in levels])
    ax.plot(
        levels,
        med,
        "o-",
        color="black",
        markersize=3.2,
        linewidth=1.0,
        markerfacecolor="white",
        markeredgewidth=0.8,
        label="per-snapshot median",
    )
    ax.plot([0, 1], [0, 1], ls="--", color="0.4", lw=1.0, label="ideal")
    ax.set_ylabel("Predicted life fraction")
    ax.set_ylim(-0.03, 1.03)
    ax.legend(loc="upper left", frameon=True, framealpha=0.9, fontsize=7)
    ax.set_title(f"MAE = {mae:.3f},  $R^2$ = {r2:.3f},  n = {len(truth)}", fontsize=8)

    axr.axhline(0.0, ls="--", color="0.4", lw=1.0)
    axr.scatter(
        truth, pred - truth, s=11, color=C_FAULTY, alpha=0.4, edgecolor="none", rasterized=True
    )
    axr.set_xlabel("True life fraction remaining")
    axr.set_ylabel("Residual")
    axr.set_xlim(-0.03, 1.03)

    sns.despine(fig=fig)
    save(fig, "fig_rul_calibration")
    return {
        "mae": mae,
        "r2": r2,
        "n_windows": int(len(truth)),
        "n_snapshots": int(len(levels)),
        "raw_outside_unit_interval": outside,
        "raw_min": float(raw.min()),
        "raw_max": float(raw.max()),
    }


def figure_feature_separability() -> dict[str, Any]:
    """Per-feature distributions for normal vs faulty CWRU windows."""
    print("[2/2] CWRU windows ...")
    windows, labels = load_cwru_windows(ML / "data/cwru", WINDOW_LENGTH)
    features = window_features(windows)
    n_normal, n_faulty = int((labels == 0).sum()), int((labels == 1).sum())
    print(f"      {len(labels)} windows | normal={n_normal} faulty={n_faulty}")

    axis_labels = ["RMS (g)", "Kurtosis", "Crest factor", "Peak-to-peak (g)"]
    # RMS and peak-to-peak are amplitudes spanning orders of magnitude; the two
    # dimensionless shape statistics do not and stay linear.
    log_axes = {0, 3}
    lower, upper = MANIFEST["ood_bounds"]["lower"], MANIFEST["ood_bounds"]["upper"]

    fig, axes = plt.subplots(1, 4, figsize=(FULL_IN, 2.0))
    for i, ax in enumerate(axes):
        normal, faulty = features[labels == 0, i], features[labels == 1, i]
        lo = float(np.percentile(features[:, i], 0.5))
        hi = float(np.percentile(features[:, i], 99.5))
        if i in log_axes:
            lo = max(lo, float(features[features[:, i] > 0, i].min()))
            bins = np.logspace(np.log10(lo), np.log10(hi), 50)
            ax.set_xscale("log")
        else:
            bins = np.linspace(lo, hi, 50)

        ax.axvspan(
            lower[i],
            upper[i],
            color="0.85",
            zorder=0,
            label="in-distribution band" if i == 0 else None,
        )
        ax.hist(
            normal,
            bins=bins,
            density=True,
            histtype="stepfilled",
            color=C_NORMAL,
            alpha=0.55,
            label="normal" if i == 0 else None,
        )
        ax.hist(
            faulty,
            bins=bins,
            density=True,
            histtype="stepfilled",
            color=C_FAULTY,
            alpha=0.55,
            label="faulty" if i == 0 else None,
        )
        ax.hist(normal, bins=bins, density=True, histtype="step", color=C_NORMAL, lw=0.9)
        ax.hist(faulty, bins=bins, density=True, histtype="step", color=C_FAULTY, lw=0.9)

        ax.set_xlabel(axis_labels[i])
        ax.set_xlim(lo, hi)
        ax.set_yticks([])
        if i == 0:
            ax.set_ylabel("Density")

    handles, legend_labels = axes[0].get_legend_handles_labels()
    fig.legend(
        handles,
        legend_labels,
        loc="upper center",
        ncol=3,
        frameon=False,
        bbox_to_anchor=(0.5, 1.09),
        fontsize=8,
    )
    sns.despine(fig=fig, left=True)
    fig.subplots_adjust(wspace=0.18)
    save(fig, "fig_cwru_feature_separability")
    return {"n_windows": int(len(labels)), "n_normal": n_normal, "n_faulty": n_faulty}


def main() -> None:
    summary = {
        "rul_calibration": figure_rul_calibration(),
        "cwru_feature_separability": figure_feature_separability(),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "figure_data_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print("\n" + json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
