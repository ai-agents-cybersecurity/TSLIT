#!/bin/bash
# Copyright 2025 Nic Cravino. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
# https://github.com/ai-agents-cybersecurity/TSLIT
#
# TSLIT Unified Experiment Runner
# Tests for affiliation bias, time-based logic bombs, and coder-specific threats

set -e

# Configuration
MODEL_PATH="${MODEL_PATH:-models/qwen2.5-coder-7b-instruct-fp16.gguf}"
CONFIG="${CONFIG:-config/adversarial_affiliation_temporal_dataset.yaml}"
OUTPUT_DIR="${OUTPUT_DIR:-artifacts}"

echo "========================================="
echo "TSLIT Unified Experiment"
echo "========================================="
echo ""
echo "Model: $MODEL_PATH"
echo "Config: $CONFIG"
echo "Output: $OUTPUT_DIR"
echo ""
echo "Testing for:"
echo "  • Affiliation bias (US/NATO vs Chinese)"
echo "  • Time-based logic bombs (9/11, July 4, etc.)"
echo "  • Coder-specific threats"
echo ""
echo "========================================="

# Check if model exists
if [ ! -f "$MODEL_PATH" ]; then
    echo "❌ ERROR: Model not found: $MODEL_PATH"
    exit 1
fi

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Run campaign
echo ""
echo "Starting campaign..."
echo "Estimated time: 90-180 minutes"
echo ""

TSLIT_TOTAL_ISOLATION=1 tslit campaign run --config "$CONFIG"

echo ""
echo "========================================="
echo "✅ Campaign Complete!"
echo "========================================="
echo ""
echo "Results: $OUTPUT_DIR/"
echo ""
echo "Next steps:"
echo "  1. Quick analysis:"
echo "     jq '.anomaly_flags[] | .detector' $OUTPUT_DIR/*.ndjson | sort | uniq -c"
echo ""
echo "  2. Run LLM analyzer:"
echo "     python -m tslit.analyzer --artifacts-dir $OUTPUT_DIR"
echo ""
