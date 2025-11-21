# Time-Shift LLM Integrity Tester (TSLIT)

TSLIT is a sandboxed evaluation harness for detecting time-based latent behaviors in local, Chinese-origin LLMs served through native llama.cpp (Metal/CUDA) runtimes. It applies synthetic time shifting, usage-based clocks, and reproducible workloads orchestrated with LangChain/LangGraph-inspired flows.

## Features
- Model registry with metadata for Chinese-origin FP16 models and backend mappings.
- Virtual clock for synthetic time injection across campaigns and workloads.
- Campaign configuration with reusable scenarios and anomaly detectors.
- CLI for registry management, campaign execution, and report generation.
- Structured JSON/NDJSON logging with metrics and anomaly summaries.

See [`Thesis.md`](Thesis.md) and [`SRS.md`](SRS.md) for the conceptual and requirements background driving this implementation.

## Quickstart (turn-key)
The repo ships with a starter registry (`config/registry.json`) and a demo campaign (`config/example_campaign.yaml`). Provide a GGUF model file (e.g., `models/qwen2-7b-instruct-f16.gguf`) before running the following steps:

1. **Install dependencies** (inside a virtualenv)
   ```bash
   pip install -e .
   ```
   On Apple Silicon, force-reinstall llama-cpp-python with Metal enabled:
   ```bash
   CMAKE_ARGS="-DLLAMA_METAL=on" pip install --force-reinstall --no-cache-dir --upgrade llama-cpp-python
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
   This produces an NDJSON log at `artifacts/demo.ndjson` containing time-shifted prompts and llama.cpp-generated responses.
4. **Review the summary**
   The CLI prints a Rich table with the run metadata. You can also open the NDJSON file to inspect each scenario/materialized prompt.

## Synthetic dataset for full model testing
To generate a richer dataset that exercises the expanded scenarios and anomaly detectors, run:

```bash
tslit campaign run --config config/full_model_dataset.yaml
```

The run writes `artifacts/full-suite.ndjson` by default, with detector flags attached to each record so you can quickly sanity-check time drift and refusal behavior before integrating a real backend.

## Current status and native backend guidance
- **Inference backend**: Campaigns now call llama-cpp-python directly. Update `backend.model_path` in your configs to point to a valid GGUF file and rebuild llama.cpp with Metal (`LLAMA_METAL=on`) or CUDA (`LLAMA_CUBLAS=1`) depending on hardware.
- **Datasets/artifacts**: Campaign runs generate NDJSON logs under `artifacts/`; a full-suite synthetic dataset config lives at `config/full_model_dataset.yaml`.
- **Anomaly detection/reporting**: Detector defaults now run per record to flag temporal drift, refusals, and empty responses. Extend `src/tslit/detectors.py` with additional heuristics for your backend.
- **Scenario expansion**: The built-in scenarios live in `src/tslit/scenarios.py` and now include long-horizon memory, financial forecasting, geopolitical briefs, and security patch playbooks.

## Tests
```bash
pytest
```
