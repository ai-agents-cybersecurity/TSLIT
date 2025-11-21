Time-Shift LLM Integrity Tester (TSLIT) Threat Model

ASSETS
- Model registry metadata: Chinese-origin model identifiers, backend mappings, precision flags.
- Campaign configurations: time-shift scenarios, synthetic time parameters, anomaly detector selections.
- Virtual clock state and execution logs: per-run timelines, prompts, and generated responses (including NDJSON artifacts).
- Local llama.cpp GGUF artifacts, Metal/CUDA builds, and any optional remote adapter credentials.
- Host and container runtime integrity: GPU passthrough, virtualization settings, environment variables used for synthetic time.
- Evaluation outputs and reports: metrics, anomaly flags, and summaries derived from runs.

TRUST BOUNDARIES
- Operator workstation vs. evaluation host/VM: CLI invocations and config editing may occur locally while campaigns run on a separate host.
- TSLIT process vs. llama.cpp runtime: inference occurs via shared libraries; compromised builds can alter execution even without network hops.
- Container/VM boundary vs. host: when TSLIT runs in Docker or a guest VM, host device access (/dev/nvidia*, Metal) is exposed across isolation layers.
- File system boundary between TSLIT app data and shared artifacts: NDJSON logs and reports may be written to shared volumes accessible by other processes.
- User-supplied configs vs. code: YAML/JSON campaign files and registry entries are external inputs parsed by the orchestrator.

DATA FLOWS
- Operator edits registry/config files -> TSLIT CLI loads YAML/JSON -> orchestrator builds LangGraph flows (crosses user-to-app boundary).
- TSLIT orchestrator -> llama.cpp Python bindings issue inference calls -> responses returned in-process (crosses app-to-native-runtime boundary).
- Orchestrator -> artifact storage writes NDJSON logs and reports -> downstream analysis tools may read them (crosses app-to-shared-storage boundary).
- Virtual clock values -> injected into prompts/system messages -> sent to backend -> outputs logged (stays within orchestrator-to-backend flow).
- Model paths/build flags -> supplied via environment variables or config -> used to initialize llama.cpp (crosses config-to-runtime boundary).

THREAT MODEL
| THREAT ID | COMPONENT NAME | THREAT NAME | STRIDE CATEGORY | WHY APPLICABLE | HOW MITIGATED | MITIGATION | LIKELIHOOD EXPLANATION | IMPACT EXPLANATION | RISK SEVERITY |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0001 | Model Registry | Tampering with model metadata to redirect evaluations to non-target models | Tampering | Registry entries drive campaign target selection; altering model_id/backends could mask issues or exfiltrate to attacker-controlled endpoints. | No explicit integrity controls in design; configs are plain files. | Sign registry files and enforce checksum verification; restrict write permissions; validate model origin and backend hostnames at load time. | Moderate: configs are editable text and may be shared; insider or malware could modify. | High: campaigns would produce misleading results or leak data to untrusted hosts. | High |
| 0002 | Campaign Config Parser | YAML injection leading to arbitrary code execution | Tampering | Campaigns use YAML/JSON; unsafe loaders could execute tags or references. | Not specified; assumes standard parsing. | Use safe YAML loaders (e.g., yaml.safe_load); validate schema; avoid Python object deserialization. | Moderate: depends on parser choice and whether untrusted configs are imported. | High: code execution compromises host and secrets. | High |
| 0003 | Orchestrator | Spoofed operator triggering campaigns with altered parameters | Spoofing | CLI access controls not described; a local attacker could run campaigns under another user's identity. | None specified beyond OS permissions. | Enforce OS-level authN (sudo/su) and audit logs; consider role-based CLI wrapper; lock down terminals on shared hosts. | Moderate: threat on shared/remote hosts without strict user controls. | Medium: misuse affects resources and data integrity but limited if no remote network exposure. | Medium |
| 0004 | Orchestrator ↔ llama.cpp runtime | Library hijack altering prompts or responses | Tampering | The orchestrator dynamically loads llama-cpp-python; a malicious shared library or patched binary can intercept generation calls. | No code-signing or checksum validation defined. | Pin wheel hashes, verify checksums of GGUF and llama.cpp builds, restrict write access to site-packages. | Moderate: attackers with filesystem access can swap binaries; insider risk exists. | High: manipulated outputs invalidate findings or leak data. | High |
| 0005 | Model Artifact Store | Path hijack loading attacker-controlled GGUF | Spoofing | Campaign configs point to local GGUF files; replacing symlinks or paths loads arbitrary models. | No runtime validation that file contents match expected vendor. | Require checksums/signatures for GGUF artifacts; store under read-only directories; validate provenance before campaigns. | Moderate: shared lab environments make file tampering feasible. | Medium: wrong model undermines origin guarantees and could exfiltrate prompts. | Medium |
| 0006 | Artifact Storage | Exposure of NDJSON logs containing prompts and model outputs | Information Disclosure | Logs include sensitive scenarios and responses; stored on shared volumes. | No encryption-at-rest or access control described. | Store artifacts in restricted directories; encrypt at rest; scrub secrets from prompts; apply retention policies. | High: artifacts are intentionally generated and may be widely shared for analysis. | High: leaks reveal proprietary prompts, evaluation strategy, or sensitive content. | High |
| 0007 | Virtual Clock Injection | Bypass of time-shift controls via environment manipulation | Tampering | Synthetic time may rely on env vars/system messages; attacker could override values to hide time-based behaviors. | Not covered; relies on campaign settings. | Validate time parameters at runtime; sign scenario definitions; protect environment variables from untrusted users. | Low: requires local access to modify env or configs. | Medium: undermines purpose by preventing detection of time-triggered logic bombs. | Medium |
| 0008 | Anomaly Detectors | Overly permissive regex/heuristics failing to flag malicious behavior | Repudiation | Weak detectors could allow vendors to repudiate issues; lack of logging for missed anomalies. | No defined detection quality controls. | Implement test suites for detectors; version and sign detector rules; log detector decisions with justifications. | Moderate: detection quality can drift without governance. | Medium: missed logic bombs reduce trust in results. | Medium |
| 0009 | Runtime Environment (Docker/VM) | Escape from container/VM to host via GPU passthrough misconfiguration | Elevation of Privilege | GPU/Metal access requires privileged device exposure; misconfigurations could allow host access. | Not specified beyond noting passthrough requirements. | Use minimal privileges; leverage NVIDIA Container Toolkit safeguards; avoid sharing host sockets; apply hypervisor isolation and firmware updates. | Low: requires sophisticated exploit plus privileged config. | High: host compromise reveals all data and credentials. | High |
| 0010 | Backend Credentials | Secrets in environment variables or CLI arguments exposed via process listing | Information Disclosure | Operators may pass tokens via env/CLI; other users on host could read them. | Not addressed. | Use secrets managers or protected config files; avoid CLI args for secrets; restrict /proc access; rotate credentials. | Moderate: common operational pattern; shared hosts increase risk. | High: leaked tokens permit API misuse and data theft. | High |

QUESTIONS & ASSUMPTIONS
- Assume llama.cpp builds are sourced from trusted releases; if remote adapters are added, require TLS/mTLS or keep them loopback-only.
- Assume configs are stored on local disk; if synced via Git or shared drives, signing/CI checks become more important.
- Clarify whether multi-tenant users share the same evaluation host; threat likelihoods rise with shared access.
- Determine if artifacts ever include proprietary customer data; if so, apply stronger confidentiality controls.
- Confirm whether campaign execution is fully offline (air-gapped) or relies on remote adapters; this affects tampering likelihood.
- No mitigations listed where threats are judged low-likelihood with high operational burden (e.g., full HSM-backed key storage for local-only tokens).
