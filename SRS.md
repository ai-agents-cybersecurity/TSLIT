Got it — so “Chinese” = country of origin of the model vendor (Qwen, DeepSeek, Kimi, Yi, etc.), not “Chinese‑language‑only.” I’ll rewrite the SRS with that assumption baked in and keep the FP16 / Ollama / Nvidia + Mac Studio bits.

Here’s the amended SRS v0.2 you can drop in as‑is.

⸻

Software Requirements Specification (SRS)

Project: Time‑Shift LLM Integrity Tester (TSLIT)
Version: 0.2 (Amended for Chinese‑origin models)
Owner: <Your org>

⸻

1. Introduction

1.1 Purpose

This SRS defines the requirements for the Time‑Shift LLM Integrity Tester (TSLIT), a system that:
	•	Runs controlled time‑shifted evaluations of local LLMs,
	•	Detects time‑based latent behaviors (expiry, logic bombs, license killswitches),
	•	Targets Chinese‑origin open‑weight model families served locally via Ollama in FP16 (non‑quantized) form where available, including but not limited to:
	•	Qwen (Alibaba Cloud),  ￼
	•	DeepSeek (DeepSeek‑R1, DeepSeek‑V3, DeepSeek‑Coder),  ￼
	•	Kimi/Kimi K2 (Moonshot AI),  ￼
	•	Yi (01.AI).  ￼
	•	Uses LangChain and LangGraph as the orchestration framework over RPC/HTTP to Ollama.  ￼

The SRS explicitly specifies requirements beyond OSI Layer 7, including host, virtualization, containers, and nested containers.

1.2 Scope

TSLIT is a black‑box integrity and safety evaluation tool. It does not retrain or modify models; instead it:
	•	Connects to one or more Ollama instances (Linux or macOS) that serve Chinese‑origin models such as qwen3:8b-fp16, qwen:7b-fp16, deepseek-r1, deepseek-coder, kimi-k2, kimi-k2-thinking, yi, etc.  ￼
	•	Executes time‑shifted workloads using LangChain/LangGraph to simulate long‑term use and future dates.
	•	Logs and analyzes outputs to detect:
	•	Hard‑coded expiry behavior,
	•	Sudden censorship or license gates at specific times,
	•	Other time/usage‑conditional “logic bombs.”

No constraint is placed on language; these models are Chinese‑origin vendors, but often multilingual in practice.

1.3 Definitions
	•	Chinese‑origin LLM – LLM where the primary vendor/company is based in China (e.g., Alibaba’s Qwen, 01.AI’s Yi, DeepSeek, Moonshot AI’s Kimi).  ￼
	•	TSLIT – Time‑Shift LLM Integrity Tester.
	•	EVALs – Evaluation suites for grading model outputs (benchmarks, custom tests).
	•	LangChain / LangGraph – Python frameworks for building agentic, graph‑based workflows and stateful LLM agents.  ￼
	•	Ollama – Local model runtime exposing HTTP APIs, supporting GPU on Linux and Metal on macOS.  ￼

1.4 References
	•	LangChain docs & API reference.  ￼
	•	LangGraph overview & reference.  ￼
	•	Ollama GPU & install documentation.  ￼
	•	Qwen (Alibaba Cloud).  ￼
	•	DeepSeek (company, R1, coder).  ￼
	•	Moonshot AI / Kimi K2.  ￼
	•	01.AI / Yi.  ￼

⸻

2. Overall Description

2.1 Product Perspective

TSLIT is a client/orchestrator layer on top of Ollama:
	•	It does not implement custom kernels or inference engines.
	•	It forwards requests via HTTP/RPC to Ollama instances running Chinese‑origin LLMs.
	•	It uses LangChain and LangGraph to define long‑running graphs of interactions and synthetic‑time scenarios.

2.2 Product Functions (High Level)
	•	Register and manage Chinese‑origin model profiles (Qwen/DeepSeek/Kimi/Yi/etc.) and their Ollama tags.
	•	Verify and target FP16 (non‑quantized) weights where available (e.g., qwen3:8b-fp16, qwen2.5-coder:7b-instruct-fp16, yi:34b-fp16).  ￼
	•	Configure and run time‑shifted evaluation campaigns with:
	•	Synthetic date/time injection,
	•	Usage‑based “virtual time” (token/interaction counters),
	•	Boundary dates and stress scenarios.
	•	Aggregate outputs, apply EVALs, and detect time‑linked anomalies.
	•	Generate machine‑readable metrics and human‑readable reports.

2.3 User Classes
	•	Security / Red‑team engineers.
	•	LLM Ops / MLOps engineers.
	•	Compliance / Legal.
	•	Research engineers and developers.

All users are technical; CLI/API is the primary interface.

2.4 Operating Environment
	•	Nvidia / Linux path:
	•	Host: Linux (bare metal or hypervisor host).
	•	Guest: Linux VM with GPU passthrough.
	•	Ollama installed on host or in container with access to /dev/nvidia*.  ￼
	•	Apple Silicon (Mac Studio M2 Ultra, 192 GB RAM):
	•	macOS 14+ with native Ollama using Metal acceleration.  ￼
	•	TSLIT may run natively or in Docker; when in Docker, GPU acceleration is only guaranteed if Ollama itself runs natively on the host and exposes HTTP.  ￼

2.5 Design & Implementation Constraints
	•	Model origin constraint:
The primary supported model families are Chinese‑origin (Qwen, DeepSeek, Kimi, Yi, and optionally GLM, Baichuan, etc.).  ￼
	•	Precision constraint:
Where possible, FP16 (non‑quantized) weights must be used; quantized weights are out of scope except for small smoke tests.
	•	Runtime constraint:
TSLIT relies on Ollama’s API and GPU/Metal handling; it does not manage drivers, Metal, or CUDA directly.  ￼
	•	Network constraint:
Evaluation environments may be air‑gapped; TSLIT must not depend on external cloud LLMs.

2.6 Assumptions
	•	Operators can install and configure Ollama, GPU drivers, and virtualization.
	•	Target hardware (e.g., M2 Ultra with 192 GB or Nvidia GPUs with sufficient VRAM) can hold selected FP16 models in memory.  ￼
	•	Any time‑based “logic bombs” are observable through output behavior under synthetic time shifts.

⸻

3. System Features (Functional Requirements)

3.1 Chinese‑Origin Model Registry

FR‑1
TSLIT shall maintain a model registry with, at minimum:
	•	model_id (Ollama tag, e.g., qwen3:8b-fp16, deepseek-r1:8b, kimi-k2-thinking, yi:34b),  ￼
	•	origin_vendor (e.g., Alibaba/Qwen, DeepSeek, Moonshot AI, 01.AI),  ￼
	•	Parameter count and approximate FP16 VRAM footprint,
	•	License type / openness (open‑weight vs proprietary),
	•	Flags: fp16_available, quantized_only.

FR‑2
TSLIT shall validate that the configured Ollama backend actually exposes FP16 weights (for example, qwen3:32b-fp16 indicating F16 quantization) and warn if only quantized (e.g., Q4_0) is available.  ￼

FR‑3
The registry shall support tagging models as “Chinese‑origin” vs “other” so that campaigns can be filtered to only those satisfying your origin requirement.

FR‑4
TSLIT shall support multiple backends (e.g., nvidia-vm-1, mac-studio-1) with mappings: model → backend(s).

⸻

3.2 Time‑Shift Sandbox Manager

FR‑5
TSLIT shall maintain a virtual clock independent of real wall time.

FR‑6
Per campaign, users shall configure:
	•	Start date/time (t0),
	•	Step type: linear, jump, or mixed,
	•	Step size (e.g. +1 day, +1 month, +1 year),
	•	Specific “probe dates” (e.g., 2030‑01‑01, 2049‑10‑01, etc.).

FR‑7
TSLIT shall inject synthetic time via:
	•	System messages (“Today is 2032‑05‑01”),
	•	Timestamped context entries (“Log entry for 2040‑01‑01 09:30 UTC”),
	•	Optional environment variables if your own wrappers read them.

FR‑8
The system shall be able to replay identical workloads under different virtual_clock values and track (model_id, backend, virtual_time) with each interaction.

FR‑9
TSLIT shall support usage‑based time (e.g., incrementing a “day counter” every N tokens or interactions) to probe for usage‑gated behavior.

⸻

3.3 LangChain / LangGraph Orchestrator

FR‑10
TSLIT shall implement campaigns as LangGraph graphs using LangChain LLM and tool primitives.  ￼

FR‑11
Graphs shall support:
	•	Branching (e.g., if suspicious phrase detected → deeper probing),
	•	Loops (multi‑day synthetic conversations),
	•	Parallel execution (multiple time slices or models in parallel).

FR‑12
EVALs shall be pluggable:
	•	Standard benchmarks (accuracy, reasoning scores),
	•	Custom anomaly rules (regex, heuristics),
	•	ML‑based classifiers for expiry/kill‑switch patterns.

FR‑13
A campaign config (YAML/JSON) shall define:
	•	Target model(s) and backend(s),
	•	Time strategy (dates, step size, horizon),
	•	Scenarios to execute,
	•	Metrics/EVALs to compute,
	•	Storage and reporting options.

FR‑14
TSLIT shall leverage LangGraph’s statefulness to checkpoint and resume long‑running campaigns if a worker fails.  ￼

⸻

3.4 Scenario & Workload Generator

FR‑15
TSLIT shall provide a library of canonical workloads:
	•	General Q&A,
	•	Long‑running “assistant” style dialog,
	•	Coding tasks (especially for DeepSeek Coder, Qwen Coder, etc.),  ￼
	•	Summarization / analysis tasks.

FR‑16
Users shall be able to define custom scenarios through:
	•	A Python API (scenario objects),
	•	Or a simple DSL in config files.

FR‑17
The workload generator shall simulate long‑term usage:
	•	Configure interactions per synthetic day,
	•	Total synthetic duration (e.g., 5 years),
	•	Token budget per campaign (e.g., ≥ 10⁶ tokens).

⸻

3.5 Aggregation, Anomaly Detection & Reporting

FR‑18
All interactions shall be logged with:
	•	Real timestamp,
	•	virtual_time,
	•	Model/backend identifiers,
	•	Prompt, response,
	•	Token counts, latency.

FR‑19
TSLIT shall compute metrics per (model, backend, virtual_time):
	•	Refusal rate,
	•	Error/exception rate,
	•	Frequency of key phrases (e.g., “expired”, “license”, “upgrade”, “China law compliance”),
	•	EVAL scores.

FR‑20
Anomaly detection shall support:
	•	Baseline vs time‑shift comparison,
	•	Continuous metric trend analysis,
	•	Hard thresholds and statistical outlier detection.

FR‑21
Reports (HTML/Markdown/PDF) shall summarize:
	•	Campaign configuration,
	•	High‑level findings per model,
	•	Detailed examples where anomalies triggered.

FR‑22
TSLIT shall export JSON artifacts for downstream tooling (dashboards, SIEM, etc.).

⸻

3.6 Security & Governance

FR‑23
TSLIT shall implement RBAC:
	•	Admin (infra + registry),
	•	Operator (run campaigns),
	•	Viewer (read‑only reports).

FR‑24
All API/UI access shall be authenticated (e.g., OIDC/SAML integration).

FR‑25
TSLIT shall support model‑origin policies, enabling:
	•	Restricting campaigns to “Chinese‑origin only,”
	•	Tagging/segregating logs per origin/vendor for regulatory reasons.

FR‑26
Logs and outputs shall be encrypted at rest and protected in transit (TLS).

⸻

3.7 Administration & Ops

FR‑27
TSLIT shall provide:
	•	Health endpoints for orchestrator/workers,
	•	Configuration via environment variables and config files.

FR‑28
An audit log shall record:
	•	Model registry changes,
	•	Campaign launches and modifications,
	•	Who accessed which reports.

⸻

4. External Interface Requirements

4.1 User Interfaces

FR‑29
A CLI shall support:
	•	Model registry management,
	•	Campaign creation, status, and retrieval,
	•	Log and report export.

FR‑30
A REST API shall expose equivalent capabilities for automation.

(Any GUI dashboard is optional and can be added later.)

4.2 Hardware Interfaces

FR‑31
For Nvidia systems, Ollama must see GPUs with compute capability ≥ 5.0, as recommended for LLMs, and sufficient VRAM for FP16 models (e.g., ~16 GB for 8B FP16, ~64 GB for 30–32B FP16).  ￼

FR‑32
On Mac Studio M2 Ultra, Ollama shall rely on Metal and unified memory; TSLIT itself should not attempt to access GPU devices directly.  ￼

4.3 Software Interfaces

FR‑33
TSLIT shall interact with Ollama through its HTTP API on configurable host/port (default localhost:11434).  ￼

FR‑34
TSLIT shall store structured data in:
	•	A relational DB (e.g., PostgreSQL) for configs and campaign metadata,
	•	File/object storage for logs and reports.

FR‑35
TSLIT shall expose Prometheus/OpenTelemetry endpoints for metrics/traces (optional but recommended).

⸻

5. Architecture & Layering (Including > L7)

5.1 Logical Components
	•	Control Plane:
	•	API server,
	•	Scheduler,
	•	Model registry.
	•	Execution Plane:
	•	Worker processes/containers running LangGraph graphs,
	•	Connections to Ollama backends.
	•	Data Plane:
	•	DB,
	•	Log storage,
	•	Report artifacts.

5.2 OSI & Meta‑Layers

TSLIT requirements span:
	•	L1–L2: Optional dedicated NICs or VLANs for backend isolation.
	•	L3: Distinct subnets for:
	•	Control plane,
	•	Backend model nodes.
	•	L4: TCP, fixed ports for TSLIT API and Ollama.
	•	L5–L6: TLS, certificate management, optional mutual TLS to backends.
	•	L7: REST APIs and HTTP/JSON contracts.

Beyond L7:
	•	L8 – Identity & Access: SSO/IdP, RBAC, access‑logging.
	•	L9 – Governance: Policies for model origin, data retention, and regulatory tagging (e.g., Chinese‑origin vs non‑Chinese).
	•	L10 – Operational Safety: Runbooks, patching procedures, GPU/driver update guides.

5.3 Virtualization & Container Topologies

5.3.1 Nvidia/Linux
Supported topologies:
	•	A. Simple:
	•	Bare metal Linux → Docker → (Ollama container + TSLIT container).
	•	B. VM:
	•	Bare metal → Hypervisor → Linux VM (GPU passthrough) → Docker → Ollama + TSLIT.  ￼
	•	C. DIND Isolation:
	•	Bare metal → Hypervisor → Linux VM → Docker → TSLIT Orchestrator container → Docker‑in‑Docker worker containers connecting to Ollama.

Requirements:
	•	GPU devices exposed via Nvidia Container Toolkit where needed.  ￼
	•	DIND workers reuse the GPU exposure of the outer daemon; no additional nested GPU virtualization is required.

5.3.2 Mac Studio (M2 Ultra)
Preferred topology:
	•	D. Native GPU path:
	•	macOS host → Ollama installed natively (Metal) → TSLIT running:
	•	Natively, or
	•	In Docker, connecting to http://host.docker.internal:11434.

Docker‑only Ollama on macOS must be documented as CPU‑only; GPU acceleration is achieved via native host Ollama.  ￼

⸻

6. Non‑Functional Requirements

6.1 Performance
	•	NFR‑1: TSLIT shall support campaigns generating ≥ 10⁶ tokens per model without manual intervention, assuming appropriate hardware.
	•	NFR‑2: Overhead vs direct Ollama client should not exceed ~20% latency at similar concurrency (to be measured in your environment).

6.2 Scalability
	•	NFR‑3: Horizontal scale by:
	•	Adding worker nodes/containers,
	•	Adding Ollama backends (GPU or Mac hosts).
	•	NFR‑4: Support at least 10 models and 20 concurrent campaigns for a single deployment (subject to hardware).

6.3 Reliability
	•	NFR‑5: Worker failure should not terminate the campaign; failed segments must be retryable.
	•	NFR‑6: Config and results must survive orchestrator restarts.

6.4 Security
	•	NFR‑7: No external network calls to commercial LLM APIs from TSLIT workers during campaigns.
	•	NFR‑8: Data at rest (logs, prompts, responses) must be encrypted where required by policy.

6.5 Portability & Maintainability
	•	NFR‑9: Codebase should run on:
	•	Linux (Nvidia GPUs),
	•	macOS (Apple Silicon, with or without Docker),
with minimal environment‑specific code.
	•	NFR‑10: Use standard Python tooling (type hints, tests, CI) to keep maintenance cost low.

⸻

7. Data Requirements
	•	DR‑1: Campaign metadata: id, description, origin filters (e.g., “Chinese‑origin only”), models, backends, time strategy.
	•	DR‑2: Interaction logs: real time, virtual time, prompt, response, model/backend, tokens, latency.
	•	DR‑3: Anomaly records: type, severity, associated samples.
	•	DR‑4: Configurable retention (e.g. 90 days for raw logs, 1 year for summaries).

⸻

8. Operational & Support Requirements
	•	OP‑1: Provide deployment manifests/scripts for:
	•	Single‑node Docker,
	•	VM‑based cluster.
	•	OP‑2: Provide runbooks for:
	•	Adding a new Chinese‑origin FP16 model in Ollama,
	•	Migrating campaigns between Nvidia and Mac Studio.
	•	OP‑3: Provide troubleshooting guidance for:
	•	Ollama not seeing GPU/Metal,
	•	FP16 models exceeding available VRAM/unified memory,
	•	Campaign failures and resume flow.

⸻
