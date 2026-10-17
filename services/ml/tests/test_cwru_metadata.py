from ml.cwru_metadata import CWRU_FILE_INFO, CWRU_FILES


def test_catalog_covers_normal_baseline_and_12k_drive_end_fault_data() -> None:
    # 4 normal-baseline loads + 60 12kHz Drive-End fault files (design.md §24).
    assert len(CWRU_FILES) == 64
    assert len(CWRU_FILE_INFO) == 64


def test_normal_label_decodes_with_no_fault_diameter() -> None:
    info = CWRU_FILE_INFO["Normal_2"]
    assert info.fault_type == "normal"
    assert info.load_hp == 2
    assert info.fault_diameter_in is None
    assert info.outer_race_position is None


def test_inner_race_label_decodes_diameter_and_load() -> None:
    info = CWRU_FILE_INFO["IR007_3"]
    assert info.fault_type == "inner_race"
    assert info.fault_diameter_in == 0.007
    assert info.load_hp == 3
    assert info.outer_race_position is None


def test_ball_label_decodes_without_position() -> None:
    info = CWRU_FILE_INFO["B028_0"]
    assert info.fault_type == "ball"
    assert info.fault_diameter_in == 0.028
    assert info.outer_race_position is None


def test_outer_race_label_decodes_clock_position() -> None:
    info = CWRU_FILE_INFO["OR014@6_1"]
    assert info.fault_type == "outer_race"
    assert info.fault_diameter_in == 0.014
    assert info.outer_race_position == 6
    assert info.load_hp == 1


def test_every_url_is_an_https_case_edu_link() -> None:
    assert all(url.startswith("https://engineering.case.edu/") for url in CWRU_FILES.values())
