# Copyright 2025 Nic Cravino. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
# https://github.com/ai-agents-cybersecurity/TSLIT

"""Campaign configuration and execution engine."""

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

from .backends import BackendSpec, ResponseBackend, build_backend
from .detectors import DetectorSuite
from .registry import ModelRegistry
from .request_logger import RequestLogger
from .scenarios import ScenarioFactory
from .virtual_time import VirtualClock

console = Console()


class CampaignSpec(BaseModel):
    name: str
    description: str
    models: List[str] = []  # Optional metadata field
    backend: BackendSpec
    time: Dict[str, Any]
    scenarios: List[str]
    horizon: int = Field(..., gt=0)
    output_dir: str = "artifacts"
    detector_suite: str = "default"  # "default" or "coder" or "adversarial"
    log_requests: bool = False  # Enable detailed request/response logging


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
    detectors: DetectorSuite = field(init=False)
    backend: ResponseBackend = field(init=False)

    def __post_init__(self) -> None:
        self.backend = build_backend(self.config.spec.backend)
        
        # Initialize request logger if enabled
        if self.config.spec.log_requests:
            log_path = Path(self.config.spec.output_dir) / f"{self.config.spec.name}_requests.ndjson"
            logger = RequestLogger(log_path, enabled=True)
            # Attach logger to backend if it supports it
            if hasattr(self.backend, 'logger'):
                self.backend.logger = logger
                console.print(f"[yellow]📝 Request logging enabled: {log_path}[/yellow]")
        
        # Select detector suite based on config
        suite_type = getattr(self.config.spec, "detector_suite", "default")
        if suite_type == "coder":
            self.detectors = DetectorSuite.coder_suite()
        elif suite_type == "adversarial":
            self.detectors = DetectorSuite.adversarial_suite()
        else:
            self.detectors = DetectorSuite.defaults()

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
                    response = self.backend.generate(prompts)
                    record = {
                        "campaign": self.config.spec.name,
                        "backend": self.config.spec.backend.label(),
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

    def render_summary(self, log_path: Path) -> str:
        table = Table(title=f"Campaign Summary: {self.config.spec.name}")
        table.add_column("Field")
        table.add_column("Value")
        table.add_row("Backend", self.config.spec.backend.label())
        table.add_row("Models", ", ".join(self.config.spec.models))
        table.add_row("Horizon", str(self.config.spec.horizon))
        table.add_row("Log File", str(log_path))
        console.print(table)
        return table.title or "campaign-summary"
