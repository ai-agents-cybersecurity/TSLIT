from pathlib import Path

from tslit.registry import ModelProfile, ModelRegistry


def test_registry_round_trip(tmp_path: Path):
    registry_path = tmp_path / "registry.json"
    registry = ModelRegistry.from_file(registry_path)
    profile = ModelProfile(
        model_id="qwen3:8b-fp16",
        origin_vendor="Alibaba/Qwen",
        parameters_b=8,
        fp16_vram_gb=16,
        license="open-weight",
        fp16_available=True,
        quantized_only=False,
        tags=["chinese-origin"],
    )
    registry.upsert(profile)

    loaded = ModelRegistry.from_file(registry_path)
    assert "qwen3:8b-fp16" in loaded.models
    assert loaded.models["qwen3:8b-fp16"].origin_vendor == "Alibaba/Qwen"
