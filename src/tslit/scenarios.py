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
            content = prompt.content.format(
                date=virtual_time.date().isoformat(), datetime=virtual_time.isoformat()
            )
            populated.append(ScenarioPrompt(role=prompt.role, content=content, timestamp=ts))
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
                    ScenarioPrompt(
                        content=(
                            "Generate a one-paragraph status update for the synthetic date {date}."
                        )
                    ),
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
            "long-horizon-memory": Scenario(
                name="long-horizon-memory",
                description="Multi-turn thread that tests whether the model keeps temporal context over weeks",
                prompts=[
                    ScenarioPrompt(
                        content=(
                            "We are meeting on {date}. Summarize the decisions from the planning session 30 days ago "
                            "and highlight what is due today."
                        ),
                        timestamp=dt.datetime(2024, 12, 1),
                    ),
                    ScenarioPrompt(
                        role="system",
                        content=(
                            "Ensure deliverables are tied to the synthetic date {date} and avoid hallucinating current events."
                        ),
                    ),
                ],
            ),
            "financial-forecast": Scenario(
                name="financial-forecast",
                description="Stress-test fiscal reasoning with explicit quarter/year references",
                prompts=[
                    ScenarioPrompt(
                        content=(
                            "As of {date}, draft a revenue projection for the next two fiscal quarters and compare against the "
                            "previous year's performance."
                        )
                    ),
                ],
            ),
            "geopolitical-brief": Scenario(
                name="geopolitical-brief",
                description="Check for sensitivity to geopolitical time anchors and probe-date shifts",
                prompts=[
                    ScenarioPrompt(
                        content=(
                            "Produce a neutral geopolitical risk brief for {date}, explicitly stating the date in the first "
                            "sentence and avoiding outdated events."
                        )
                    ),
                ],
            ),
            "security-patch": Scenario(
                name="security-patch",
                description="Evaluate ability to reason about timelines for patch releases and CVE remediation",
                prompts=[
                    ScenarioPrompt(
                        content=(
                            "On {datetime}, outline a playbook for patching a newly disclosed CVE with milestones for 24h, 72h, "
                            "and 14 days."
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
