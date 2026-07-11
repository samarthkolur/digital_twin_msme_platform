from statistics import fmean

from edge.providers.base import VibrationFeatures


def compute_vibration_features(magnitudes_g: list[float], sampling_hz: int) -> VibrationFeatures:
    """Computes RMS/kurtosis/crest-factor/peak-to-peak (design.md §6.0) from a
    raw vibration-magnitude window.

    The window mean — dominated by the ~1g static gravity offset at the
    sensor's mount orientation — is subtracted first, so all four features
    describe the dynamic (AC-coupled) vibration signal rather than the
    static offset. `kurtosis` is Pearson's definition (normal/baseline
    vibration ~= 3.0), matching the §6.0 example value.
    """
    mean_g = fmean(magnitudes_g)
    ac = [m - mean_g for m in magnitudes_g]

    variance = fmean(v**2 for v in ac)
    rms_g = variance**0.5
    kurtosis = fmean(v**4 for v in ac) / variance**2 if variance > 0 else 0.0
    peak_to_peak_g = max(ac) - min(ac)
    crest_factor = max(abs(v) for v in ac) / rms_g if rms_g > 0 else 0.0

    return VibrationFeatures(
        rms_g=round(rms_g, 4),
        kurtosis=round(kurtosis, 3),
        crest_factor=round(crest_factor, 3),
        peak_to_peak_g=round(peak_to_peak_g, 4),
        sampling_hz=sampling_hz,
    )
