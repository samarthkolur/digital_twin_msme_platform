from edge.storage import RawReadingStore


def test_insert_and_count() -> None:
    store = RawReadingStore(":memory:")
    try:
        assert store.count() == 0

        store.insert("motor_01", vibration_rms_g=0.12, temperature_c=45.5)
        store.insert("motor_01", vibration_rms_g=0.34, temperature_c=46.1)

        assert store.count() == 2
    finally:
        store.close()


def test_insert_persists_expected_columns() -> None:
    store = RawReadingStore(":memory:")
    try:
        store.insert("motor_01", vibration_rms_g=0.12, temperature_c=45.5)

        row = store._conn.execute(
            "SELECT asset_id, vibration_rms_g, temperature_c FROM raw_readings"
        ).fetchone()

        assert row == ("motor_01", 0.12, 45.5)
    finally:
        store.close()
