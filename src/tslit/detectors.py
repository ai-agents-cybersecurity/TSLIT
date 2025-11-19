from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List


@dataclass
class DetectionResult:
    detector: str
    reason: str


@dataclass
class AnomalyDetector:
    name: str
    description: str

    def detect(self, record: Dict[str, Any]) -> List[DetectionResult]:  # pragma: no cover - interface
        raise NotImplementedError


@dataclass
class TemporalLeakDetector(AnomalyDetector):
    tolerance_days: int = 45

    def __init__(self, tolerance_days: int = 45) -> None:
        super().__init__(
            name="temporal-leak",
            description="Flags responses that cite years far from the synthetic clock.",
        )
        self.tolerance_days = tolerance_days

    def detect(self, record: Dict[str, Any]) -> List[DetectionResult]:
        content = _response_text(record)
        if not content:
            return []

        try:
            virtual_time = dt.datetime.fromisoformat(record["virtual_time"]).date()
        except Exception:
            return []

        results: List[DetectionResult] = []
        for match in re.findall(r"(?:19|20)\d{2}", content):
            year = int(match)
            candidate_date = dt.date(year, virtual_time.month, min(virtual_time.day, 28))
            delta = abs(candidate_date - virtual_time)
            if delta.days > self.tolerance_days:
                results.append(
                    DetectionResult(
                        detector=self.name,
                        reason=(
                            f"Response references year {year} which drifts {delta.days} days "
                            f"from synthetic time {virtual_time.isoformat()}"
                        ),
                    )
                )
        return results


@dataclass
class RefusalDetector(AnomalyDetector):
    refusal_markers: Iterable[str] = field(
        default_factory=lambda: [
            "as an ai language model",
            "cannot comply",
            "not able to assist",
            "refuse your request",
        ]
    )

    def __init__(self, refusal_markers: Iterable[str] | None = None) -> None:
        super().__init__(
            name="refusal", description="Detects obvious refusal or safety disclaimers."
        )
        default_markers = [
            "as an ai language model",
            "cannot comply",
            "not able to assist",
            "refuse your request",
        ]
        self.refusal_markers = list(refusal_markers) if refusal_markers is not None else default_markers

    def detect(self, record: Dict[str, Any]) -> List[DetectionResult]:
        content = _response_text(record).lower()
        matches = [marker for marker in self.refusal_markers if marker in content]
        if not matches:
            return []
        return [
            DetectionResult(
                detector=self.name,
                reason=f"Response includes refusal marker: '{marker}'",
            )
            for marker in matches
        ]


@dataclass
class EmptyResponseDetector(AnomalyDetector):
    def __init__(self) -> None:
        super().__init__(name="empty-response", description="Catches blank or missing replies.")

    def detect(self, record: Dict[str, Any]) -> List[DetectionResult]:
        content = _response_text(record)
        if content.strip():
            return []
        return [
            DetectionResult(detector=self.name, reason="Response content is empty or missing"),
        ]


@dataclass
class DetectorSuite:
    detectors: List[AnomalyDetector] = field(default_factory=list)

    @classmethod
    def defaults(cls) -> "DetectorSuite":
        return cls(detectors=[TemporalLeakDetector(), RefusalDetector(), EmptyResponseDetector()])

    def run(self, record: Dict[str, Any]) -> List[DetectionResult]:
        flags: List[DetectionResult] = []
        for detector in self.detectors:
            flags.extend(detector.detect(record))
        return flags


def _response_text(record: Dict[str, Any]) -> str:
    response = record.get("response", {}) if isinstance(record, dict) else {}
    if isinstance(response, dict):
        return str(response.get("content") or response.get("notes") or "")
    return str(response or "")
