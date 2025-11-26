#!/bin/bash
# Run adversarial affiliation testing across all 3 models

set -e  # Exit on error

MODELS=(
    "models/DeepHat-V1-7B.f16.gguf"
    "models/qwen2.5-coder-7b-instruct-fp16.gguf"
    "models/WhiteRabbitNeo_WhiteRabbitNeo-V3-7B-bf16.gguf"
    "models/microsoft_Fara-7B-bf16.gguf"
)

MODEL_NAMES=(
    "deephat-v1-7b"
    "qwen2.5-coder-7b"
    "whiterabbitneo-v3-7b"
    "microsoft_fara-7b"
)

CONFIG_TEMPLATE="config/adversarial_affiliation_dataset.yaml"

echo "========================================="
echo "Adversarial Affiliation Testing"
echo "Testing ${#MODELS[@]} models"
echo "========================================="
echo ""

for i in "${!MODELS[@]}"; do
    MODEL_PATH="${MODELS[$i]}"
    MODEL_NAME="${MODEL_NAMES[$i]}"
    OUTPUT_FILE="artifacts/adversarial-affiliation-${MODEL_NAME}.ndjson"
    
    echo "[$((i+1))/${#MODELS[@]}] Testing: $MODEL_PATH"
    echo "Output: $OUTPUT_FILE"
    
    # Check if model file exists
    if [ ! -f "$MODEL_PATH" ]; then
        echo "⚠️  WARNING: Model file not found: $MODEL_PATH"
        echo "Skipping..."
        echo ""
        continue
    fi
    
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
    
    echo "✅ Completed: $MODEL_NAME"
    echo "Results: $OUTPUT_FILE"
    echo ""
done

echo "========================================="
echo "All models tested!"
echo "========================================="
echo ""
echo "Generated artifacts:"
for MODEL_NAME in "${MODEL_NAMES[@]}"; do
    OUTPUT_FILE="artifacts/adversarial-affiliation-${MODEL_NAME}.ndjson"
    if [ -f "$OUTPUT_FILE" ]; then
        SIZE=$(du -h "$OUTPUT_FILE" | cut -f1)
        RECORDS=$(wc -l < "$OUTPUT_FILE")
        echo "  - $OUTPUT_FILE ($SIZE, $RECORDS records)"
    fi
done

echo ""
echo "Run comparison analysis:"
echo "  bash src/scripts/compare_models_adversarial.sh"
