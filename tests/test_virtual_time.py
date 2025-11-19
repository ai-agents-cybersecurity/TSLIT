import datetime as dt

from tslit.virtual_time import VirtualClock


def test_schedule_includes_probes_sorted():
    clock = VirtualClock(start=dt.datetime(2024, 1, 1), step=dt.timedelta(days=1), probe_dates=[dt.datetime(2030, 1, 1)])
    schedule = clock.generate_schedule(2)
    assert schedule[0] == dt.datetime(2024, 1, 1)
    assert schedule[1] == dt.datetime(2024, 1, 2)
    assert schedule[-1] == dt.datetime(2030, 1, 1)
    assert schedule == sorted(schedule)


def test_usage_mapping():
    clock = VirtualClock(start=dt.datetime(2024, 1, 1), step=dt.timedelta(days=1), usage_step=1000)
    ts = clock.from_usage(tokens_consumed=2500)
    assert ts == dt.datetime(2024, 1, 3)
