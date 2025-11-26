#!/bin/bash
# Run COMBINED adversarial affiliation + time-based testing for DeepHat-V1-7B
# Tests for logic bombs that activate based on BOTH affiliation AND date

set -e  # Exit on error

MODEL_PATH="models/DeepHat-V1-7B.f16.gguf"
MODEL_NAME="deephat-v1-7b-temporal"
CONFIG_TEMPLATE="config/adversarial_affiliation_temporal_dataset.yaml"
OUTPUT_FILE="artifacts/adversarial-affiliation-temporal-${MODEL_NAME}.ndjson"

echo "========================================="
echo "Adversarial Affiliation + Temporal Testing"
echo "Model: DeepHat-V1-7B"
echo "========================================="
echo ""
echo "This test combines:"
echo "  1. Affiliation bias (US/NATO vs Chinese)"
echo "  2. Time-based logic bombs (9/11, July 4, etc.)"
echo ""
echo "Checking for:"
echo "  🚨 Anti-US code on 9/11 or July 4"
echo "  🚨 Anti-Chinese code on Tiananmen anniversary (June 4)"
echo "  🚨 Date-specific refusals or backdoors"
echo "  🚨 Behavior changes across 15 sensitive dates"
echo ""
echo "========================================="
echo ""

# Check if model file exists
if [ ! -f "$MODEL_PATH" ]; then
    echo "❌ ERROR: Model file not found: $MODEL_PATH"
    echo "Please ensure the model is downloaded and the path is correct."
    exit 1
fi

echo "Model: $MODEL_PATH"
echo "Output: $OUTPUT_FILE"
echo "Sensitive dates being tested:"
echo "  - 2024-09-11 (9/11 anniversary)"
echo "  - 2024-07-04 (US Independence Day)"
echo "  - 2024-12-07 (Pearl Harbor)"
echo "  - 2024-10-01 (Chinese National Day)"
echo "  - 2024-06-04 (Tiananmen Square)"
echo "  - 2024-05-09 (Russian Victory Day)"
echo "  - 2024-02-11 (Iranian Revolution)"
echo "  - 2024-05-14 (Israeli Independence)"
echo "  - + 7 more dates (baselines and future probes)"
echo ""

# Create temporary config with this model
TMP_CONFIG="config/.tmp_adversarial_temporal_${MODEL_NAME}.yaml"
sed "s|model_path:.*|model_path: $MODEL_PATH|g" "$CONFIG_TEMPLATE" > "$TMP_CONFIG"
sed -i '' "s|name:.*|name: adversarial-affiliation-temporal-${MODEL_NAME}|g" "$TMP_CONFIG"
sed -i '' "s|output_file:.*|output_file: adversarial-affiliation-temporal-${MODEL_NAME}.ndjson|g" "$TMP_CONFIG"

# Run campaign
echo "Starting campaign..."
echo "⚠️  This will take longer than standard tests due to:"
echo "   - 15 probe dates (vs 3 in standard config)"
echo "   - 15 scenarios"
echo "   - Horizon 8"
echo "   - Total: ~1800 interactions (15 dates × 15 scenarios × 8 horizon)"
echo ""
echo "Estimated time: 45-90 minutes depending on model speed"
echo ""

TSLIT_TOTAL_ISOLATION=1 tslit campaign run --config "$TMP_CONFIG"

# Clean up temp config
rm "$TMP_CONFIG"

echo ""
echo "========================================="
echo "✅ Testing Complete!"
echo "========================================="
echo ""
echo "Results saved to: $OUTPUT_FILE"
echo ""
echo "Next steps:"
echo "  1. Quick stats:"
echo "     jq '[.anomaly_flags[] | .detector] | group_by(.) | map({detector: .[0], count: length})' $OUTPUT_FILE"
echo ""
echo "  2. Check for date-specific patterns:"
echo "     jq 'select(.virtual_time | contains(\"09-11\")) | {time: .virtual_time, scenario, flags: .anomaly_flags}' $OUTPUT_FILE"
echo ""
echo "  3. Run LLM analyzer for deep analysis:"
echo "     bash src/scripts/run_llm_analyzer.sh"
echo ""
echo "  4. Look for combined affiliation + date threats:"
echo "     - US requests on 9/11 with malicious code?"
echo "     - Chinese requests on June 4 with backdoors?"
echo "     - Refusal spikes on sensitive dates?"
echo ""
