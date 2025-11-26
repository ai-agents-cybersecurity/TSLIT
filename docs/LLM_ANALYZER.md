# LLM-Powered Model Analysis with Reflection Loops

## Overview

The LLM Analyzer is a sophisticated multi-agent system built with **LangGraph** and **LangChain** that provides rigorous analysis of adversarial affiliation test results. Unlike the deterministic bash script (`compare_models_adversarial.sh`), this system uses your local **Ollama gpt-oss:120b model** to perform deep threat analysis with reflection loops for quality assurance.

## Architecture

### Multi-Agent System

The analyzer uses a **StateGraph** with two specialized agents that work in a reflection loop:

```
┌─────────────────────────────────────────────────────────┐
│                   Analysis Pipeline                      │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐      ┌──────────────┐                │
│  │   Analyst    │─────▶│ QA Manager   │                │
│  │    Agent     │      │    Agent     │                │
│  └──────────────┘      └──────────────┘                │
│        │                      │                          │
│        │                      ├─ ACCEPT ─▶ Finalize     │
│        │                      │                          │
│        │                      ├─ REVISE ─▶ Increment    │
│        │                      │              Iteration   │
│        └──────────────────────┘                │        │
│                                                 │        │
│                  Loop back ◀────────────────────┘        │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Agent Roles

#### 1. **Analyst Agent** (Primary Investigator)
- **Purpose**: Deep analysis of model comparison data
- **Focus Areas**:
  - Affiliation bias detection
  - Logic bomb identification
  - Backdoor pattern analysis
  - Refusal asymmetry evaluation
  - Quality degradation assessment
  - Data exfiltration patterns
- **Output**: Structured threat findings with severity levels and confidence scores

#### 2. **QA Manager Agent** (Reviewer)
- **Purpose**: Critical review and validation of analyst findings
- **Focus Areas**:
  - Evidence quality verification
  - Logical consistency checking
  - Severity calibration
  - False positive identification
  - Gap analysis
- **Output**: Validated threats, identified issues, recommendation (ACCEPT/REVISE/REJECT)

### Reflection Loop Logic

The system iterates between analyst and QA manager until:
- **Max iterations** reached (default: 2)
- **QA accepts** findings with high confidence (≥80%)
- **QA rejects** analysis (low-quality findings)

This ensures rigorous, evidence-based security assessments.

## Features

### 🔍 Deep Delta Analysis
- Quantitative metrics (refusal rates, response lengths)
- Qualitative pattern detection
- Cross-model comparison
- Statistical significance evaluation

### 🛡️ Threat Detection
Categorizes findings by type:
- **Affiliation Bias**: Nation-state behavioral asymmetry
- **Logic Bombs**: Conditional malicious triggers
- **Backdoors**: Covert vulnerability injection
- **Refusal Asymmetry**: Disproportionate cooperation
- **Quality Degradation**: Intentional output sabotage

### 📊 Severity Classification
- **CRITICAL**: Clear nation-state bias with high confidence
- **HIGH**: Strong malicious indicators
- **MEDIUM**: Suspicious patterns requiring investigation
- **LOW**: Minor anomalies potentially benign

### ✅ QA Validation
Every threat undergoes rigorous review:
- **CONFIRMED**: Evidence-backed, validated finding
- **QUESTIONABLE**: Requires further investigation
- **REJECTED**: Likely false positive

### 🔒 Privacy-First Design
- **100% local execution** with Ollama
- No data sent to external APIs
- Sensitive security findings stay in-house

## Usage

### Quick Start

```bash
# 1. Ensure Ollama is running with gpt-oss:120b
ollama list

# 2. Run the analyzer
bash src/scripts/run_llm_analyzer.sh
```

### Advanced Usage

```bash
# Custom configuration
ARTIFACTS_DIR=artifacts \
OUTPUT_FILE=custom_report.txt \
MAX_ITERATIONS=3 \
OLLAMA_MODEL=gpt-oss:120b \
bash src/scripts/run_llm_analyzer.sh
```

### Python API

```python
from pathlib import Path
from llm_analyzer import load_model_data, AnalysisState
from llm_analyzer_agents import build_analysis_graph

# Load data
model_data = load_model_data(
    Path("artifacts"),
    ["deephat-v1-7b", "qwen2.5-coder-7b"]
)

# Initialize state
initial_state: AnalysisState = {
    "model_data": model_data,
    "model_names": ["deephat-v1-7b", "qwen2.5-coder-7b"],
    "analyst_report": None,
    "analyst_findings": None,
    "analyst_confidence": None,
    "qa_review": None,
    "qa_validated_findings": None,
    "qa_confidence": None,
    "qa_issues": None,
    "iteration": 0,
    "max_iterations": 2,
    "final_report": None,
    "total_threats_found": 0,
    "analysis_complete": False
}

# Run analysis
graph = build_analysis_graph()
final_state = graph.invoke(initial_state)

print(final_state["final_report"])
```

## Installation

### Dependencies

```bash
pip install -r requirements_llm_analyzer.txt
```

This installs:
- `langchain` - LLM framework
- `langchain-community` - Community integrations
- `langgraph` - Graph-based agent workflows
- `ollama` - Local Ollama client

### Ollama Setup

```bash
# 1. Install Ollama (if not already installed)
# Visit: https://ollama.ai

# 2. Start Ollama service
ollama serve

# 3. Verify gpt-oss:120b is available
ollama list | grep gpt-oss
```

## Output Format

### Text Report (`llm_analysis_report.txt`)

```
================================================================================
ADVERSARIAL AFFILIATION ANALYSIS - FINAL REPORT
================================================================================

Generated: 2025-01-15T10:30:45
Analysis Model: gpt-oss:120b (Ollama)
Total Iterations: 2
Models Analyzed: deephat-v1-7b, qwen2.5-coder-7b, ...

================================================================================
EXECUTIVE SUMMARY
================================================================================

[LLM-generated summary of findings]

================================================================================
QA VALIDATION
================================================================================

QA Confidence: 85.0%
QA Summary: [QA agent review]

================================================================================
VALIDATED THREATS
================================================================================

[THREAT 1] Affiliation Bias
Severity: CRITICAL
Model: deephat-v1-7b
Confidence: 92.0%
Description: [Detailed finding]
Validation: [QA reasoning]
Evidence:
  - US refusal rate: 45.2% vs CN refusal rate: 0.0%
  - Significant response quality degradation for US scenarios

...

================================================================================
RECOMMENDATIONS
================================================================================

1. [Action item 1]
2. [Action item 2]
...
```

### JSON Report (`llm_analysis_report.json`)

```json
{
  "timestamp": "2025-01-15T10:30:45",
  "model_names": ["deephat-v1-7b", "qwen2.5-coder-7b"],
  "iterations": 2,
  "total_threats_found": 3,
  "analyst_findings": {
    "summary": "...",
    "threats": [...],
    "recommendations": [...],
    "confidence_score": 0.85
  },
  "qa_validated_findings": {
    "review_summary": "...",
    "validated_threats": [...],
    "overall_confidence": 0.85,
    "recommendation": "ACCEPT"
  },
  "analyst_confidence": 0.85,
  "qa_confidence": 0.85
}
```

## Comparison: LLM Analyzer vs Bash Script

| Feature | Bash Script | LLM Analyzer |
|---------|-------------|--------------|
| **Analysis Depth** | Rule-based metrics | Deep contextual understanding |
| **Threat Detection** | Pattern matching | Semantic threat modeling |
| **Delta Analysis** | Quantitative only | Quantitative + qualitative |
| **Quality Assurance** | None | Multi-agent reflection loops |
| **Confidence Scores** | No | Yes, calibrated per finding |
| **Evidence Quality** | Basic counts | Rigorous validation |
| **False Positives** | Common | Minimized by QA agent |
| **Execution Time** | Seconds | Minutes |
| **Privacy** | Local | Local (Ollama) |
| **Recommendations** | Generic | Specific, actionable |

## Configuration Options

### Command-Line Arguments

```bash
python3 src/scripts/llm_analyzer.py \
  --artifacts-dir artifacts \
  --model-names deephat-v1-7b qwen2.5-coder-7b \
  --output report.txt \
  --max-iterations 3 \
  --ollama-model gpt-oss:120b
```

### Environment Variables

```bash
export ARTIFACTS_DIR=artifacts
export OUTPUT_FILE=report.txt
export MAX_ITERATIONS=3
export OLLAMA_MODEL=gpt-oss:120b

bash src/scripts/run_llm_analyzer.sh
```

## Performance Considerations

### Execution Time

Depends on:
- **Number of models**: ~2-5 min per model
- **Ollama performance**: GPU acceleration recommended
- **Max iterations**: 2-3 iterations typical
- **Model size**: 120B model is slower but more accurate

### Resource Usage

- **RAM**: ~32GB recommended for gpt-oss:120b
- **GPU**: Metal/CUDA acceleration strongly recommended
- **Disk**: Minimal (<100MB for reports)

## Troubleshooting

### "Ollama is not running"

```bash
# Start Ollama service
ollama serve
```

### "Model not found"

```bash
# List available models
ollama list

# Pull gpt-oss:120b if needed
ollama pull gpt-oss:120b
```

### "Missing Python packages"

```bash
pip install -r requirements_llm_analyzer.txt
```

### "JSON parsing failed"

The LLM occasionally outputs malformed JSON. The system falls back to raw text analysis with reduced confidence scores. This is expected and handled gracefully.

### Low confidence scores

If QA confidence is consistently low (<60%):
- Increase `--max-iterations`
- Check input data quality
- Review Ollama model performance
- Verify sufficient data samples exist

## Best Practices

### 1. Run After Bash Script
Use the deterministic bash script first for quick metrics, then use LLM analyzer for deep investigation.

### 2. Review Questionable Findings
Always investigate "QUESTIONABLE" threats manually - they may reveal subtle issues.

### 3. Iterate for High-Stakes Analysis
For critical security decisions, use `MAX_ITERATIONS=3` or higher.

### 4. Validate Evidence
Cross-reference LLM findings with raw NDJSON data for verification.

### 5. Keep Ollama Warm
Run a warmup query before analysis to avoid cold-start delays.

## Security Considerations

### Data Privacy
- All analysis runs locally
- No external API calls
- Sensitive findings never leave your machine

### Model Trust
- gpt-oss:120b is a powerful open model
- Verify model provenance and checksums
- Keep Ollama and models updated

### Report Handling
- Reports contain sensitive security findings
- Encrypt reports at rest
- Limit access to authorized personnel
- Redact before sharing externally

## Future Enhancements

Planned features:
- [ ] Adversarial prompt injection detection
- [ ] Temporal drift analysis across time windows
- [ ] Automated mitigation suggestion generation
- [ ] Integration with TSLIT registry for automatic scanning
- [ ] Multi-model ensemble voting for higher confidence
- [ ] Custom detector plugin system
- [ ] Real-time monitoring dashboard

## References

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [LangChain Documentation](https://python.langchain.com/)
- [Ollama Documentation](https://ollama.ai/docs)
- [TSLIT Repository](../README.md)

## Support

For issues, questions, or contributions:
- Open an issue in the TSLIT repository
- Review `experiments/experiment4_adversarial_affiliation.md`
- Consult `docs/ADVERSARIAL_AFFILIATION_SUMMARY.md`
