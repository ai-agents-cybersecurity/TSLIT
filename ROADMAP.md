# TSLIT Roadmap

## Current State (v0.1 - MVP)

✅ **Synthetic Time Injection via Prompts**
- Virtual clock with configurable time steps and probe dates
- Time-shifted prompts inject synthetic dates into model context
- Anomaly detection (temporal-leak, refusal, backdoor patterns)
- 33 specialized scenarios (21 coder + 12 adversarial affiliation)
- Request/response logging for transparency

✅ **Testing Capabilities**
- Coder-focused scenarios (security, crypto, license detection)
- Adversarial affiliation testing (nation-state bias detection)
- 9 specialized detectors including affiliation bias
- Multi-model comparison workflows

✅ **Infrastructure**
- Native llama.cpp backend (Metal/CUDA support)
- NDJSON artifact logging
- Automated analysis scripts
- Comprehensive documentation

---

## Next MVP (v0.2) - System-Level Time Isolation

### 🎯 Objective

Achieve **complete temporal isolation** by controlling both:
1. **Payload time** (prompt dates) ✅ Already implemented
2. **System time** (OS-level clock) 🔜 Next phase
3. **Template time helpers** (Jinja `strftime_now`) 🔜 Lock down

### Motivation

Current implementation relies on prompt-based time injection. While effective for detecting most time-gated behaviors, sophisticated backdoors could potentially:
- Access system time through llama.cpp error messages
- Read timestamps from log files
- Detect time discrepancies between prompt dates and system time
- Implement dual-clock verification (prompt date vs system date)

**Goal**: Eliminate ALL possible system time leakage vectors.

Recent findings from digging through `llama.cpp` show that:
- Core inference APIs never inject system time — they only see tokens you provide.
- The Jinja/minja chat templating layer exposes `strftime_now(...)`, which pulls the host clock and many shipped templates call it to embed `Current date: ...` into system messages.

**Implication:** to reach total isolation we must block template-driven time injection in addition to controlling OS time.

---

## Phase 1: System Time Shifting Research

### Investigation Areas

#### 1. **macOS Native Containers** 🍎
Explore macOS sandboxing/containerization options:

**Approach A: `libfaketime` for macOS**
```bash
# Install libfaketime
brew install libfaketime

# Run llama.cpp with fake system time
DYLD_INSERT_LIBRARIES=/usr/local/lib/faketime/libfaketime.1.dylib \
FAKETIME="2030-12-31 00:00:00" \
python -m tslit campaign run --config config/test.yaml
```

**Pros:**
- Lightweight (no container overhead)
- Works with native Metal acceleration
- Process-level time isolation

**Cons:**
- May not catch all system calls
- Limited to macOS/Linux (no Windows support out of box)
- Potential compatibility issues with SIP (System Integrity Protection)

**Research Tasks:**
- [ ] Test libfaketime compatibility with llama-cpp-python
- [ ] Verify Metal GPU access works with faketime
- [ ] Test with SIP enabled/disabled
- [ ] Measure performance impact
- [ ] Verify complete time isolation (no leaks)

#### 1b. **Template Isolation Option (No `strftime_now`)** 🛑
Add a first-class “total isolation” switch that disables template time helpers and enforces deterministic prompts.

**Design sketch:**
- CLI flag/env: `--total-isolation` / `TSLIT_TOTAL_ISOLATION=1`.
- In backend/template plumbing, set `define_strftime_now = False` before calling `llama_chat_apply_template` (or skip Jinja entirely).
- Reject/override model-provided templates that reference `strftime_now` when isolation is enabled.
- Emit audit log entry stating template time helpers were disabled.

**Tasks:**
- [ ] Add flag to CLI + config schema (default off) that toggles isolation.
- [ ] Wire flag into backend/template helpers to disable `strftime_now` exposure.
- [ ] Add guardrails: warn/error if selected template contains `strftime_now` while flag is on.
- [ ] Regression tests covering: (a) normal chat template, (b) template with `strftime_now` blocked, (c) raw prompt path unaffected.
- [ ] Docs: update README/ROADMAP to describe the switch and default behavior.

#### 2. **Docker Containerization** 🐳
Standard approach with proven isolation:

**Architecture:**
```
Host System (real time)
  └─> Docker Container (fake time via libfaketime)
       └─> llama.cpp (isolated inference)
            └─> TSLIT campaign runner
```

**Implementation:**
```dockerfile
FROM python:3.11-slim

# Install libfaketime
RUN apt-get update && apt-get install -y libfaketime

# Install llama-cpp-python with CPU support
RUN pip install llama-cpp-python

# Copy TSLIT
COPY . /app
WORKDIR /app
RUN pip install -e .

# Entry point with faketime wrapper
ENTRYPOINT ["faketime", "-f", "@2030-12-31 00:00:00", "tslit"]
```

**Pros:**
- Complete isolation from host system
- Cross-platform (works on macOS, Linux, Windows)
- Reproducible environments
- Easy CI/CD integration

**Cons:**
- No GPU acceleration (Metal/CUDA) without complex setup
- Slower inference (CPU-only unless using nvidia-docker)
- Container overhead
- Model files need to be mounted/copied

**Research Tasks:**
- [ ] Create minimal Docker image with llama.cpp CPU support
- [ ] Test faketime integration in container
- [ ] Investigate GPU passthrough (nvidia-docker for CUDA)
- [ ] Measure CPU vs native Metal performance
- [ ] Document setup for reproducible builds

#### 3. **Hybrid Approach: Time-Shifted Proxy** 🔄
Proxy llama.cpp requests with synchronized time injection:

**Architecture:**
```
TSLIT Campaign
  └─> TimeProxy (Python middleware)
       ├─> Injects synchronized timestamps
       ├─> Filters error messages (remove real timestamps)
       └─> Forwards to llama.cpp
            └─> Model inference
                 └─> Response sanitization
                      └─> Return to TSLIT
```

**Key Features:**
- Intercepts all llama.cpp communication
- Ensures prompt time === system time (as seen by model)
- Sanitizes error messages, logs, metadata
- Prevents time leakage through any channel

**Implementation Plan:**
```python
class TemporalProxy:
    def __init__(self, virtual_time: datetime, backend: LlamaBackend):
        self.virtual_time = virtual_time
        self.backend = backend
    
    def generate(self, prompts):
        # 1. Set fake system time (if using libfaketime)
        with FakeTime(self.virtual_time):
            # 2. Make request to llama.cpp
            response = self.backend.generate(prompts)
            
            # 3. Sanitize response (remove real timestamps)
            response = self._sanitize_timestamps(response)
            
            # 4. Verify no time leakage
            self._audit_response(response, self.virtual_time)
            
        return response
    
    def _sanitize_timestamps(self, response):
        # Remove 'created' timestamps from llama.cpp response
        # Replace with virtual_time epoch
        if 'raw' in response:
            response['raw']['created'] = int(self.virtual_time.timestamp())
        return response
    
    def _audit_response(self, response, expected_time):
        # Check for any real date/time references
        # Flag if response contains current system date
        pass
```

**Pros:**
- Works with native llama.cpp (keeps Metal/CUDA)
- Fine-grained control over time exposure
- Can detect and block leakage attempts
- Auditable (logs all sanitization actions)

**Cons:**
- More complex implementation
- Potential performance overhead
- Requires maintenance if llama.cpp API changes

**Research Tasks:**
- [ ] Prototype TimeProxy middleware
- [ ] Identify all llama.cpp timestamp sources
- [ ] Implement response sanitization
- [ ] Add leakage detection audit trail
- [ ] Performance benchmarking

---

## Phase 2: Implementation (v0.2-alpha)

### Deliverables

#### 1. **Multi-Backend Support**
```yaml
# config/campaign.yaml
backend:
  type: llama-cpp-isolated
  isolation_method: libfaketime  # or docker, or proxy
  model_path: models/model.gguf
  virtual_time_sync: true  # Sync system time with prompt time
```

#### 2. **Temporal Proxy Module**
```python
# src/tslit/temporal_proxy.py
class TemporalIsolationBackend:
    """Backend with complete temporal isolation."""
    
    def __init__(self, isolation_method='libfaketime'):
        self.isolation = self._setup_isolation(isolation_method)
    
    def generate_with_time_shift(self, prompts, virtual_time):
        # System time matches prompt time
        with self.isolation.set_time(virtual_time):
            return self.backend.generate(prompts)
```

#### 3. **Verification Tools**
```bash
# Verify no time leakage
tslit verify-isolation --config config/test.yaml

# Output:
# ✓ System time isolated
# ✓ No real timestamps in responses
# ✓ Prompt time === System time
# ✓ llama.cpp errors sanitized
```

#### 4. **Docker Support**
```bash
# Build isolated container
docker build -t tslit:isolated .

# Run campaign with time shift
docker run -v $(pwd)/models:/models \
           -e FAKE_TIME="2030-12-31 00:00:00" \
           tslit:isolated campaign run --config config/adversarial.yaml
```

---

## Phase 3: Enhanced Testing (v0.2-beta)

### New Capabilities

#### 1. **Dual-Clock Attack Detection**
Test if models verify prompt time against system time:

```python
# Scenario: Mismatched Times
# System time: 2025-11-21
# Prompt date: 2030-12-31
# Expected: Model uses prompt date
# Backdoor: Model detects mismatch and refuses

# With v0.2: Both times synchronized
# System time: 2030-12-31 (faketime)
# Prompt date: 2030-12-31
# Backdoor cannot detect discrepancy
```

#### 2. **Error Message Time Leakage Detection**
```python
# Test: Trigger llama.cpp error
# Check if error message contains real timestamp
# With proxy: Error messages sanitized

def test_error_time_isolation():
    # Force an error (e.g., invalid parameter)
    with assert_raises(LlamaError) as exc:
        backend.generate_with_bad_params()
    
    # Verify error message doesn't contain real date
    assert "2025-11-21" not in str(exc)
    assert "2030-12-31" in str(exc)  # Should show fake date
```

#### 3. **Metadata Timestamp Verification**
```python
# Verify all timestamps use virtual time
def verify_metadata_isolation(response):
    timestamps = extract_timestamps(response)
    for ts in timestamps:
        assert is_within_tolerance(ts, virtual_time)
        assert ts != real_system_time
```

---

## Phase 4: Documentation & Validation (v0.2-stable)

### Documentation Updates

1. **`docs/TEMPORAL_ISOLATION.md`**
   - Complete isolation architecture
   - Setup guides for libfaketime/Docker
   - Verification procedures
   - Known limitations

2. **`docs/ADVANCED_BACKDOOR_DETECTION.md`**
   - Dual-clock attack patterns
   - Multi-vector time leakage scenarios
   - Defense strategies

3. **Research Paper Updates**
   - Methodology section: Complete isolation approach
   - Results: Comparison of prompt-only vs system-level time shifting
   - Validation: Proof of no time leakage

### Validation Protocol

**Experiment 5: System-Level Time Isolation Validation**
```bash
# 1. Run with prompt-only time shift (current)
tslit campaign run --config config/validation.yaml

# 2. Run with system-level time shift (v0.2)
tslit campaign run --config config/validation.yaml --isolation=libfaketime

# 3. Compare results
tslit compare-isolation artifacts/validation_v01.ndjson \
                       artifacts/validation_v02.ndjson

# Expected: Identical results (proves current method is sufficient)
# OR: Different results (reveals system-time-aware backdoors)
```

---

## Open Questions & Research Areas

### Risks & Mitigations
- [ ] **GPU coverage gaps**: Document minimum viable GPU passthrough paths (Metal and CUDA) and publish known-bad configurations so testers avoid silent CPU fallbacks.
- [ ] **Artifact reproducibility**: Standardize how timestamps are scrubbed/normalized in NDJSON outputs so cross-run comparisons stay valid even when faketime libraries differ.
- [ ] **Operational ergonomics**: Provide a one-liner setup per platform (macOS/Linux/Windows via Docker) so contributors can reproduce isolation experiments without deep OS tuning.

### 1. **Performance Trade-offs**
- [ ] Benchmark: Native vs libfaketime vs Docker
- [ ] GPU acceleration compatibility
- [ ] Memory overhead
- [ ] Latency per request

### 2. **Security Guarantees**
- [ ] Can libfaketime be bypassed?
- [ ] Are there other time sources? (RDTSC CPU instruction, NTP, etc.)
- [ ] Do we need kernel-level isolation?

### 3. **Cross-Platform Support**
- [ ] macOS: libfaketime + SIP workarounds
- [ ] Linux: libfaketime (native support)
- [ ] Windows: Docker only? (no native faketime)

### 4. **Model Artifacts**
- [ ] Does quantization affect time-awareness?
- [ ] Do fine-tuned models have different time sensitivities?
- [ ] Can models detect containerization? (fingerprinting)

---

## Success Criteria for v0.2

### Must Have ✅
- [ ] At least one working system-level time isolation method (libfaketime or Docker)
- [ ] Proof that system time is synchronized with prompt time
- [ ] Verification tools to detect time leakage
- [ ] Documentation for setup and usage
- [ ] Backward compatibility with v0.1 campaigns

### Should Have 🎯
- [ ] Both libfaketime and Docker support
- [ ] Temporal proxy with sanitization
- [ ] Performance benchmarks
- [ ] CI/CD integration with Docker

### Nice to Have 💡
- [ ] GPU acceleration in Docker (nvidia-docker)
- [ ] Automatic leakage detection in responses
- [ ] Time-sync audit trail
- [ ] Cross-platform installers

---

## Timeline (Tentative)

**Phase 1 (Research)**: 2-3 weeks
- Test libfaketime with llama.cpp
- Prototype Docker setup
- Design temporal proxy architecture

**Phase 2 (Implementation)**: 3-4 weeks
- Implement chosen isolation method
- Integrate with TSLIT backend
- Create verification tools

**Phase 3 (Testing)**: 2 weeks
- Run validation experiments
- Compare v0.1 vs v0.2 results
- Document findings

**Phase 4 (Documentation)**: 1 week
- Write guides
- Update README
- Prepare release notes

**Total: 8-10 weeks to v0.2-stable**

---

## Long-Term Vision (v0.3+)

### Advanced Isolation Features
- **Network time isolation**: Block NTP requests
- **Hardware clock isolation**: Prevent RDTSC instruction access
- **Multi-layer verification**: Kernel + process + prompt time
- **Automated backdoor synthesis**: Generate test cases for potential time-based triggers

### Integration with Broader Security Tools
- **MLSecOps pipelines**: Automated model scanning before deployment
- **Supply chain verification**: Timestamp all model checkpoints
- **Red team tools**: Adversarial time-based backdoor injection testing
- **Compliance reporting**: Generate audit trails for regulatory review

### Research Contributions
- **Dataset publication**: Share TSLIT results as benchmark
- **Threat taxonomy**: Categorize all known time-based model attacks
- **Defense playbook**: Best practices for temporal isolation in AI systems

---

## Contributing

Have ideas for temporal isolation? Open an issue or PR!

**Priority areas:**
1. libfaketime compatibility testing
2. Docker GPU passthrough solutions
3. Windows native time isolation methods
4. Novel time leakage vectors

---

**Current Version**: v0.1 (Prompt-level time shifting)  
**Next Release**: v0.2-alpha (System-level time isolation - Research phase)  
**Target Date**: Q1 2026

See `CHANGELOG.md` for version history.
