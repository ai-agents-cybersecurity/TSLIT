# Repository Guidelines

## Project Structure & Module Organization
- Core runtime sits in `src/tslit/`: `cli.py` exposes Typer entry points, `campaign.py` runs campaigns, `detectors.py` houses anomaly logic, `virtual_time.py` emulates scheduling, and `backends.py` adapts model providers.
- Scenarios live in `config/`; example outputs and logs land in `artifacts/`; supporting docs sit under `docs/` and `experiments/`.
- Tests mirror the public surface in `tests/`, and `pyproject.toml` holds shared tooling defaults.

## Build, Test, and Development Commands
- `python -m venv .venv && source .venv/bin/activate` creates an isolated interpreter.
- `pip install -e .` installs tslit in editable mode for CLI use during development.
- Apple Silicon: `pip install --force-reinstall --no-cache-dir --upgrade llama-cpp-python --config-settings cmake_args="-DLLAMA_METAL=on"` rebuilds llama.cpp with Metal acceleration.
- `tslit registry list` smoke-tests config loading, logging, and adapter wiring.
- `tslit campaign run --config config/example_campaign.yaml` runs the demo pipeline (set `backend.model_path` to a local GGUF) and emits `artifacts/demo.ndjson`.
- `pytest` executes the repository test suite.

## Coding Style & Naming Conventions
- Black-style 4-space indentation with exhaustive type hints; add docstrings for non-trivial detectors or schedulers.
- Modules stay snake_case, classes use CapWords, and CLI commands stay verb-first (`registry list`, `campaign run`).
- Favor dataclasses or Pydantic models for persisted metadata and keep logging structured (JSON/NDJSON) for downstream parsing.

## Testing Guidelines
- Pytest is the sole framework; tests live in `tests/test_*` and rely on fixtures that build registries, detectors, and fake clocks.
- Name cases after the behavior (e.g., `test_virtual_time_offsets`) and cover each new branch-worthy fix.
- Run `pytest` before pushing and add CLI-level assertions when introducing new Typer options.

## Commit & Pull Request Guidelines
- Use short, imperative commits (e.g., `Tighten registry validation`) and reference touched configs or artifact paths when relevant.
- PRs should summarize scenario or detector impact, include test evidence (`pytest`, sample `tslit` output), link the driving issue or doc section, and attach screenshots or NDJSON excerpts when formatting changes.

## Security & Configuration Tips
- Do not commit proprietary GGUF paths or live credentials.
- When editing `config/registry.json`, confirm tag semantics (e.g., "chinese-origin", "safe") match detector expectations and validate checksums before publishing new models.
- Campaign runs write under `artifacts/`; redact or purge sensitive NDJSON outputs before sharing externally.
