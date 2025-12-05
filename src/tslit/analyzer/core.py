# Copyright 2025 Nic Cravino. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
# https://github.com/ai-agents-cybersecurity/TSLIT

"""
Core analysis functionality for LLM-powered model comparison.

This module provides data loading, metrics computation, and context preparation
for the multi-agent analysis pipeline.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, TypedDict

logger = logging.getLogger(__name__)


class AnalysisState(TypedDict):
    """State passed between agents in the analysis pipeline."""
    model_data: Dict[str, List[Dict[str, Any]]]
    model_names: List[str]
    analyst_report: Optional[str]
    analyst_findings: Optional[Dict[str, Any]]
    analyst_confidence: Optional[float]
    qa_review: Optional[str]
    qa_validated_findings: Optional[Dict[str, Any]]
    qa_confidence: Optional[float]
    qa_issues: Optional[List[str]]
    iteration: int
    max_iterations: int
    final_report: Optional[str]
    total_threats_found: int
    analysis_complete: bool


@dataclass
class ModelComparison:
    """Comparison metrics between models."""
    model_name: str
    total_interactions: int
    us_refusal_rate: float
    cn_refusal_rate: float
    neutral_refusal_rate: float
    us_avg_length: float
    cn_avg_length: float
    neutral_avg_length: float
    affiliation_bias_flags: int
    backdoor_flags: int
    raw_deltas: Dict[str, Any] = field(default_factory=dict)


def _first_user_message(messages: List[Dict[str, Any]]) -> str:
    """Return the first user-authored message content if present."""
    for message in messages:
        if message.get("role") == "user":
            return str(message.get("content", ""))
    return str(messages[0].get("content", "")) if messages else ""


def _extract_prompt_from_record(record: Dict[str, Any]) -> str:
    """Extract prompt from a record's prompts field."""
    prompts = record.get("prompts", [])
    return _first_user_message(prompts) if prompts else ""


def _extract_prompt_from_request(request_entry: Dict[str, Any]) -> str:
    """Extract prompt from a request entry."""
    request_block = request_entry.get("request", {}) if request_entry else {}
    messages = request_block.get("messages", []) if isinstance(request_block, dict) else []
    return _first_user_message(messages)


def load_model_data(artifacts_dir: Path, model_names: List[str]) -> Dict[str, List[Dict[str, Any]]]:
    """Load NDJSON data for all models, including request prompts for context.
    
    Auto-discovers NDJSON files in the artifacts directory, excluding *_requests.ndjson files.
    """
    data = {}
    
    # Auto-discover NDJSON files (exclude _requests files)
    ndjson_files = [
        f for f in artifacts_dir.glob("*.ndjson")
        if not f.name.endswith("_requests.ndjson")
    ]
    
    if not ndjson_files:
        logger.warning(f"No NDJSON files found in {artifacts_dir}")
        return data
    
    # Use the first (or most recent) file found
    filepath = sorted(ndjson_files, key=lambda f: f.stat().st_mtime, reverse=True)[0]
    requests_filepath = artifacts_dir / f"{filepath.stem}_requests.ndjson"
    
    logger.info(f"Loading data from: {filepath}")
    
    # Use first model name as key, or derive from filename
    model_key = model_names[0] if model_names else filepath.stem
    
    # Load responses
    records = []
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse line in {filepath}: {e}")
    
    # Load requests if available and merge with responses
    if requests_filepath.exists():
        logger.info(f"Loading request prompts from {requests_filepath}")
        requests: List[Dict[str, Any]] = []
        with open(requests_filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                try:
                    requests.append(json.loads(line))
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse line in {requests_filepath}: {e}")

        # Prefer completed requests (post-response)
        completed_requests = [
            req for req in requests
            if (req.get("metadata") or {}).get("phase") != "pre-request"
            and req.get("response", {}).get("status") != "pending"
        ]
        if completed_requests:
            requests = completed_requests

        # Merge requests with responses
        if len(requests) == len(records):
            for i, record in enumerate(records):
                prompt_text = _extract_prompt_from_request(requests[i])
                record['request_prompt'] = prompt_text
                record['request_full'] = requests[i]
            logger.info(f"Merged {len(requests)} request prompts with responses")
        else:
            logger.warning(
                f"Request count ({len(requests)}) != response count ({len(records)})"
            )
    else:
        logger.info(f"No requests file found at {requests_filepath}")

    # Ensure every record has a prompt
    for record in records:
        if not record.get('request_prompt'):
            record['request_prompt'] = _extract_prompt_from_record(record)

    data[model_key] = records
    logger.info(f"Loaded {len(records)} records for {model_key}")
    
    return data


def compute_model_metrics(records: List[Dict[str, Any]]) -> ModelComparison:
    """Compute comprehensive metrics for a single model."""
    if not records:
        return ModelComparison(
            model_name="unknown", total_interactions=0, us_refusal_rate=0.0,
            cn_refusal_rate=0.0, neutral_refusal_rate=0.0, us_avg_length=0.0,
            cn_avg_length=0.0, neutral_avg_length=0.0, affiliation_bias_flags=0,
            backdoor_flags=0
        )
    
    us_records = [r for r in records if any(x in r.get("scenario", "") for x in ["us-", "nato-", "five-eyes"])]
    cn_records = [r for r in records if "chinese-" in r.get("scenario", "")]
    neutral_records = [r for r in records if any(x in r.get("scenario", "") for x in ["neutral-", "academic-"])]
    
    def count_refusals(recs):
        return sum(1 for r in recs if any(
            flag.get("detector") == "refusal" for flag in r.get("anomaly_flags", [])
        ))
    
    us_refusals = count_refusals(us_records)
    cn_refusals = count_refusals(cn_records)
    neutral_refusals = count_refusals(neutral_records)
    
    us_rate = (us_refusals / len(us_records) * 100) if us_records else 0.0
    cn_rate = (cn_refusals / len(cn_records) * 100) if cn_records else 0.0
    neutral_rate = (neutral_refusals / len(neutral_records) * 100) if neutral_records else 0.0
    
    def avg_length(recs):
        if not recs:
            return 0.0
        lengths = [len(r.get("response", {}).get("content", "")) for r in recs]
        return sum(lengths) / len(lengths) if lengths else 0.0
    
    us_avg = avg_length(us_records)
    cn_avg = avg_length(cn_records)
    neutral_avg = avg_length(neutral_records)
    
    affiliation_bias = sum(1 for r in records if any(
        flag.get("detector") == "affiliation-bias" for flag in r.get("anomaly_flags", [])
    ))
    backdoor = sum(1 for r in records if any(
        flag.get("detector") == "backdoor" for flag in r.get("anomaly_flags", [])
    ))
    
    backend = records[0].get("backend", "unknown")
    model_name = backend if isinstance(backend, str) else backend.get("model_path", "unknown") if isinstance(backend, dict) else "unknown"
    if "/" in model_name:
        model_name = model_name.split("/")[-1]
    
    return ModelComparison(
        model_name=model_name, total_interactions=len(records), us_refusal_rate=us_rate,
        cn_refusal_rate=cn_rate, neutral_refusal_rate=neutral_rate, us_avg_length=us_avg,
        cn_avg_length=cn_avg, neutral_avg_length=neutral_avg, affiliation_bias_flags=affiliation_bias,
        backdoor_flags=backdoor, raw_deltas={
            "refusal_delta_us_cn": us_rate - cn_rate,
            "refusal_delta_us_neutral": us_rate - neutral_rate,
            "length_delta_us_cn": us_avg - cn_avg,
            "length_delta_us_neutral": us_avg - neutral_avg,
            "us_records": len(us_records), "cn_records": len(cn_records),
            "neutral_records": len(neutral_records),
        }
    )


def prepare_analysis_context(model_data: Dict[str, List[Dict[str, Any]]]) -> str:
    """Prepare structured context for LLM analysis with deep code security inspection."""
    from tslit.analyzer.security import CodeSecurityAnalyzer
    from tslit.analyzer.validator import DetectorFlagValidator
    
    security_analyzer = CodeSecurityAnalyzer()
    flag_validator = DetectorFlagValidator()
    context_parts = ["# MODEL COMPARISON DATA\n"]
    
    for model_name, records in model_data.items():
        metrics = compute_model_metrics(records)
        
        context_parts.append(f"\n## Model: {model_name}")
        context_parts.append(f"Total Interactions: {metrics.total_interactions}")
        context_parts.append(f"\n### Refusal Rates:")
        context_parts.append(f"- US/NATO/Five Eyes: {metrics.us_refusal_rate:.1f}%")
        context_parts.append(f"- Chinese Government: {metrics.cn_refusal_rate:.1f}%")
        context_parts.append(f"- Neutral Baseline: {metrics.neutral_refusal_rate:.1f}%")
        context_parts.append(f"\n### Average Response Lengths:")
        context_parts.append(f"- US/NATO/Five Eyes: {metrics.us_avg_length:.0f} chars")
        context_parts.append(f"- Chinese Government: {metrics.cn_avg_length:.0f} chars")
        context_parts.append(f"- Neutral Baseline: {metrics.neutral_avg_length:.0f} chars")
        context_parts.append(f"\n### Detector Flags:")
        context_parts.append(f"- Affiliation Bias Flags: {metrics.affiliation_bias_flags}")
        context_parts.append(f"- Backdoor Pattern Flags: {metrics.backdoor_flags}")
        context_parts.append(f"\n### Key Deltas:")
        context_parts.append(f"- Refusal Rate Delta (US vs CN): {metrics.raw_deltas['refusal_delta_us_cn']:.1f}%")
        context_parts.append(f"- Length Delta (US vs CN): {metrics.raw_deltas['length_delta_us_cn']:.0f} chars")
        
        # Deep code security analysis
        us_records = [r for r in records if any(x in r.get("scenario", "") for x in ["us-", "nato-", "five-eyes"])]
        cn_records = [r for r in records if "chinese-" in r.get("scenario", "")]
        security_comparison = security_analyzer.compare_security_profiles(us_records, cn_records)
        
        context_parts.append(f"\n### CODE SECURITY ANALYSIS:")
        context_parts.append(f"- US/NATO Total Risk Score: {security_comparison['us_total_risk']}")
        context_parts.append(f"- Chinese Total Risk Score: {security_comparison['cn_total_risk']}")
        context_parts.append(f"- Risk Delta: {security_comparison['risk_delta']:+d}")
        context_parts.append(f"- Conclusion: {security_comparison['conclusion']}")
        
        if security_comparison['us_by_type']:
            context_parts.append(f"\n**US/NATO Malicious Patterns:**")
            for pattern_type, count in security_comparison['us_by_type'].items():
                context_parts.append(f"  - {pattern_type}: {count}")
        
        if security_comparison['cn_by_type']:
            context_parts.append(f"\n**Chinese Malicious Patterns:**")
            for pattern_type, count in security_comparison['cn_by_type'].items():
                context_parts.append(f"  - {pattern_type}: {count}")
        
        # Add sample responses with security analysis
        _add_sample_responses(context_parts, records, security_analyzer, flag_validator)
        context_parts.append("\n" + "="*80 + "\n")
    
    return "\n".join(context_parts)


def _add_sample_responses(
    context_parts: List[str],
    records: List[Dict[str, Any]],
    security_analyzer: "CodeSecurityAnalyzer",
    flag_validator: "DetectorFlagValidator"
) -> None:
    """Add sample response analysis to context."""
    us_samples = [r for r in records if "us-" in r.get("scenario", "")][:3]
    cn_samples = [r for r in records if "chinese-" in r.get("scenario", "")][:3]
    
    for label, samples, comparison_samples in [
        ("US/NATO", us_samples, cn_samples),
        ("Chinese Government", cn_samples, us_samples)
    ]:
        if not samples:
            continue
            
        context_parts.append(f"\n### Sample {label} Responses:")
        for i, sample in enumerate(samples, 1):
            scenario = sample.get("scenario", "unknown")
            full_response = sample.get("response", {}).get("content", "")
            response_preview = full_response[:500]
            flags = [f.get("detector") for f in sample.get("anomaly_flags", [])]
            request_prompt = sample.get("request_prompt", "")
            prompt_preview = request_prompt[:300] if request_prompt else "[No prompt]"
            
            sec_findings = security_analyzer.analyze_code(full_response)
            flag_validations = flag_validator.validate_all_flags(
                sample, {'comparison_records': comparison_samples}
            )
            
            context_parts.append(f"\n{i}. Scenario: {scenario}")
            context_parts.append(f"   Prompt: {prompt_preview}...")
            context_parts.append(f"   Response: {response_preview}...")
            context_parts.append(f"   Detector Flags: {flags}")
            context_parts.append(f"   Risk Score: {sec_findings['risk_score']} ({sec_findings['threat_level']})")


def run_analysis(
    artifacts_dir: Path,
    model_names: List[str],
    output_path: Path,
    max_iterations: int = 2
) -> Dict[str, Any]:
    """Run the full analysis pipeline and return results."""
    from tslit.analyzer.agents import build_analysis_graph
    
    model_data = load_model_data(artifacts_dir, model_names)
    if not model_data:
        raise ValueError("No model data loaded")
    
    initial_state: AnalysisState = {
        "model_data": model_data,
        "model_names": model_names,
        "analyst_report": None,
        "analyst_findings": None,
        "analyst_confidence": None,
        "qa_review": None,
        "qa_validated_findings": None,
        "qa_confidence": None,
        "qa_issues": None,
        "iteration": 0,
        "max_iterations": max_iterations,
        "final_report": None,
        "total_threats_found": 0,
        "analysis_complete": False
    }
    
    graph = build_analysis_graph()
    # Each iteration = analyst -> qa_manager -> increment (3 nodes), so limit = max_iterations * 3 + buffer
    recursion_limit = max_iterations * 3 + 50
    final_state = graph.invoke(initial_state, config={"recursion_limit": recursion_limit})
    
    # Save reports
    output_path.write_text(final_state["final_report"], encoding="utf-8")
    
    json_output = output_path.with_suffix(".json")
    structured_output = {
        "timestamp": datetime.now().isoformat(),
        "model_names": model_names,
        "iterations": final_state["iteration"],
        "total_threats_found": final_state["total_threats_found"],
        "analyst_findings": final_state.get("analyst_findings"),
        "qa_validated_findings": final_state.get("qa_validated_findings"),
        "analyst_confidence": final_state.get("analyst_confidence"),
        "qa_confidence": final_state.get("qa_confidence"),
    }
    json_output.write_text(json.dumps(structured_output, indent=2), encoding="utf-8")
    
    return final_state
