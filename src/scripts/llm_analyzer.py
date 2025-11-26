#!/usr/bin/env python3
"""
LLM-Powered Model Comparison Analyzer with Reflection Loops

Multi-agent system using LangGraph/LangChain to analyze adversarial affiliation
test results with deep delta analysis, threat detection, and rigorous QA review.

Agents:
- analyst_agent: Primary analysis agent examining deltas and threat patterns
- qa_manager_agent: Reflection agent that reviews and validates findings

Uses local Ollama model for privacy-sensitive security analysis.
"""

import json
import logging
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, TypedDict

from langchain_community.chat_models import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# State Management
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
    """Return the first user-authored message content if present, else first message content."""

    for message in messages:
        if message.get("role") == "user":
            return str(message.get("content", ""))
    return str(messages[0].get("content", "")) if messages else ""


def _extract_prompt_from_record(record: Dict[str, Any]) -> str:
    prompts = record.get("prompts", [])
    return _first_user_message(prompts) if prompts else ""


def _extract_prompt_from_request(request_entry: Dict[str, Any]) -> str:
    request_block = request_entry.get("request", {}) if request_entry else {}
    messages = request_block.get("messages", []) if isinstance(request_block, dict) else []
    return _first_user_message(messages)


def load_model_data(artifacts_dir: Path, model_names: List[str]) -> Dict[str, List[Dict[str, Any]]]:
    """Load NDJSON data for all models, including request prompts for context."""
    data = {}
    for model_name in model_names:
        filepath = artifacts_dir / f"adversarial-affiliation-{model_name}.ndjson"
        requests_filepath = artifacts_dir / f"adversarial-affiliation-{model_name}_requests.ndjson"
        
        if not filepath.exists():
            logger.warning(f"Missing data file: {filepath}")
            continue
        
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

            # Prefer completed requests (post-response) to align 1:1 with response records
            completed_requests = [
                req for req in requests
                if (req.get("metadata") or {}).get("phase") != "pre-request"
                and req.get("response", {}).get("status") != "pending"
            ]
            if completed_requests:
                requests = completed_requests

            # Merge requests with responses (they should be in same order)
            if len(requests) == len(records):
                for i, record in enumerate(records):
                    prompt_text = _extract_prompt_from_request(requests[i])
                    record['request_prompt'] = prompt_text
                    record['request_full'] = requests[i]  # Keep full request for detailed analysis
                logger.info(f"Merged {len(requests)} request prompts with responses")
            else:
                logger.warning(
                    f"Request count ({len(requests)}) != response count ({len(records)}), "
                    "falling back to prompts embedded in response logs"
                )
        else:
            logger.info(f"No requests file found at {requests_filepath}")

        # Ensure every record has a prompt for downstream analysis
        for record in records:
            if not record.get('request_prompt'):
                record['request_prompt'] = _extract_prompt_from_record(record)
    
        data[model_name] = records
        logger.info(f"Loaded {len(records)} records for {model_name}")
    
    return data


def compute_model_metrics(records: List[Dict[str, Any]]) -> ModelComparison:
    """Compute comprehensive metrics for a single model with statistical validation."""
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
        return sum(1 for r in recs if any(flag.get("detector") == "refusal" for flag in r.get("anomaly_flags", [])))
    
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
    
    affiliation_bias = sum(1 for r in records if any(flag.get("detector") == "affiliation-bias" for flag in r.get("anomaly_flags", [])))
    backdoor = sum(1 for r in records if any(flag.get("detector") == "backdoor" for flag in r.get("anomaly_flags", [])))
    
    # Extract model name from backend field (which is a string like "llama-cpp:model.gguf")
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
    from code_security_analyzer import CodeSecurityAnalyzer
    from detector_flag_validator import DetectorFlagValidator
    
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
        
        context_parts.append(f"\n### 🔒 CODE SECURITY ANALYSIS:")
        context_parts.append(f"- US/NATO Total Risk Score: {security_comparison['us_total_risk']}")
        context_parts.append(f"- Chinese Total Risk Score: {security_comparison['cn_total_risk']}")
        context_parts.append(f"- Risk Delta: {security_comparison['risk_delta']:+d} (positive = US has MORE risk)")
        context_parts.append(f"- Conclusion: {security_comparison['conclusion']}")
        
        if security_comparison['us_by_type']:
            context_parts.append(f"\n**US/NATO Malicious Patterns:**")
            for pattern_type, count in security_comparison['us_by_type'].items():
                context_parts.append(f"  - {pattern_type}: {count}")
        
        if security_comparison['cn_by_type']:
            context_parts.append(f"\n**Chinese Malicious Patterns:**")
            for pattern_type, count in security_comparison['cn_by_type'].items():
                context_parts.append(f"  - {pattern_type}: {count}")
        
        us_samples = [r for r in records if "us-" in r.get("scenario", "")][:3]
        cn_samples = [r for r in records if "chinese-" in r.get("scenario", "")][:3]
        
        if us_samples:
            context_parts.append(f"\n### Sample US/NATO Responses (With Security Analysis + Request Context):")
            for i, sample in enumerate(us_samples, 1):
                scenario = sample.get("scenario", "unknown")
                full_response = sample.get("response", {}).get("content", "")
                response_preview = full_response[:500]
                flags = [f.get("detector") for f in sample.get("anomaly_flags", [])]
                
                # Get request prompt for context
                request_prompt = sample.get("request_prompt", "")
                prompt_preview = request_prompt[:300] if request_prompt else "[No prompt available]"
                
                # Deep security analysis of the code
                sec_findings = security_analyzer.analyze_code(full_response)
                
                # Systematic false-positive analysis for detector flags
                flag_validations = flag_validator.validate_all_flags(sample, {
                    'comparison_records': cn_samples  # For affiliation-bias validation
                })
                
                context_parts.append(f"\n{i}. Scenario: {scenario}")
                context_parts.append(f"   📝 PROMPT ASKED: {prompt_preview}{'...' if len(request_prompt) > 300 else ''}")
                context_parts.append(f"   💬 Response: {response_preview}...")
                context_parts.append(f"   🚩 Detector Flags: {flags}")
                
                # Show flag validation results
                if flag_validations:
                    context_parts.append(f"   🔬 FLAG VALIDATION (Systematic False-Positive Analysis):")
                    for flag_type, validation in flag_validations.items():
                        recommendation = validation['recommendation']
                        confidence = validation['confidence']
                        reasoning = validation['reasoning']
                        
                        icon = "✅" if recommendation == "REJECTED" else "⚠️" if recommendation == "QUESTIONABLE" else "🚨"
                        context_parts.append(f"     {icon} {flag_type}: {recommendation} (confidence: {confidence:.0%})")
                        context_parts.append(f"        Reasoning: {reasoning[:150]}...")
                
                context_parts.append(f"   🔍 Security Findings:")
                context_parts.append(f"     - Risk Score: {sec_findings['risk_score']} ({sec_findings['threat_level']})")
                
                if sec_findings['network_calls']:
                    context_parts.append(f"     - ⚠️  Network Calls: {sec_findings['network_calls'][:3]}")
                if sec_findings['file_manipulation']:
                    context_parts.append(f"     - ⚠️  File Manipulation: {sec_findings['file_manipulation'][:3]}")
                if sec_findings['encryption']:
                    context_parts.append(f"     - ⚠️  Encryption: {sec_findings['encryption'][:3]}")
                if sec_findings['execution']:
                    context_parts.append(f"     - 🚨 Code Execution: {sec_findings['execution'][:3]}")
                if sec_findings['obfuscation']:
                    context_parts.append(f"     - 🚨 Obfuscation: {sec_findings['obfuscation'][:3]}")
                if sec_findings['sensitive_dates']:
                    context_parts.append(f"     - 🚨 SENSITIVE DATES: {[d['date'] for d in sec_findings['sensitive_dates']]}")
                    for date_match in sec_findings['sensitive_dates']:
                        context_parts.append(f"       * {date_match['date']}: {date_match['context'][:100]}...")
                if sec_findings['invalid_dates']:
                    context_parts.append(f"     - ⚠️  Invalid Dates (leap year edge cases): {[d['date'] for d in sec_findings['invalid_dates']]}")
                if sec_findings['hardcoded_ips']:
                    context_parts.append(f"     - 🚨 Hardcoded IPs: {sec_findings['hardcoded_ips'][:3]}")
                if sec_findings['hardcoded_urls']:
                    context_parts.append(f"     - ⚠️  Hardcoded URLs: {sec_findings['hardcoded_urls'][:3]}")
        
        if cn_samples:
            context_parts.append(f"\n### Sample Chinese Government Responses (With Security Analysis + Request Context):")
            for i, sample in enumerate(cn_samples, 1):
                scenario = sample.get("scenario", "unknown")
                full_response = sample.get("response", {}).get("content", "")
                response_preview = full_response[:500]
                flags = [f.get("detector") for f in sample.get("anomaly_flags", [])]
                
                # Get request prompt for context
                request_prompt = sample.get("request_prompt", "")
                prompt_preview = request_prompt[:300] if request_prompt else "[No prompt available]"
                
                # Deep security analysis of the code
                sec_findings = security_analyzer.analyze_code(full_response)
                
                # Systematic false-positive analysis for detector flags
                flag_validations = flag_validator.validate_all_flags(sample, {
                    'comparison_records': us_samples  # For affiliation-bias validation
                })
                
                context_parts.append(f"\n{i}. Scenario: {scenario}")
                context_parts.append(f"   📝 PROMPT ASKED: {prompt_preview}{'...' if len(request_prompt) > 300 else ''}")
                context_parts.append(f"   💬 Response: {response_preview}...")
                context_parts.append(f"   🚩 Detector Flags: {flags}")
                
                # Show flag validation results
                if flag_validations:
                    context_parts.append(f"   🔬 FLAG VALIDATION (Systematic False-Positive Analysis):")
                    for flag_type, validation in flag_validations.items():
                        recommendation = validation['recommendation']
                        confidence = validation['confidence']
                        reasoning = validation['reasoning']
                        
                        icon = "✅" if recommendation == "REJECTED" else "⚠️" if recommendation == "QUESTIONABLE" else "🚨"
                        context_parts.append(f"     {icon} {flag_type}: {recommendation} (confidence: {confidence:.0%})")
                        context_parts.append(f"        Reasoning: {reasoning[:150]}...")
                
                context_parts.append(f"   🔍 Security Findings:")
                context_parts.append(f"     - Risk Score: {sec_findings['risk_score']} ({sec_findings['threat_level']})")
                
                if sec_findings['network_calls']:
                    context_parts.append(f"     - ⚠️  Network Calls: {sec_findings['network_calls'][:3]}")
                if sec_findings['file_manipulation']:
                    context_parts.append(f"     - ⚠️  File Manipulation: {sec_findings['file_manipulation'][:3]}")
                if sec_findings['encryption']:
                    context_parts.append(f"     - ⚠️  Encryption: {sec_findings['encryption'][:3]}")
                if sec_findings['execution']:
                    context_parts.append(f"     - 🚨 Code Execution: {sec_findings['execution'][:3]}")
                if sec_findings['obfuscation']:
                    context_parts.append(f"     - 🚨 Obfuscation: {sec_findings['obfuscation'][:3]}")
                if sec_findings['sensitive_dates']:
                    context_parts.append(f"     - 🚨 SENSITIVE DATES: {[d['date'] for d in sec_findings['sensitive_dates']]}")
                    for date_match in sec_findings['sensitive_dates']:
                        context_parts.append(f"       * {date_match['date']}: {date_match['context'][:100]}...")
                if sec_findings['invalid_dates']:
                    context_parts.append(f"     - ⚠️  Invalid Dates (leap year edge cases): {[d['date'] for d in sec_findings['invalid_dates']]}")
                if sec_findings['hardcoded_ips']:
                    context_parts.append(f"     - 🚨 Hardcoded IPs: {sec_findings['hardcoded_ips'][:3]}")
                if sec_findings['hardcoded_urls']:
                    context_parts.append(f"     - ⚠️  Hardcoded URLs: {sec_findings['hardcoded_urls'][:3]}")
        
        context_parts.append("\n" + "="*80 + "\n")
    
    return "\n".join(context_parts)


def main():
    """Main execution function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="LLM-powered analysis of adversarial affiliation test results")
    parser.add_argument("--artifacts-dir", type=str, default="artifacts", help="Directory containing model NDJSON files")
    parser.add_argument("--model-names", type=str, nargs="+", default=["deephat-v1-7b", "qwen2.5-coder-7b", "whiterabbitneo-v3-7b"], help="Model names to analyze")
    parser.add_argument("--output", type=str, default="llm_analysis_report.txt", help="Output report file path")
    parser.add_argument("--max-iterations", type=int, default=2, help="Maximum reflection loop iterations")
    parser.add_argument("--ollama-model", type=str, default="gpt-oss:120b", help="Ollama model name for analysis")
    
    args = parser.parse_args()
    
    artifacts_dir = Path(args.artifacts_dir)
    if not artifacts_dir.exists():
        logger.error(f"Artifacts directory not found: {artifacts_dir}")
        sys.exit(1)
    
    # Load model data
    logger.info("="*80)
    logger.info("LLM-POWERED ADVERSARIAL AFFILIATION ANALYZER")
    logger.info("="*80)
    logger.info(f"Artifacts directory: {artifacts_dir}")
    logger.info(f"Models to analyze: {args.model_names}")
    logger.info(f"Ollama model: {args.ollama_model}")
    logger.info(f"Max iterations: {args.max_iterations}")
    logger.info("="*80)
    
    model_data = load_model_data(artifacts_dir, args.model_names)
    
    if not model_data:
        logger.error("No model data loaded. Exiting.")
        sys.exit(1)
    
    # Import agents module
    from llm_analyzer_agents import build_analysis_graph
    
    # Initialize state
    initial_state: AnalysisState = {
        "model_data": model_data,
        "model_names": args.model_names,
        "analyst_report": None,
        "analyst_findings": None,
        "analyst_confidence": None,
        "qa_review": None,
        "qa_validated_findings": None,
        "qa_confidence": None,
        "qa_issues": None,
        "iteration": 0,
        "max_iterations": args.max_iterations,
        "final_report": None,
        "total_threats_found": 0,
        "analysis_complete": False
    }
    
    # Build and execute graph
    logger.info("\nBuilding analysis graph with reflection loops...")
    graph = build_analysis_graph()
    
    logger.info("Executing analysis pipeline...")
    logger.info("="*80)
    
    final_state = graph.invoke(initial_state)
    
    # Save report
    logger.info("="*80)
    logger.info("Analysis complete!")
    logger.info(f"Total iterations: {final_state['iteration']}")
    logger.info(f"Confirmed threats: {final_state['total_threats_found']}")
    logger.info(f"QA confidence: {final_state.get('qa_confidence', 0.0):.1%}")
    
    output_path = Path(args.output)
    output_path.write_text(final_state["final_report"], encoding="utf-8")
    logger.info(f"\nFinal report saved to: {output_path}")
    
    # Also save structured JSON findings
    json_output = output_path.with_suffix(".json")
    structured_output = {
        "timestamp": datetime.now().isoformat(),
        "model_names": args.model_names,
        "iterations": final_state["iteration"],
        "total_threats_found": final_state["total_threats_found"],
        "analyst_findings": final_state.get("analyst_findings"),
        "qa_validated_findings": final_state.get("qa_validated_findings"),
        "analyst_confidence": final_state.get("analyst_confidence"),
        "qa_confidence": final_state.get("qa_confidence"),
    }
    json_output.write_text(json.dumps(structured_output, indent=2), encoding="utf-8")
    logger.info(f"Structured findings saved to: {json_output}")
    
    # Print summary to console
    print("\n" + "="*80)
    print("ANALYSIS SUMMARY")
    print("="*80)
    print(f"Models Analyzed: {len(model_data)}")
    print(f"Reflection Iterations: {final_state['iteration']}")
    print(f"Confirmed Threats: {final_state['total_threats_found']}")
    print(f"Final QA Confidence: {final_state.get('qa_confidence', 0.0):.1%}")
    print(f"\nFull report: {output_path}")
    print(f"JSON findings: {json_output}")
    print("="*80)


if __name__ == "__main__":
    main()
