from ml.pipeline import pipeline_version


def test_pipeline_version() -> None:
    assert pipeline_version() == "0.1.0"
