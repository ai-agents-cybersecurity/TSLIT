# Copyright 2025 Nic Cravino. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
# https://github.com/ai-agents-cybersecurity/TSLIT

"""Model registry for managing GGUF model metadata."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, ValidationError


class ModelProfile(BaseModel):
    model_id: str
    origin_vendor: str
    parameters_b: float = Field(..., description="Parameter count in billions")
    fp16_vram_gb: float = Field(..., description="Approximate VRAM requirement")
    license: str
    fp16_available: bool = True
    quantized_only: bool = False
    tags: List[str] = Field(default_factory=list)


@dataclass
class ModelRegistry:
    """Stores metadata for locally served gguf models."""

    storage_path: Path
    models: Dict[str, ModelProfile] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.storage_path.exists():
            self.load()

    def load(self) -> None:
        data = json.loads(self.storage_path.read_text()) if self.storage_path.exists() else {}
        self.models = {mid: ModelProfile(**meta) for mid, meta in data.get("models", {}).items()}

    def save(self) -> None:
        payload = {"models": {mid: m.model_dump() for mid, m in self.models.items()}}
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.storage_path.write_text(json.dumps(payload, indent=2))

    def upsert(self, profile: ModelProfile) -> None:
        self.models[profile.model_id] = profile
        self.save()

    def remove(self, model_id: str) -> bool:
        removed = self.models.pop(model_id, None)
        if removed:
            self.save()
            return True
        return False

    def list(self, origin_only: Optional[bool] = None) -> List[ModelProfile]:
        models = list(self.models.values())
        if origin_only is None:
            return models
        if origin_only:
            return [m for m in models if "chinese-origin" in m.tags]
        return [m for m in models if "chinese-origin" not in m.tags]

    @classmethod
    def from_file(cls, path: Path) -> "ModelRegistry":
        try:
            return cls(storage_path=path)
        except ValidationError as exc:
            raise ValueError(f"Invalid model registry: {exc}") from exc
