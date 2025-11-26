# LLM Analyzer Workflow Visualization

## Complete Analysis Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         LLM ANALYZER COMPLETE WORKFLOW                       │
└─────────────────────────────────────────────────────────────────────────────┘


STEP 1: PREREQUISITES CHECK
════════════════════════════
┌──────────────────┐
│ run_llm_analyzer │
│     .sh          │
└────────┬─────────┘
         │
         ├─→ Check Ollama running? ────→ ❌ Exit with error
         │                          └─→ ✅ Continue
         │
         ├─→ Check gpt-oss:120b? ──────→ ❌ Warning, user confirm
         │                          └─→ ✅ Continue
         │
         └─→ Check NDJSON files? ───────→ ❌ Exit with error
                                    └─→ ✅ Continue


STEP 2: DATA LOADING & PREPARATION
═══════════════════════════════════
┌─────────────────────────────────────────┐
│ load_model_data()                       │
├─────────────────────────────────────────┤
│ • Read artifacts/*.ndjson               │
│ • Parse each line as JSON               │
│ • Build model_data dict                 │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│ compute_model_metrics() [per model]    │
├─────────────────────────────────────────┤
│ • Categorize records:                   │
│   - US/NATO/Five Eyes                   │
│   - Chinese government                  │
│   - Neutral baseline                    │
│                                         │
│ • Calculate metrics:                    │
│   - Refusal rates (%)                   │
│   - Average response lengths            │
│   - Detector flag counts                │
│                                         │
│ • Compute deltas:                       │
│   - US vs CN refusal delta              │
│   - US vs CN length delta               │
│   - US vs Neutral deltas                │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│ prepare_analysis_context()              │
├─────────────────────────────────────────┤
│ • Format metrics for LLM                │
│ • Include sample responses              │
│ • Structure cross-model comparison      │
│ • Add scenario examples                 │
└─────────────────┬───────────────────────┘
                  │
                  ▼


STEP 3: MULTI-AGENT REFLECTION LOOP
════════════════════════════════════

┌───────────────────────────────────────────────────────────────┐
│ StateGraph Execution                                          │
└───────────────────────────────────────────────────────────────┘

Iteration = 0
│
▼
┌──────────────────────────────────────────────────────────┐
│ ANALYST AGENT                                            │
│ ════════════════════════════════════════════════════     │
│                                                          │
│ Input: Structured metrics + sample responses            │
│                                                          │
│ LLM Call:                                                │
│ ┌──────────────────────────────────────────────────┐    │
│ │ System: "You are a cybersecurity expert..."      │    │
│ │                                                   │    │
│ │ User: "[Detailed metrics and samples]"           │    │
│ │                                                   │    │
│ │ Model: gpt-oss:120b @ temp=0.3                   │    │
│ └──────────────────────────────────────────────────┘    │
│                                                          │
│ Output (JSON):                                           │
│ {                                                        │
│   "summary": "Analysis identified 2 CRITICAL threats...",│
│   "threats": [                                           │
│     {                                                    │
│       "type": "affiliation_bias",                        │
│       "severity": "CRITICAL",                            │
│       "model": "deephat-v1-7b",                          │
│       "description": "Model refuses US requests...",     │
│       "evidence": [                                      │
│         "US refusal: 45.2%, CN refusal: 0.0%",          │
│         "Response quality degradation: 75%"              │
│       ],                                                 │
│       "confidence": 0.92                                 │
│     },                                                   │
│     {...}                                                │
│   ],                                                     │
│   "recommendations": [...],                              │
│   "confidence_score": 0.85                               │
│ }                                                        │
│                                                          │
│ State Updated:                                           │
│ • analyst_report = full text                            │
│ • analyst_findings = parsed JSON                        │
│ • analyst_confidence = 0.85                             │
└──────────────────┬───────────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────────┐
│ QA MANAGER AGENT                                         │
│ ════════════════════════════════════════════════════     │
│                                                          │
│ Input: Original data + Analyst findings                 │
│                                                          │
│ LLM Call:                                                │
│ ┌──────────────────────────────────────────────────┐    │
│ │ System: "You are a senior QA manager..."         │    │
│ │                                                   │    │
│ │ User: "[Original data + Analyst report]"         │    │
│ │                                                   │    │
│ │ Model: gpt-oss:120b @ temp=0.2 (more critical)   │    │
│ └──────────────────────────────────────────────────┘    │
│                                                          │
│ Output (JSON):                                           │
│ {                                                        │
│   "review_summary": "Analysis is well-supported...",     │
│   "validated_threats": [                                 │
│     {                                                    │
│       "original_threat": {...threat from analyst...},    │
│       "validation": "CONFIRMED",                         │
│       "reasoning": "Large sample (n=15), significant...",│
│       "adjusted_severity": "CRITICAL",                   │
│       "adjusted_confidence": 0.90                        │
│     },                                                   │
│     {                                                    │
│       "original_threat": {...},                          │
│       "validation": "QUESTIONABLE",                      │
│       "reasoning": "Sample size too small (n=3)..."      │
│     }                                                    │
│   ],                                                     │
│   "critical_issues": [                                   │
│     "Backdoor finding needs larger sample"               │
│   ],                                                     │
│   "overall_confidence": 0.82,                            │
│   "recommendation": "REVISE"  ← Decision point          │
│ }                                                        │
│                                                          │
│ State Updated:                                           │
│ • qa_review = full text                                 │
│ • qa_validated_findings = parsed JSON                   │
│ • qa_confidence = 0.82                                  │
│ • qa_issues = ["Backdoor finding needs..."]            │
└──────────────────┬───────────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────────┐
│ DECISION GATE: should_continue()                        │
│ ════════════════════════════════════════════════════     │
│                                                          │
│ Check 1: iteration >= max_iterations?                   │
│   → YES: goto finalize                                  │
│   → NO: continue to Check 2                             │
│                                                          │
│ Check 2: recommendation == "ACCEPT" and confidence ≥0.8?│
│   → YES: goto finalize                                  │
│   → NO: continue to Check 3                             │
│                                                          │
│ Check 3: recommendation == "REJECT"?                    │
│   → YES: goto finalize (low quality)                   │
│   → NO: goto increment (loop again)                     │
│                                                          │
│ Decision: "continue" or "finalize"                      │
└──────────────────┬───────────────────────────────────────┘
                   │
                   ├─→ "finalize" ─────────┐
                   │                        │
                   └─→ "continue"           │
                          ▼                 │
                   ┌────────────────┐       │
                   │ INCREMENT      │       │
                   │ ITERATION      │       │
                   │                │       │
                   │ iteration += 1 │       │
                   └────────┬───────┘       │
                            │               │
                            │ Loop back     │
                            │ to Analyst    │
                            ▼               │
                      [Analyst Agent]       │
                            │               │
                            │               │
                            └───────────────┤
                                            │
                                            ▼


STEP 4: FINALIZATION
════════════════════
┌──────────────────────────────────────────────────────────┐
│ finalize_report()                                        │
│ ════════════════════════════════════════════════════     │
│                                                          │
│ Aggregate Data:                                          │
│ • Best findings across iterations                       │
│ • Highest confidence analysis                           │
│ • All QA validation results                             │
│                                                          │
│ Generate Sections:                                       │
│ ┌────────────────────────────────────────────────────┐  │
│ │ 1. Executive Summary                                │  │
│ │    - Overall findings                               │  │
│ │    - Threat count                                   │  │
│ │    - Key recommendations                            │  │
│ └────────────────────────────────────────────────────┘  │
│                                                          │
│ ┌────────────────────────────────────────────────────┐  │
│ │ 2. QA Validation                                    │  │
│ │    - Overall confidence: X.X%                       │  │
│ │    - Validation summary                             │  │
│ │    - Recommendation: ACCEPT/REVISE/REJECT           │  │
│ └────────────────────────────────────────────────────┘  │
│                                                          │
│ ┌────────────────────────────────────────────────────┐  │
│ │ 3. Validated Threats (CONFIRMED only)               │  │
│ │    [THREAT 1] Affiliation Bias                      │  │
│ │    Severity: CRITICAL                               │  │
│ │    Model: deephat-v1-7b                             │  │
│ │    Confidence: 90.0%                                │  │
│ │    Description: [...]                               │  │
│ │    Evidence: [...]                                  │  │
│ │    Validation: [...]                                │  │
│ │                                                     │  │
│ │    [THREAT 2] ...                                   │  │
│ └────────────────────────────────────────────────────┘  │
│                                                          │
│ ┌────────────────────────────────────────────────────┐  │
│ │ 4. Questionable Findings                            │  │
│ │    Items that need further investigation            │  │
│ └────────────────────────────────────────────────────┘  │
│                                                          │
│ ┌────────────────────────────────────────────────────┐  │
│ │ 5. Recommendations                                  │  │
│ │    1. DO NOT DEPLOY model-x in context Y           │  │
│ │    2. Conduct expanded testing on...                │  │
│ │    3. Review training data provenance...            │  │
│ └────────────────────────────────────────────────────┘  │
│                                                          │
│ ┌────────────────────────────────────────────────────┐  │
│ │ 6. Critical Issues (from QA)                        │  │
│ │    Issues identified during validation              │  │
│ └────────────────────────────────────────────────────┘  │
│                                                          │
│ ┌────────────────────────────────────────────────────┐  │
│ │ 7. Detailed Reports                                 │  │
│ │    - Full analyst report                            │  │
│ │    - Full QA review                                 │  │
│ └────────────────────────────────────────────────────┘  │
│                                                          │
│ State Updated:                                           │
│ • final_report = complete text report                   │
│ • total_threats_found = count of CONFIRMED              │
│ • analysis_complete = True                              │
└──────────────────┬───────────────────────────────────────┘
                   │
                   ▼


STEP 5: OUTPUT GENERATION
══════════════════════════
┌──────────────────────────────────────────────────────────┐
│ Write Reports                                            │
│ ════════════════════════════════════════════════════     │
│                                                          │
│ Text Report:                                             │
│ ┌────────────────────────────────────────────────────┐  │
│ │ llm_analysis_report.txt                             │  │
│ │                                                     │  │
│ │ Human-readable comprehensive report                 │  │
│ │ • Executive summary                                 │  │
│ │ • All validated threats                             │  │
│ │ • Evidence and reasoning                            │  │
│ │ • Recommendations                                   │  │
│ │ • Full analysis details                             │  │
│ └────────────────────────────────────────────────────┘  │
│                                                          │
│ JSON Report:                                             │
│ ┌────────────────────────────────────────────────────┐  │
│ │ llm_analysis_report.json                            │  │
│ │                                                     │  │
│ │ Structured data for programmatic access             │  │
│ │ {                                                   │  │
│ │   "timestamp": "...",                               │  │
│ │   "model_names": [...],                             │  │
│ │   "iterations": 2,                                  │  │
│ │   "total_threats_found": 3,                         │  │
│ │   "analyst_findings": {...},                        │  │
│ │   "qa_validated_findings": {...},                   │  │
│ │   "analyst_confidence": 0.85,                       │  │
│ │   "qa_confidence": 0.82                             │  │
│ │ }                                                   │  │
│ └────────────────────────────────────────────────────┘  │
└──────────────────┬───────────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────────┐
│ Console Summary                                          │
│ ════════════════════════════════════════════════════     │
│                                                          │
│ ========================================                 │
│ ANALYSIS SUMMARY                                         │
│ ========================================                 │
│ Models Analyzed: 4                                       │
│ Reflection Iterations: 2                                 │
│ Confirmed Threats: 3                                     │
│ Final QA Confidence: 82.0%                               │
│                                                          │
│ Full report: llm_analysis_report.txt                     │
│ JSON findings: llm_analysis_report.json                  │
│ ========================================                 │
└──────────────────────────────────────────────────────────┘


COMPLETE! ✅
```

## Iteration Example: REVISE → ACCEPT

```
═══════════════════════════════════════════════════════════════════════
ITERATION 1
═══════════════════════════════════════════════════════════════════════

Analyst: "Found 4 threats: 2 CRITICAL, 1 HIGH, 1 MEDIUM"
         Confidence: 0.75

QA:      "Threat #3 (HIGH) has weak evidence - only n=3 samples"
         "Threat #4 (MEDIUM) could be explained by prompt sensitivity"
         Recommendation: REVISE
         Confidence: 0.60

Decision: CONTINUE (confidence < 0.8, recommendation = REVISE)

───────────────────────────────────────────────────────────────────────

ITERATION 2 (with QA feedback in mind)
═══════════════════════════════════════════════════════════════════════

Analyst: "Re-analyzed with focus on sample sizes and alternative explanations"
         "Found 2 threats: 2 CRITICAL (both with n>10)"
         "Dropped weak findings from previous iteration"
         Confidence: 0.88

QA:      "Threat #1: CONFIRMED - strong evidence, large sample"
         "Threat #2: CONFIRMED - significant delta, consistent pattern"
         "Improved analysis quality - focused on robust findings"
         Recommendation: ACCEPT
         Confidence: 0.85

Decision: FINALIZE (confidence ≥ 0.8, recommendation = ACCEPT)

═══════════════════════════════════════════════════════════════════════
FINAL REPORT: 2 CONFIRMED threats, high confidence
═══════════════════════════════════════════════════════════════════════
```

## State Evolution Through Pipeline

```
Initial State:
{
  "model_data": {...loaded from NDJSON...},
  "iteration": 0,
  "max_iterations": 2,
  "analyst_report": None,
  "qa_review": None,
  ...
}

After Analyst (Iteration 1):
{
  ...previous state...,
  "analyst_report": "Full text analysis...",
  "analyst_findings": {threats: [4 threats], confidence: 0.75},
  "analyst_confidence": 0.75
}

After QA (Iteration 1):
{
  ...previous state...,
  "qa_review": "Full review text...",
  "qa_validated_findings": {validated_threats: [...], recommendation: "REVISE"},
  "qa_confidence": 0.60,
  "qa_issues": ["Weak evidence for threat #3"]
}

After Increment:
{
  ...previous state...,
  "iteration": 1  ← Incremented
}

After Analyst (Iteration 2):
{
  ...previous state...,
  "analyst_report": "Revised analysis...",  ← Updated
  "analyst_findings": {threats: [2 threats], confidence: 0.88},  ← Updated
  "analyst_confidence": 0.88  ← Updated
}

After QA (Iteration 2):
{
  ...previous state...,
  "qa_review": "Improved quality...",  ← Updated
  "qa_validated_findings": {validated_threats: [...], recommendation: "ACCEPT"},
  "qa_confidence": 0.85,  ← Updated
  "qa_issues": []  ← Updated
}

After Finalize:
{
  ...previous state...,
  "final_report": "Complete formatted report...",
  "total_threats_found": 2,
  "analysis_complete": True
}
```

## Key Decision Points

### 1. Continue vs Finalize
```
if iteration >= max_iterations:
    → finalize (hit limit)
elif recommendation == "ACCEPT" and qa_confidence >= 0.8:
    → finalize (high quality)
elif recommendation == "REJECT":
    → finalize (low quality, stop wasting resources)
else:
    → continue (needs improvement)
```

### 2. Threat Validation
```
Analyst proposes → QA validates → Report includes

THREAT → CONFIRMED   → ✅ In "Validated Threats" section
THREAT → QUESTIONABLE → ⚠️  In "Questionable Findings" section
THREAT → REJECTED    → ❌ Excluded from report
```

### 3. Confidence Calibration
```
Analyst Confidence: How certain is the analyst?
QA Confidence: How much does QA trust the analyst?
Adjusted Confidence: QA's revised confidence per threat

Final Confidence = QA Confidence (higher standard)
```

## Runtime Characteristics

```
Operation                  | Time      | Notes
───────────────────────────┼───────────┼─────────────────────
Load data                  | <1 sec    | Fast NDJSON parsing
Compute metrics            | <1 sec    | Simple calculations
Prepare context            | <1 sec    | String formatting
Analyst LLM call           | 2-4 min   | Depends on model
QA LLM call                | 2-3 min   | Slightly faster
Iteration decision         | <1 ms     | Simple logic
Finalize report            | <1 sec    | Text generation
Write files                | <1 sec    | Disk I/O

Total (2 iterations):      | ~10 min   | Normal case
Total (1 iteration):       | ~5 min    | Quick accept
Total (4 iterations):      | ~20 min   | Extra rigor
```

## Error Recovery

```
Error Type              | Recovery Strategy
────────────────────────┼──────────────────────────────────────
Ollama not running      | Pre-flight check, clear error, exit
Model not found         | Warning, user confirmation to proceed
Missing NDJSON          | Pre-flight check, clear error, exit
JSON parse failure      | Fallback to raw text, reduced confidence
LLM timeout             | Retry with exponential backoff
Low quality output      | QA rejects, stop iterating gracefully
```

This completes the workflow visualization!
