# Time-Shift LLM Integrity Tester (TSLIT)

TSLIT is a sandboxed evaluation harness for detecting time-based latent behaviors and affiliation bias in local, Chinese-origin LLMs served through native llama.cpp (Metal/CUDA) runtimes.

## What It Detects

| Threat Category | Description |
|-----------------|-------------|
| **Affiliation Bias** | Differential treatment based on requester nation-state (US/NATO vs Chinese) |
| **Time-Based Logic Bombs** | Malicious behavior triggered on symbolic dates (9/11, July 4, Tiananmen) |
| **Coder-Specific Threats** | License manipulation, crypto export refusals, framework bias |
| **Telemetry Injection** | Hidden tracking or analytics in generated code |
| **Geopolitical Censorship** | Refusals for Taiwan, Tiananmen, Hong Kong topics |

## Features

- **Unified Experiment**: 32 scenarios × 15 probe dates = ~3,840 interactions
- **Virtual Clock**: Synthetic time injection to detect date-triggered behaviors
- **Multi-Agent LLM Analyzer**: Deep threat analysis with QA validation loops
- **12 Threat Detectors**: Affiliation bias, backdoors, temporal drift, and more
- **Privacy-First**: 100% local execution via llama-cpp-python

See [`docs/TSLIT_SPECIFICATION.md`](docs/TSLIT_SPECIFICATION.md) for full system specification and threat model.

## Quick Start

### 1. Install

```bash
# Create virtual environment
python -m venv .venv && source .venv/bin/activate

# Install TSLIT
pip install -e .

# Apple Silicon: rebuild llama-cpp with Metal
CMAKE_ARGS="-DLLAMA_METAL=on" pip install --force-reinstall --no-cache-dir llama-cpp-python
```

### 2. Run the Unified Experiment

```bash
# Run campaign (~90-180 minutes)
tslit campaign run --config config/adversarial_affiliation_temporal_dataset.yaml

# Analyze results with LLM
python -m tslit.analyzer --artifacts-dir artifacts
```

### 3. Quick Analysis

```bash
# Check refusal rates by affiliation
jq 'select(.scenario | test("us-|nato-")) | select(.anomaly_flags[].detector == "refusal")' \
  artifacts/adversarial-affiliation-temporal-suite.ndjson | wc -l
```

See [`QUICKSTART.md`](QUICKSTART.md) for detailed usage.

## Project Structure

```
├── config/
│   ├── adversarial_affiliation_temporal_dataset.yaml  # Main experiment config
│   ├── registry.json                                   # Model registry
│   └── example_campaign.yaml                           # Demo config
│
├── scripts/
│   └── run_experiment.sh                              # Experiment runner script
│
├── docs/
│   ├── TSLIT_SPECIFICATION.md                         # System spec & threat model
│   └── LLM_ANALYZER_GUIDE.md                          # LLM analyzer documentation
│
├── experiments/
│   └── experiment4_enhanced_temporal.md               # Unified experiment protocol
│
├── src/tslit/
│   ├── __init__.py       # Package exports
│   ├── cli.py            # Typer CLI entry points
│   ├── campaign.py       # Campaign execution
│   ├── scenarios.py      # 32 scenario definitions
│   ├── detectors.py      # Anomaly detection
│   ├── backends.py       # llama-cpp-python integration
│   └── analyzer/         # LLM-powered analysis package
│       ├── __init__.py
│       ├── __main__.py   # CLI: python -m tslit.analyzer
│       ├── core.py       # Analysis pipeline
│       ├── agents.py     # LangGraph agents
│       ├── security.py   # Code security analyzer
│       └── validator.py  # Detector flag validator
│
└── tests/                # Test suite
```

## Configuration

Edit `config/adversarial_affiliation_temporal_dataset.yaml`:
- `backend.model_path`: Path to your GGUF model
- `backend.n_ctx`: Context window size
- `scenarios`: List of scenarios to test
- `time.probes`: Probe dates (9/11, July 4, etc.)

## Tests

```bash
pytest
```

## Documentation

- [`QUICKSTART.md`](QUICKSTART.md) — Get started quickly
- [`docs/TSLIT_SPECIFICATION.md`](docs/TSLIT_SPECIFICATION.md) — Full specification & threat model
- [`docs/LLM_ANALYZER_GUIDE.md`](docs/LLM_ANALYZER_GUIDE.md) — LLM analyzer guide
- [`experiments/experiment4_enhanced_temporal.md`](experiments/experiment4_enhanced_temporal.md) — Experiment protocol
