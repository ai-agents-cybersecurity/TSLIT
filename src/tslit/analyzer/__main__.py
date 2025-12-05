#!/usr/bin/env python3
# Copyright 2025 Nic Cravino. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
# https://github.com/ai-agents-cybersecurity/TSLIT

"""
CLI entry point for the LLM Analyzer.

Usage:
    python -m tslit.analyzer [OPTIONS]
    
Environment Variables:
    LLM_ANALYZER_MODEL_PATH: Path to GGUF model 
    LLM_ANALYZER_N_CTX: Context window size 
    LLM_ANALYZER_N_GPU_LAYERS: GPU layers, -1 for all (default: -1)
    LLM_ANALYZER_MAX_TOKENS: Max output tokens 
"""

import argparse
import logging
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for LLM Analyzer."""
    parser = argparse.ArgumentParser(
        description="LLM-powered analysis of adversarial affiliation test results"
    )
    parser.add_argument(
        "--artifacts-dir",
        type=str,
        default="artifacts",
        help="Directory containing model NDJSON files"
    )
    parser.add_argument(
        "--model-names",
        type=str,
        nargs="+",
        default=["qwen2.5-coder-7b-instruct-fp16"],
        help="Model names to analyze"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="llm_analysis_report.txt",
        help="Output report file path"
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=20,
        help="Maximum reflection loop iterations"
    )
    
    args = parser.parse_args()
    
    artifacts_dir = Path(args.artifacts_dir)
    if not artifacts_dir.exists():
        logger.error(f"Artifacts directory not found: {artifacts_dir}")
        sys.exit(1)
    
    logger.info("=" * 80)
    logger.info("LLM-POWERED THREAT ANALYZER")
    logger.info("=" * 80)
    logger.info(f"Artifacts: {artifacts_dir}")
    logger.info(f"Models: {args.model_names}")
    logger.info(f"Max iterations: {args.max_iterations}")
    logger.info("=" * 80)
    
    from tslit.analyzer.core import run_analysis
    
    try:
        final_state = run_analysis(
            artifacts_dir=artifacts_dir,
            model_names=args.model_names,
            output_path=Path(args.output),
            max_iterations=args.max_iterations
        )
        
        print("\n" + "=" * 80)
        print("ANALYSIS COMPLETE")
        print("=" * 80)
        print(f"Iterations: {final_state['iteration']}")
        print(f"Confirmed Threats: {final_state['total_threats_found']}")
        print(f"QA Confidence: {final_state.get('qa_confidence', 0.0):.1%}")
        print(f"\nReport: {args.output}")
        print("=" * 80)
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
