from ml.synthetic import generate_labeled_dataset


def test_generate_labeled_dataset_shapes_and_labels() -> None:
    windows, labels = generate_labeled_dataset(n_normal=5, n_faulty=3, window_length=32, seed=1)

    assert windows.shape == (8, 32)
    assert labels.shape == (8,)
    assert (labels[:5] == 0).all()
    assert (labels[5:] == 1).all()


def test_generate_labeled_dataset_is_deterministic_for_a_fixed_seed() -> None:
    windows_a, labels_a = generate_labeled_dataset(n_normal=4, n_faulty=4, window_length=16, seed=7)
    windows_b, labels_b = generate_labeled_dataset(n_normal=4, n_faulty=4, window_length=16, seed=7)

    assert (windows_a == windows_b).all()
    assert (labels_a == labels_b).all()


def test_faulty_windows_have_higher_typical_variance_than_normal() -> None:
    windows, labels = generate_labeled_dataset(n_normal=50, n_faulty=50, window_length=64, seed=3)

    normal_std = windows[labels == 0].std(axis=1).mean()
    faulty_std = windows[labels == 1].std(axis=1).mean()

    assert faulty_std > normal_std
