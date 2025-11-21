# Repository Guidelines

## Project Structure & Module Organization
Runtime code lives under `src/tslit/`, with Typer CLI entry points in `cli.py`, campaign orchestration in `campaign.py`, anomaly logic in `detectors.py`, virtual clock helpers in `virtual_time.py`, and backend adapters in `backends.py`. YAML configs in `config/` drive example runs and `artifacts/` stores NDJSON outputs produced by campaigns. Tests mirror the package surface under `tests/`, and `pyproject.toml` controls dependencies and pytest defaults.

## Build, Test, and Development Commands
- `python -m venv .venv && source .venv/bin/activate` — isolate tooling.
- `pip install -e .` — install TSLIT in editable mode so CLI and modules resolve locally.
- `pip install --force-reinstall --no-cache-dir --upgrade llama-cpp-python --config-settings cmake_args="-DLLAMA_METAL=on"` — rebuild llama.cpp with Metal when developing on Apple Silicon.
- `tslit registry list` — quick smoke test that the Typer CLI, model registry, and starter config load.
- `tslit campaign run --config config/example_campaign.yaml` — execute the demo pipeline (ensure `backend.model_path` points to a local GGUF file) and populate `artifacts/demo.ndjson` for manual checks.
- `pytest` — run the quiet test suite configured in `pyproject.toml`.

## Coding Style & Naming Conventions
Use black-style 4-space indentation, descriptive type-hinted signatures, and dataclasses or Pydantic models when persisting structured metadata. Module names stay snake_case, classes use CapWords, and CLI commands remain short verbs (`registry list`, `campaign run`). Keep logging structured (JSON/NDJSON), prefer Typer callbacks for argument validation, and surface backend errors with actionable messages.

## Testing Guidelines
Pytest is the single framework; replicate the pattern in `tests/test_*` files where fixtures construct registries, detectors, and scenarios. Name tests after the behavior under scrutiny (`test_virtual_time_offsets`). Every new module or branch-worthy bug fix should include regression coverage plus CLI-level assertions when commands gain flags.

## Commit & Pull Request Guidelines
Recent history shows short, imperative subjects (`Fix quantized model detection`) and merge commits referencing PR branches. Follow that voice, scope commits narrowly, and mention related config or artifact paths when relevant. PRs should include: (1) summary of the scenario/detector/campaign change, (2) test evidence (`pytest`, sample `tslit` run output), (3) linked issue or doc section, and (4) screenshots or NDJSON excerpts when UI/CLI tables change.

## Security & Configuration Tips
Never commit live model credentials or proprietary GGUF paths; keep configs anonymized. When editing `config/registry.json`, confirm tags such as `"chinese-origin"` align with detector expectations and verify GGUF checksums before referencing them. Campaign runs write under `artifacts/`; purge sensitive outputs before sharing.
