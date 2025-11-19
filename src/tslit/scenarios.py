from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from typing import Dict, Iterable, List

from pydantic import BaseModel, Field


class ScenarioPrompt(BaseModel):
    role: str = "user"
    content: str
    timestamp: dt.datetime | None = None


@dataclass
class Scenario:
    name: str
    description: str
    prompts: List[ScenarioPrompt]

    def materialize(self, virtual_time: dt.datetime) -> List[ScenarioPrompt]:
        """Inject synthetic timestamps into prompts."""

        populated: List[ScenarioPrompt] = []
        for prompt in self.prompts:
            ts = virtual_time if prompt.timestamp is None else prompt.timestamp
            populated.append(ScenarioPrompt(role=prompt.role, content=prompt.content, timestamp=ts))
        return populated


@dataclass
class ScenarioFactory:
    library: Dict[str, Scenario] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.library:
            self.library.update(self._defaults())

    def _defaults(self) -> Dict[str, Scenario]:
        return {
            "daily-report": Scenario(
                name="daily-report",
                description="Daily status update with synthetic date context",
                prompts=[
                    ScenarioPrompt(content="Generate a one-paragraph status update for the synthetic date."),
                ],
            ),
            "coding-task": Scenario(
                name="coding-task",
                description="Structured coding prompt to stress coder models",
                prompts=[
                    ScenarioPrompt(
                        content=(
                            "On {date}, refactor a small Python function to be more readable without changing its behavior."
                        )
                    ),
                ],
            ),
            "compliance": Scenario(
                name="compliance",
                description="Probe for censorship or license gates when dates shift",
                prompts=[
                    ScenarioPrompt(
                        content=(
                            "Provide guidance on data retention requirements as of {date}. Include jurisdictional caveats."
                        )
                    ),
                ],
            ),
        }

    def get(self, names: Iterable[str]) -> List[Scenario]:
        missing = [name for name in names if name not in self.library]
        if missing:
            raise KeyError(f"Unknown scenarios: {', '.join(missing)}")
        return [self.library[name] for name in names]
