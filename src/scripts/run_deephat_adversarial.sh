#!/bin/bash
# Run adversarial affiliation testing for DeepHat-V1-7B only

set -e  # Exit on error

MODEL_PATH="models/DeepHat-V1-7B.f16.gguf"
MODEL_NAME="deephat-v1-7b"
CONFIG_TEMPLATE="config/adversarial_affiliation_dataset.yaml"
OUTPUT_FILE="artifacts/adversarial-affiliation-${MODEL_NAME}.ndjson"

echo "========================================="
echo "Adversarial Affiliation Testing"
echo "Model: DeepHat-V1-7B"
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
echo ""

# Create temporary config with this model
TMP_CONFIG="config/.tmp_adversarial_${MODEL_NAME}.yaml"
sed "s|model_path:.*|model_path: $MODEL_PATH|g" "$CONFIG_TEMPLATE" > "$TMP_CONFIG"
sed -i '' "s|name:.*|name: adversarial-affiliation-${MODEL_NAME}|g" "$TMP_CONFIG"
sed -i '' "s|output_file:.*|output_file: adversarial-affiliation-${MODEL_NAME}.ndjson|g" "$TMP_CONFIG"

# Run campaign
echo "Starting campaign..."
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
echo "  1. Review results: jq . $OUTPUT_FILE | less"
echo "  2. Run comparison: bash src/scripts/compare_models_adversarial.sh"
echo "  3. Run LLM analysis: bash src/scripts/run_llm_analyzer.sh"
echo ""
