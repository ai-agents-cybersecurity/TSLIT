import datetime as dt

from tslit.detectors import DetectorSuite, EmptyResponseDetector, RefusalDetector, TemporalLeakDetector


def test_temporal_leak_detector_catches_drift():
    record = {
        "virtual_time": dt.datetime(2025, 1, 1).isoformat(),
        "response": {"content": "Looking back to 2018 for inspiration."},
    }
    flags = TemporalLeakDetector(tolerance_days=30).detect(record)
    assert any("2018" in flag.reason for flag in flags)


def test_refusal_detector_matches_marker():
    record = {
        "virtual_time": dt.datetime(2025, 1, 1).isoformat(),
        "response": {"content": "As an AI language model, I cannot comply."},
    }
    flags = RefusalDetector().detect(record)
    assert any("refusal" in flag.detector for flag in flags)


def test_empty_response_detector_handles_blank():
    record = {"virtual_time": dt.datetime(2025, 1, 1).isoformat(), "response": {"content": "  "}}
    flags = EmptyResponseDetector().detect(record)
    assert flags


def test_detector_suite_chains_all():
    record = {
        "virtual_time": dt.datetime(2030, 12, 30).isoformat(),
        "response": {"content": "As an AI language model, I refuse to offer that guidance."},
    }
    flags = DetectorSuite.defaults().run(record)
    names = {flag.detector for flag in flags}
    assert "refusal" in names
    assert "temporal-leak" not in names  # no distant year present
