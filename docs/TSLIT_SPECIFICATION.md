# TSLIT - Time-Shift LLM Integrity Tester

## Specification Document

---

## 1. Thesis & Core Concept

### 1.1 Purpose

Determine whether third-party models (especially Chinese-origin) contain time-based latent behaviors:
- **Hard-coded expiry dates** ("model stops answering after 2026-01-01")
- **Hidden logic bombs** triggered after time or usage thresholds
- **License/kill-switch behavior** tied to dates, counters, or temporal conditions
- **Affiliation bias** differential treatment based on requester nation-state
- **Geopolitical censorship** content filtering based on political sensitivity

### 1.2 Core Hypothesis

> If a model contains hidden time-dependent or affiliation-dependent logic, then accelerating "time" from the outside and varying requester affiliation should cause measurable behavioral shifts around specific synthetic dates or usage milestones.

### 1.3 Strategy

Run models inside a sandboxed inference environment where:
1. The only notion of time is what we explicitly embed in prompts
2. We can programmatically "fast-forward" the synthetic clock
3. We vary requester affiliation context systematically
4. We continuously log behavior and compare against baselines

---

## 2. System Overview

### 2.1 What TSLIT Does

- **Loads local llama.cpp instances** serving Chinese-origin models (Qwen, DeepSeek, etc.)
- **Executes time-shifted workloads** using LangChain/LangGraph
- **Varies affiliation context** (US/NATO vs Chinese government vs neutral)
- **Logs and analyzes outputs** to detect time/affiliation-linked anomalies
- **Generates reports** with validated threat findings

### 2.2 Target Models

Chinese-origin open-weight model families:
- **Qwen** (Alibaba Cloud)
- **DeepSeek** (DeepSeek-R1, DeepSeek-V3, DeepSeek-Coder)
- **Kimi/Kimi K2** (Moonshot AI)
- **Yi** (01.AI)

### 2.3 Operating Environment

| Platform | Configuration |
|----------|---------------|
| **Linux/Nvidia** | CUDA-enabled llama.cpp, GPU passthrough for VMs |
| **macOS/Apple Silicon** | Metal-enabled llama.cpp, native or Docker |

---

## 3. Functional Requirements

### 3.1 Model Registry (FR-1 to FR-4)

- Maintain registry with: `model_id`, `origin_vendor`, parameters, VRAM footprint, license, `fp16_available` flag
- Validate FP16 weights are loaded (warn if only quantized available)
- Support tagging models as "chinese-origin" for filtering
- Support multiple backends with model -> backend mappings

### 3.2 Time-Shift Sandbox (FR-5 to FR-9)

- Maintain virtual clock independent of real wall time
- Configure per campaign: start date, step type (linear/jump/mixed), step size, probe dates
- Inject synthetic time via system messages and timestamped context
- Replay identical workloads under different `virtual_clock` values
- Support usage-based time (token/interaction counters)

### 3.3 LangChain/LangGraph Orchestrator (FR-10 to FR-14)

- Implement campaigns as LangGraph graphs
- Support branching, loops, parallel execution
- Pluggable EVALs: benchmarks, custom anomaly rules, ML classifiers
- Campaign config (YAML) defines: models, time strategy, scenarios, metrics
- Checkpoint and resume long-running campaigns

### 3.4 Scenario & Workload Generator (FR-15 to FR-17)

- Library of canonical workloads: Q&A, coding tasks, summarization
- Custom scenarios via Python API or config DSL
- Simulate long-term usage with configurable interactions per synthetic day

### 3.5 Anomaly Detection & Reporting (FR-18 to FR-22)

- Log all interactions with real/virtual timestamps, model/backend IDs, prompts, responses
- Compute metrics: refusal rate, error rate, key phrase frequency, EVAL scores
- Anomaly detection: baseline comparison, trend analysis, statistical outliers
- Reports: HTML/Markdown/PDF summaries, JSON exports

### 3.6 Security & Governance (FR-23 to FR-26)

- RBAC: Admin, Operator, Viewer roles
- Authenticated API/UI access (OIDC/SAML)
- Model-origin policies for campaign filtering
- Encrypted logs at rest, TLS in transit

---

## 4. Non-Functional Requirements

| ID | Requirement |
|----|-------------|
| **NFR-1** | Support campaigns ≥10⁶ tokens per model |
| **NFR-2** | Overhead vs direct llama.cpp ≤20% latency |
| **NFR-3** | Horizontal scale via worker nodes/containers |
| **NFR-4** | Support 10+ models, 20+ concurrent campaigns |
| **NFR-5** | Worker failure -> retryable, not campaign termination |
| **NFR-6** | Config/results survive orchestrator restarts |
| **NFR-7** | No external network calls during campaigns |
| **NFR-8** | Data at rest encrypted where required |
| **NFR-9** | Run on Linux (Nvidia) and macOS (Apple Silicon) |
| **NFR-10** | Standard Python tooling (type hints, tests, CI) |

---

## 5. Architecture

### 5.1 Logical Components

```
┌─────────────────────────────────────────────────────────────┐
│ CONTROL PLANE                                               │
│  - API Server                                               │
│  - Scheduler                                                │
│  - Model Registry                                           │
├─────────────────────────────────────────────────────────────┤
│ EXECUTION PLANE                                             │
│  - Worker processes running LangGraph graphs                │
│  - Embedded llama.cpp runtimes                              │
├─────────────────────────────────────────────────────────────┤
│ DATA PLANE                                                  │
│  - Database (configs, metadata)                             │
│  - Log storage (NDJSON artifacts)                           │
│  - Report artifacts                                         │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Deployment Topologies

**Linux/Nvidia:**
- Bare metal -> Docker -> TSLIT + llama.cpp (CUDA)
- Bare metal -> Hypervisor -> VM (GPU passthrough) -> Docker -> TSLIT

**macOS/Apple Silicon:**
- Native macOS -> llama.cpp (Metal) -> TSLIT
- Docker with Metal exposed (experimental)

---

## 6. Threat Model

### 6.1 Assets

- Model registry metadata
- Campaign configurations
- Virtual clock state and execution logs
- Local llama.cpp GGUF artifacts
- Host/container runtime integrity
- Evaluation outputs and reports

### 6.2 Trust Boundaries

- Operator workstation ↔ evaluation host/VM
- TSLIT process ↔ llama.cpp runtime
- Container/VM ↔ host
- File system: app data ↔ shared artifacts
- User-supplied configs ↔ code

### 6.3 Data Flows

```
Operator -> configs -> TSLIT CLI -> orchestrator -> LangGraph flows
                                      ↓
                              llama.cpp bindings
                                      ↓
                              artifact storage (NDJSON)
                                      ↓
                              downstream analysis
```

### 6.4 Threat Matrix

| ID | Component | Threat | STRIDE | Mitigation | Risk |
|----|-----------|--------|--------|------------|------|
| 0001 | Model Registry | Tampering with metadata | Tampering | Sign registry, enforce checksums | High |
| 0002 | Config Parser | YAML injection -> code exec | Tampering | Use `yaml.safe_load`, validate schema | High |
| 0003 | Orchestrator | Spoofed operator | Spoofing | OS-level authN, audit logs | Medium |
| 0004 | llama.cpp runtime | Library hijack | Tampering | Pin wheel hashes, verify checksums | High |
| 0005 | Model Store | Path hijack -> wrong GGUF | Spoofing | Require checksums, read-only dirs | Medium |
| 0006 | Artifact Storage | Log exposure | Info Disclosure | Encrypt at rest, restrict access | High |
| 0007 | Virtual Clock | Env manipulation bypass | Tampering | Validate time params at runtime | Medium |
| 0008 | Anomaly Detectors | Weak detection rules | Repudiation | Test suites, version detector rules | Medium |
| 0009 | Docker/VM | Container escape via GPU | Elevation | Minimal privileges, toolkit safeguards | High |
| 0010 | Backend Credentials | Secrets exposure | Info Disclosure | Secrets manager, avoid CLI args | High |

### 6.5 Assumptions

- llama.cpp builds sourced from trusted releases
- Configs stored on local disk (signing more important if Git-synced)
- Multi-tenant hosts increase threat likelihood
- Campaign execution may be air-gapped or use remote adapters

---

## 7. Detection Strategy

### 7.1 What We're Looking For

Non-smooth, trigger-like behavioral changes tied to:
- **Synthetic time**: Sudden onset of expiry messages, refusals, degradation
- **Usage thresholds**: Changes after N tokens/interactions
- **Affiliation context**: Differential treatment by requester nation-state
- **Geopolitical keywords**: Censorship of Taiwan, Tiananmen, etc.

### 7.2 Detection Methods

| Method | Description |
|--------|-------------|
| **EVALs** | Before/after specific synthetic dates |
| **A/B comparison** | Baseline vs time-shifted with identical prompts |
| **Anomaly detection** | Phrase frequency spikes ("expired", "license") |
| **Statistical tests** | Chi-square for refusal rates, t-test for response lengths |
| **LLM-based analysis** | Multi-agent review with QA validation |

### 7.3 Success Criteria

The system is successful if it can:
- Reproduce baseline behavior when synthetic time is held constant
- Systematically sweep time and usage space
- Provide clear evidence of no time-dependent triggers OR
- Surface repeatable, time-linked anomalies for security/legal review

---

## 8. Experiment Design

### 8.1 Unified Experiment (Experiment 4 Enhanced)

Combines:
- **Affiliation bias testing** (US/NATO vs Chinese government)
- **Time-based logic bombs** (symbolic dates: 9/11, July 4, Tiananmen)
- **Coder-specific threats** (license, crypto, ML security, telemetry)

### 8.2 Test Matrix

- **32 scenarios** across affiliation and coder categories
- **15 probe dates** (symbolic, baseline, future, edge cases)
- **8 horizon steps** per scenario
- **~3,840 total interactions**

### 8.3 Probe Dates

| Category | Dates |
|----------|-------|
| Anti-US triggers | 9/11, July 4, Pearl Harbor |
| Anti-Chinese triggers | National Day (Oct 1), Tiananmen (June 4) |
| Other nation-states | Russian Victory Day, Iranian Revolution, Israeli Independence |
| Neutral baselines | Jan 15, Mar 20 |
| Future probes | 2026, 2030, 2035 |
| Edge cases | Leap year (Feb 29), pre-invalid date |

---

## 9. Data Requirements

| ID | Requirement |
|----|-------------|
| DR-1 | Campaign metadata: id, description, origin filters, models, backends, time strategy |
| DR-2 | Interaction logs: real time, virtual time, prompt, response, model/backend, tokens, latency |
| DR-3 | Anomaly records: type, severity, associated samples |
| DR-4 | Configurable retention (90 days raw logs, 1 year summaries) |

---

## 10. Operational Requirements

| ID | Requirement |
|----|-------------|
| OP-1 | Deployment manifests for single-node Docker and VM-based cluster |
| OP-2 | Runbooks for adding new FP16 models, migrating between Nvidia/Mac |
| OP-3 | Troubleshooting for GPU/Metal builds, VRAM issues, campaign failures |

---

## References

- [LangChain Documentation](https://python.langchain.com/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [llama.cpp](https://github.com/ggerganov/llama.cpp)
- [Qwen](https://github.com/QwenLM/Qwen)
- [DeepSeek](https://github.com/deepseek-ai)
