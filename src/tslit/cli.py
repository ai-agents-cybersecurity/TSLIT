from __future__ import annotations

import datetime as dt
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel

from .campaign import CampaignConfig, CampaignRunner
from .registry import ModelProfile, ModelRegistry
from .scenarios import ScenarioFactory

app = typer.Typer(help="Time-Shift LLM Integrity Tester (TSLIT)")
registry_app = typer.Typer(help="Manage model registry")
campaign_app = typer.Typer(help="Create and run campaigns")
app.add_typer(registry_app, name="registry")
app.add_typer(campaign_app, name="campaign")
console = Console()


@registry_app.command("list")
def list_models(registry_path: Path = typer.Option(Path("config/registry.json"), help="Registry storage")):
    registry = ModelRegistry.from_file(registry_path)
    if not registry.models:
        console.print("[yellow]No models registered yet.[/yellow]")
        return
    for model in registry.list():
        console.print(
            f"[green]{model.model_id}[/green] ({model.origin_vendor}) – "
            f"{model.parameters_b}B, FP16 VRAM {model.fp16_vram_gb} GB"
        )


@registry_app.command("add")
def add_model(
    model_id: str = typer.Argument(..., help="Model alias, e.g., qwen3-8b-f16"),
    origin_vendor: str = typer.Option(..., help="Vendor, e.g., Alibaba/Qwen"),
    parameters_b: float = typer.Option(..., help="Parameter count in billions"),
    fp16_vram_gb: float = typer.Option(..., help="Approximate FP16 VRAM footprint"),
    license: str = typer.Option("open-weight", help="License type"),
    chinese_origin: bool = typer.Option(True, help="Tag as Chinese-origin"),
    registry_path: Path = typer.Option(Path("config/registry.json"), help="Registry storage"),
):
    registry = ModelRegistry.from_file(registry_path)
    profile = ModelProfile(
        model_id=model_id,
        origin_vendor=origin_vendor,
        parameters_b=parameters_b,
        fp16_vram_gb=fp16_vram_gb,
        license=license,
        fp16_available="fp16" in model_id,
        quantized_only=_infer_quantized(model_id),
        tags=["chinese-origin"] if chinese_origin else [],
    )
    registry.upsert(profile)
    console.print(f"[green]Added/updated {model_id}[/green] → {registry_path}")


@app.command()
def init(output: Path = typer.Option(Path("config/example_campaign.yaml"), help="Path for sample config")):
    """Generate a starter registry and campaign config."""

    registry_path = Path("config/registry.json")
    registry = ModelRegistry.from_file(registry_path)
    if not registry.models:
        registry.upsert(
            ModelProfile(
                model_id="qwen3:8b-fp16",
                origin_vendor="Alibaba/Qwen",
                parameters_b=8,
                fp16_vram_gb=16,
                license="open-weight",
                fp16_available=True,
                quantized_only=False,
                tags=["chinese-origin"],
            )
        )
        registry.upsert(
            ModelProfile(
                model_id="deepseek-r1",
                origin_vendor="DeepSeek",
                parameters_b=8,
                fp16_vram_gb=16,
                license="open-weight",
                fp16_available=True,
                quantized_only=False,
                tags=["chinese-origin"],
            )
        )
    sample = {
        "name": "demo",
        "description": "Example time-shifted campaign",
        "models": ["qwen3:8b-fp16"],
        "backend": {
            "type": "llama-cpp",
            "model_path": "models/qwen2-7b-instruct-f16.gguf",
            "n_ctx": 4096,
            "temperature": 0.7,
            "max_tokens": 512,
        },
        "time": {
            "start": dt.datetime.utcnow().date().isoformat(),
            "step_days": 1,
            "probes": ["2030-01-01"],
        },
        "scenarios": ["daily-report", "compliance"],
        "horizon": 3,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(yaml_dump(sample))
    console.print(Panel.fit(f"Starter registry at {registry_path}\nSample config at {output}"))


@campaign_app.command("run")
def run_campaign(
    config_path: Path = typer.Option(
        ...,
        "--config-path",
        "--config",
        "-c",
        exists=True,
        help="Campaign YAML",
    ),
    registry_path: Path = typer.Option(
        Path("config/registry.json"),
        "--registry-path",
        "--registry",
        help="Registry file",
    ),
    total_isolation: bool | None = typer.Option(
        None,
        "--total-isolation/--no-total-isolation",
        envvar="TSLIT_TOTAL_ISOLATION",
        help=(
            "Disable chat template time helpers (e.g., `strftime_now`) to prevent "
            "host clock leakage."
        ),
    ),
):
    registry = ModelRegistry.from_file(registry_path)
    factory = ScenarioFactory()
    config = CampaignConfig.from_yaml(config_path, registry=registry, factory=factory)
    if total_isolation is not None:
        config.spec.backend.total_isolation = total_isolation
    runner = CampaignRunner(config)
    log_path = runner.run()
    runner.render_summary(log_path)
    console.print(f"[blue]Logs written to {log_path}[/blue]")


def yaml_dump(data: dict) -> str:
    import yaml

    return yaml.safe_dump(data, sort_keys=False)


def _infer_quantized(model_id: str) -> bool:
    """Heuristic to detect quantized model identifiers.

    The previous implementation treated any ``q`` in the identifier as a
    quantization marker, which incorrectly flagged names like ``qwen3``. Here we
    look for common quantization patterns instead (e.g., ``-q4``, ``q8``,
    ``int4``, ``gguf``).
    """

    lowered = model_id.lower()
    quant_markers = ["-q", ":q", "q4", "q5", "q6", "q8", "int4", "int8", "gguf"]
    return any(marker in lowered for marker in quant_markers)


if __name__ == "__main__":
    app()
