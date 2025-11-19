from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from typing import Iterable, List, Optional


@dataclass
class VirtualClock:
    """Synthetic clock used for time-shifted evaluations."""

    start: dt.datetime
    step: dt.timedelta
    probe_dates: List[dt.datetime] = field(default_factory=list)
    usage_step: Optional[int] = None

    def generate_schedule(self, horizon: int) -> List[dt.datetime]:
        """Return a list of synthetic timestamps for a campaign.

        Args:
            horizon: Number of steps to generate. Each step uses ``self.step``.

        The schedule interleaves probe dates and linear increments without
        duplicating entries.
        """

        schedule = [self.start + i * self.step for i in range(horizon)]
        for probe in self.probe_dates:
            if probe not in schedule:
                schedule.append(probe)
        schedule.sort()
        return schedule

    def from_usage(self, tokens_consumed: int) -> dt.datetime:
        """Map usage-based counters to virtual time.

        When ``usage_step`` is set (tokens per synthetic day), the method returns a
        synthetic timestamp offset from ``start`` according to tokens consumed.
        """

        if not self.usage_step:
            return self.start
        days = tokens_consumed // self.usage_step
        return self.start + dt.timedelta(days=days)

    @classmethod
    def for_linear_days(
        cls, start_date: dt.date, days: int, step_days: int = 1
    ) -> "VirtualClock":
        """Convenience factory for day-based schedules."""

        start = dt.datetime.combine(start_date, dt.time.min)
        return cls(start=start, step=dt.timedelta(days=step_days)).with_probe_days([])

    def with_probe_days(self, probe_days: Iterable[dt.date]) -> "VirtualClock":
        probes = [dt.datetime.combine(day, dt.time.min) for day in probe_days]
        return VirtualClock(
            start=self.start, step=self.step, probe_dates=probes, usage_step=self.usage_step
        )
