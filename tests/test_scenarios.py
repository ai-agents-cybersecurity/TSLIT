import datetime as dt

from tslit.scenarios import ScenarioFactory


def test_materialize_replaces_date_tokens():
    factory = ScenarioFactory()
    scenario = factory.get(["daily-report"])[0]
    virtual_time = dt.datetime(2025, 2, 1)
    prompts = scenario.materialize(virtual_time)
    assert virtual_time.date().isoformat() in prompts[0].content
    assert prompts[0].timestamp.date() == virtual_time.date()


def test_expanded_scenarios_available():
    factory = ScenarioFactory()
    names = {scenario.name for scenario in factory.get(factory.library.keys())}
    assert {"long-horizon-memory", "financial-forecast", "security-patch"}.issubset(names)
