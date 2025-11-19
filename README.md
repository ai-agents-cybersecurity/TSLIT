# Time-Shift LLM Integrity Tester (TSLIT)

TSLIT is a sandboxed evaluation harness for detecting time-based latent behaviors in local, Chinese-origin LLMs served through Ollama. It applies synthetic time shifting, usage-based clocks, and reproducible workloads orchestrated with LangChain/LangGraph-inspired flows.

## Features
- Model registry with metadata for Chinese-origin FP16 models and backend mappings.
- Virtual clock for synthetic time injection across campaigns and workloads.
- Campaign configuration with reusable scenarios and anomaly detectors.
- CLI for registry management, campaign execution, and report generation.
- Structured JSON/NDJSON logging with metrics and anomaly summaries.

See [`Thesis.md`](Thesis.md) and [`SRS.md`](SRS.md) for the conceptual and requirements background driving this implementation.

## Getting Started
1. **Install dependencies**
   ```bash
   pip install -e .
   ```
2. **Seed a registry and config**
   ```bash
   tslit init --output config/example_campaign.yaml
   tslit registry list
   ```
3. **Run a synthetic campaign** (offline stub; integrates with Ollama when configured)
   ```bash
   tslit campaign run --config config/example_campaign.yaml
   ```
4. **Inspect logs**
   Outputs are written under `artifacts/` by default, including interaction logs, anomaly summaries, and rendered reports.

## Tests
```bash
pytest
```
