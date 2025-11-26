#!/bin/bash
# Run LLM-powered analysis of adversarial affiliation test results
# Uses LangGraph with reflection loops and local Ollama model for security analysis

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "========================================="
echo "LLM-Powered Model Analysis"
echo "========================================="
echo ""
echo "Project root: $PROJECT_ROOT"
echo "Analyzer script: $SCRIPT_DIR/llm_analyzer.py"
echo ""

# Default configuration
ARTIFACTS_DIR="${ARTIFACTS_DIR:-$PROJECT_ROOT/artifacts}"
OUTPUT_FILE="${OUTPUT_FILE:-$PROJECT_ROOT/llm_analysis_report.txt}"
MAX_ITERATIONS="${MAX_ITERATIONS:-2}"
OLLAMA_MODEL="${OLLAMA_MODEL:-gpt-oss:120b}"

MODEL_NAMES=(
    "deephat-v1-7b"
    "qwen2.5-coder-7b"
    "whiterabbitneo-v3-7b"
    "microsoft_fara-7b"
)

echo "Configuration:"
echo "  Artifacts dir: $ARTIFACTS_DIR"
echo "  Output file: $OUTPUT_FILE"
echo "  Max iterations: $MAX_ITERATIONS"
echo "  Ollama model: $OLLAMA_MODEL"
echo "  Models: ${MODEL_NAMES[*]}"
echo ""

# Check if Ollama is running
echo "Checking Ollama availability..."
if ! ollama list &>/dev/null; then
    echo "⚠️  ERROR: Ollama is not running or not installed"
    echo "Please start Ollama and ensure the model '$OLLAMA_MODEL' is available"
    echo ""
    echo "To start Ollama: ollama serve"
    echo "To check models: ollama list"
    exit 1
fi

# Check if the specified model exists
if ! ollama list | grep -q "$OLLAMA_MODEL"; then
    echo "⚠️  WARNING: Model '$OLLAMA_MODEL' not found in Ollama"
    echo "Available models:"
    ollama list
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "✅ Ollama is available"
echo ""

# Check for required files
MISSING_FILES=0
for MODEL_NAME in "${MODEL_NAMES[@]}"; do
    FILE="$ARTIFACTS_DIR/adversarial-affiliation-${MODEL_NAME}.ndjson"
    if [ ! -f "$FILE" ]; then
        echo "⚠️  Missing: $FILE"
        MISSING_FILES=$((MISSING_FILES + 1))
    fi
done

if [ $MISSING_FILES -gt 0 ]; then
    echo ""
    echo "⚠️  $MISSING_FILES model result file(s) missing"
    echo "Run this first: bash src/scripts/run_all_models_adversarial.sh"
    exit 1
fi

echo "✅ All model result files found"
echo ""

# Check Python dependencies
echo "Checking Python dependencies..."
if ! python3 -c "import langchain, langgraph, langchain_community" 2>/dev/null; then
    echo "⚠️  Missing required Python packages"
    echo "Installing dependencies..."
    pip install -r "$PROJECT_ROOT/requirements_llm_analyzer.txt"
fi

echo "✅ Dependencies satisfied"
echo ""

# Add src/scripts to PYTHONPATH so imports work
export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"

# Run the analyzer
echo "========================================="
echo "Starting LLM Analysis Pipeline"
echo "========================================="
echo ""
echo "This will use multi-agent reflection loops to:"
echo "  1. Analyze model comparison data for threats"
echo "  2. Review findings with QA agent"
echo "  3. Iterate until confidence threshold or max iterations"
echo "  4. Generate comprehensive security report"
echo ""
echo "⏳ Analysis may take several minutes depending on:"
echo "  - Number of models"
echo "  - Complexity of findings"
echo "  - Ollama model performance"
echo ""

cd "$PROJECT_ROOT"

python3 "$SCRIPT_DIR/llm_analyzer.py" \
    --artifacts-dir "$ARTIFACTS_DIR" \
    --model-names "${MODEL_NAMES[@]}" \
    --output "$OUTPUT_FILE" \
    --max-iterations "$MAX_ITERATIONS" \
    --ollama-model "$OLLAMA_MODEL"

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "========================================="
    echo "✅ Analysis Complete!"
    echo "========================================="
    echo ""
    echo "Reports generated:"
    echo "  Text report: $OUTPUT_FILE"
    echo "  JSON findings: ${OUTPUT_FILE%.txt}.json"
    echo ""
    echo "View report:"
    echo "  cat $OUTPUT_FILE"
    echo ""
else
    echo ""
    echo "========================================="
    echo "❌ Analysis Failed"
    echo "========================================="
    echo "Exit code: $EXIT_CODE"
    echo ""
fi

exit $EXIT_CODE
