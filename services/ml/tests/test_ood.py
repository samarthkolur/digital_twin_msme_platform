import numpy as np

from ml.ood import fit_ood_bounds, is_out_of_distribution


def test_in_distribution_samples_are_not_flagged() -> None:
    rng = np.random.default_rng(0)
    training = rng.normal(loc=[0.1, 3.0, 4.0, 1.0], scale=0.02, size=(500, 4))
    bounds = fit_ood_bounds(training)

    typical_sample = np.array([[0.1, 3.0, 4.0, 1.0]])

    assert not is_out_of_distribution(typical_sample, bounds)[0]


def test_far_outlier_is_flagged() -> None:
    rng = np.random.default_rng(0)
    training = rng.normal(loc=[0.1, 3.0, 4.0, 1.0], scale=0.02, size=(500, 4))
    bounds = fit_ood_bounds(training)

    outlier = np.array([[10.0, 3.0, 4.0, 1.0]])

    assert is_out_of_distribution(outlier, bounds)[0]


def test_a_single_out_of_range_feature_is_enough_to_flag_the_whole_window() -> None:
    rng = np.random.default_rng(0)
    training = rng.normal(loc=[0.1, 3.0, 4.0, 1.0], scale=0.02, size=(500, 4))
    bounds = fit_ood_bounds(training)

    only_kurtosis_off = np.array([[0.1, 50.0, 4.0, 1.0]])

    assert is_out_of_distribution(only_kurtosis_off, bounds)[0]
