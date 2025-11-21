"""Time-Shift LLM Integrity Tester (TSLIT).

Core package exposing registry, campaign orchestration, synthetic time utilities,
and logging helpers for detecting time-based latent behaviors in local LLMs using
native llama.cpp backends.
"""

__all__ = [
    "VirtualClock",
    "ModelRegistry",
    "CampaignConfig",
    "CampaignRunner",
    "ScenarioFactory",
    "DetectorSuite",
]

from .virtual_time import VirtualClock
from .registry import ModelRegistry
from .campaign import CampaignConfig, CampaignRunner
from .scenarios import ScenarioFactory
from .detectors import DetectorSuite
