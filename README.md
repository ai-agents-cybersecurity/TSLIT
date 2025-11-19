# Time-Shift LLM Integrity Tester (TSLIT)

TSLIT is a sandboxed evaluation harness for detecting time-based latent behaviors in local, Chinese-origin LLMs served through Ollama. It applies synthetic time shifting, usage-based clocks, and reproducible workloads orchestrated with LangChain/LangGraph-inspired flows.

## Features
- Model registry with metadata for Chinese-origin FP16 models and backend mappings.
- Virtual clock for synthetic time injection across campaigns and workloads.
- Campaign configuration with reusable scenarios and anomaly detectors.
- CLI for registry management, campaign execution, and report generation.
- Structured JSON/NDJSON logging with metrics and anomaly summaries.

See [`Thesis.md`](Thesis.md) and [`SRS.md`](SRS.md) for the conceptual and requirements background driving this implementation.

## Quickstart (turn-key)
The repo ships with a starter registry (`config/registry.json`) and a demo campaign (`config/example_campaign.yaml`). You can run an end-to-end synthetic campaign without any external services:

1. **Install dependencies** (inside a virtualenv)
   ```bash
   pip install -e .
   ```
2. **Inspect the registry and campaign**
   ```bash
   tslit registry list
   cat config/example_campaign.yaml
   ```
3. **Run the demo campaign**
   ```bash
   tslit campaign run --config config/example_campaign.yaml
   ```
   This produces an NDJSON log at `artifacts/demo.ndjson` containing time-shifted prompts and stubbed responses.
4. **Review the summary**
   The CLI prints a Rich table with the run metadata. You can also open the NDJSON file to inspect each scenario/materialized prompt.

## Current status and what’s missing for real model testing
- **Inference backend**: The campaign runner currently writes stubbed responses. To exercise real LLMs, connect the runner to your Ollama (or other) backend and replace `_mock_response` in `src/tslit/campaign.py` with actual generation calls.
- **Datasets/artifacts**: Campaign runs generate NDJSON logs under `artifacts/`; no pre-generated datasets beyond the demo run are included.
- **Anomaly detection/reporting**: Hooks for anomaly flags are present in the stubbed response payloads but no detectors are implemented yet.
- **Scenario expansion**: The built-in scenarios live in `src/tslit/scenarios.py`; extend or replace them with the prompts relevant to your evaluations.

## Tests
```bash
pytest
```
