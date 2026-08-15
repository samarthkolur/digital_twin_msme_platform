"""Out-of-distribution confidence flagging (design.md §6.3 step 4).

Per-feature bounds from the training distribution's 0.5th/99.5th percentiles
(a symmetric two-tailed 99% band) rather than a single upper percentile, so a
feature that's anomalously *low* is flagged just as reliably as one that's
anomalously high — design.md's "99th percentile" language is the intent
(flag inputs outside the well-characterized training range); a strictly
one-sided upper bound would miss that for features where "too low" is also
abnormal (e.g. an implausibly small RMS suggesting a disconnected sensor).
"""

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True, slots=True)
class OODBounds:
    lower: NDArray[np.float64]
    upper: NDArray[np.float64]


def fit_ood_bounds(training_features: NDArray[np.float64]) -> OODBounds:
    lower = np.percentile(training_features, 0.5, axis=0)
    upper = np.percentile(training_features, 99.5, axis=0)
    return OODBounds(lower=lower, upper=upper)


def is_out_of_distribution(features: NDArray[np.float64], bounds: OODBounds) -> NDArray[np.bool_]:
    """features: (n_windows, n_features). Returns one bool per window — True
    if *any* feature falls outside its training-distribution bounds, per
    design.md §6.3's "flags the prediction as low-confidence rather than
    suppressing it" (a single out-of-range feature is enough to distrust the
    whole prediction).
    """
    below = features < bounds.lower
    above = features > bounds.upper
    result: NDArray[np.bool_] = np.any(below | above, axis=1)
    return result
