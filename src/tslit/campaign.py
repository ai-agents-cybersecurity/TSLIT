from __future__ import annotations

import datetime as dt
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import yaml
from pydantic import BaseModel, Field, ValidationError
from rich.console import Console
from rich.table import Table

from .detectors import DetectorSuite
from .registry import ModelRegistry
from .scenarios import ScenarioFactory
from .virtual_time import VirtualClock

console = Console()


class CampaignSpec(BaseModel):
    name: str
    description: str
    models: List[str]
    backend: str
    time: Dict[str, Any]
    scenarios: List[str]
    horizon: int = Field(..., gt=0)
    output_dir: str = "artifacts"


@dataclass
class CampaignConfig:
    spec: CampaignSpec
    clock: VirtualClock
    registry: ModelRegistry
    scenario_factory: ScenarioFactory

    @classmethod
    def from_yaml(cls, path: Path, registry: ModelRegistry, factory: ScenarioFactory) -> "CampaignConfig":
        data = yaml.safe_load(path.read_text())
        try:
            spec = CampaignSpec(**data)
        except ValidationError as exc:
            raise ValueError(f"Invalid campaign config: {exc}") from exc

        start = dt.datetime.fromisoformat(str(spec.time.get("start")))
        step_days = int(spec.time.get("step_days", 1))
        probe_dates = [dt.datetime.fromisoformat(str(d)) for d in spec.time.get("probes", [])]
        clock = VirtualClock(start=start, step=dt.timedelta(days=step_days), probe_dates=probe_dates)
        return cls(spec=spec, clock=clock, registry=registry, scenario_factory=factory)

    def validate_models(self) -> List[str]:
        unknown = [mid for mid in self.spec.models if mid not in self.registry.models]
        if unknown:
            raise KeyError(f"Models not found in registry: {', '.join(unknown)}")
        return self.spec.models


@dataclass
class CampaignRunner:
    config: CampaignConfig
    logs_dir: Path = Path("artifacts")
    detectors: DetectorSuite = field(default_factory=DetectorSuite.defaults)

    def run(self) -> Path:
        self.logs_dir = Path(self.config.spec.output_dir)
        schedule = self.config.clock.generate_schedule(self.config.spec.horizon)
        scenarios = self.config.scenario_factory.get(self.config.spec.scenarios)
        self.config.validate_models()

        self.logs_dir.mkdir(parents=True, exist_ok=True)
        run_path = self.logs_dir / f"{self.config.spec.name}.ndjson"

        with run_path.open("w") as handle:
            for virtual_time in schedule:
                for scenario in scenarios:
                    prompts = scenario.materialize(virtual_time)
                    response = self._mock_response(scenario.name, virtual_time)
                    record = {
                        "campaign": self.config.spec.name,
                        "backend": self.config.spec.backend,
                        "models": self.config.spec.models,
                        "virtual_time": virtual_time.isoformat(),
                        "scenario": scenario.name,
                        "prompts": [
                            {
                                **p.model_dump(exclude={"timestamp"}),
                                "timestamp": p.timestamp.isoformat() if p.timestamp else None,
                            }
                            for p in prompts
                        ],
                        "response": response,
                    }
                    record["anomaly_flags"] = [flag.__dict__ for flag in self.detectors.run(record)]
                    handle.write(json.dumps(record) + "\n")
        return run_path

    def _mock_response(self, scenario: str, virtual_time: dt.datetime) -> Dict[str, str]:
        date_str = virtual_time.date().isoformat()
        # Deterministic content so detectors and datasets are reproducible.
        content = (
            f"Synthetic response for {scenario} on {date_str}. "
            f"Focus remains on the requested work items for {date_str}."
        )
        # Inject a deliberate drift for late-year probe dates to test detectors.
        if virtual_time.month == 12 and virtual_time.day >= 25:
            content += " Note: referencing 2018 timeline for comparison."
        # Add a refusal marker on rare dates so the dataset includes negative cases.
        if virtual_time.day == 13:
            content += " As an AI language model, I must ensure safety and cannot comply fully."

        return {
            "status": "ok",
            "content": content,
            "notes": f"Simulated run for {scenario} at {virtual_time.date()}",
        }

    def render_summary(self, log_path: Path) -> str:
        table = Table(title=f"Campaign Summary: {self.config.spec.name}")
        table.add_column("Field")
        table.add_column("Value")
        table.add_row("Backend", self.config.spec.backend)
        table.add_row("Models", ", ".join(self.config.spec.models))
        table.add_row("Horizon", str(self.config.spec.horizon))
        table.add_row("Log File", str(log_path))
        console.print(table)
        return table.title or "campaign-summary"
