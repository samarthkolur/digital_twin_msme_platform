import numpy as np

from ml.evaluate import evaluate_f1, scores_to_binary_predictions


def test_scores_to_binary_predictions_thresholds_correctly() -> None:
    scores = np.array([0.1, 0.5, 0.9, 1.5])

    predictions = scores_to_binary_predictions(scores, threshold=0.5)

    assert list(predictions) == [0, 0, 1, 1]


def test_evaluate_f1_perfect_predictions() -> None:
    y_true = np.array([0, 0, 1, 1])
    y_pred = np.array([0, 0, 1, 1])

    assert evaluate_f1(y_true, y_pred) == 1.0


def test_evaluate_f1_no_true_positives_is_zero_not_an_error() -> None:
    y_true = np.array([1, 1, 1])
    y_pred = np.array([0, 0, 0])

    assert evaluate_f1(y_true, y_pred) == 0.0
