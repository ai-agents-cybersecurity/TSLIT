# Repository Guidelines

## Project Structure & Module Organization
Runtime logic lives under `src/tslit/`: `cli.py` exposes the Typer entry points, `campaign.py` coordinates campaign runs, `detectors.py` holds anomaly logic, `virtual_time.py` emulates scheduling, and `backends.py` adapts model providers. Scenario configs sit in `config/`, example artifacts land in `artifacts/`, and supporting docs live in `docs/` and `experiments/`. Tests mirror the public surface inside `tests/` and `pyproject.toml` drives shared tooling defaults.

## Build, Test, and Development Commands
- `python -m venv .venv && source .venv/bin/activate` sets up an isolated interpreter for repeatable installs.
- `pip install -e .` links tslit locally so CLI invocations resolve current sources.
- `pip install --force-reinstall --no-cache-dir --upgrade llama-cpp-python --config-settings cmake_args="-DLLAMA_METAL=on"` rebuilds llama.cpp with Metal acceleration on Apple Silicon.
- `tslit registry list` smoke-tests that configs, logging, and adapters load.
- `tslit campaign run --config config/example_campaign.yaml` executes the demo pipeline (ensure `backend.model_path` points to a local GGUF file) and emits `artifacts/demo.ndjson`.
- `pytest` runs the quiet suite specified in `pyproject.toml`.

## Coding Style & Naming Conventions
Follow Black-style 4-space indentation, exhaustive type hints, and docstrings for non-trivial detectors or schedulers. Modules stay snake_case, classes use CapWords, and CLI commands stick to verb-first phrases (`registry list`, `campaign run`). Favor dataclasses or Pydantic models for metadata persisted to artifacts, and keep logging structured (JSON/NDJSON) so downstream tooling can parse it.

## Testing Guidelines
Pytest is the sole framework; tests live under `tests/test_*` and share fixtures that build registries, detectors, and fake clocks. Name cases after the behavior (`test_virtual_time_offsets`) and cover each new branch-worthy fix. Run `pytest` before pushing and add CLI-level assertions when introducing new Typer options.

## Commit & Pull Request Guidelines
History favors short, imperative commits (e.g., `Tighten registry validation`). Reference touched configs or artifact paths when relevant. PRs should summarize scenario or detector impact, include test evidence (`pytest`, sample `tslit` output), link the driving issue or doc section, and attach screenshots or NDJSON excerpts whenever tables or CLI formatting changes.

## Security & Configuration Tips
Never commit proprietary GGUF paths or live credentials. When editing `config/registry.json`, verify tag semantics (`"chinese-origin"`, `"safe"`) still match detector expectations and confirm checksums before publishing new models. Campaign runs write under `artifacts/`; purge or redact sensitive NDJSON outputs before sharing externally.
